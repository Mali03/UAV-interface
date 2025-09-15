from pymavlink import mavutil
import os
import time
import math

class attitude:
    def __init__(self,roll,pitch,yaw,yawspeed=0):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.yawspeed = yawspeed

class location:
    def __init__(self,lat,lon,alt):
        self.lat = lat
        self.lon = lon
        self.alt = alt

class velocity:
    def __init__(self, vx, vy, vz, airspeed):
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.airspeed = airspeed
          

class Drone:
    def __init__(self,ip="udpin:127.0.0.1:14550",baud=115200):
      self.vehicle = None

      os.environ["MAVLINK20"] = "1"  # MAVLink 2.0'ı zorunlu kıl
      self.vehicle = mavutil.mavlink_connection(str(ip),baud=baud)
      self.vehicle.wait_heartbeat()
      print("Bağlandı.")
      
      time.sleep(1)

    def arm_disarm(self,arm):
        if arm:
            arm=1
        elif arm==0:
            arm=0
        self.vehicle.mav.command_long_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            arm, 0, 0, 0, 0, 0, 0)
        if arm == 0:
            print("Disarm olana kadar bekleniyor...")
            self.vehicle.motors_disarmed_wait()
            print('Disarmed')
            time.sleep(1)
        if arm == 1:
            print("Arm olana kadar bekleniyor...")
            self.vehicle.motors_armed_wait()
            print('Armed')
            time.sleep(1)

    @property
    def mode(self):
        while True:
            msg = self.vehicle.recv_match(type = 'HEARTBEAT', blocking = True)
            if msg:
                msg = msg.to_dict()
                # Mode mapping sözlüğünü al
                mode_mapping = self.vehicle.mode_mapping()

                # Sözlüğü ters çevirerek mode_id -> mode_string eşlemesi oluştur
                reverse_mode_mapping = {v: k for k, v in mode_mapping.items()}

                # Belirli bir mode_id'nin karşılık gelen string modunu almak için:
                mode_id = msg.get("custom_mode")  # Örnek ID
                mode_string = reverse_mode_mapping.get(mode_id, "Unknown Mode")
                return mode_string
    
    @mode.setter
    def mode(self, new_mode):
        mode_mapping = self.vehicle.mode_mapping()

        if new_mode not in mode_mapping:
            print(f'Bilinmeyen mod: {new_mode}')
            print('Geçerli modlar:', list(mode_mapping.keys()))
            return

        mode_id = mode_mapping[new_mode]

        self.vehicle.mav.set_mode_send(
            self.vehicle.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id
        )
    
        # Mod değişikliğini bekle
        while self.mode != new_mode:
            print(f"{new_mode} moduna geçiş bekleniyor...")
            time.sleep(0.1)

        print(new_mode)
    
    def takeoff(self, altitude):
        self.vehicle.mav.command_long_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0,
            0,
            0,
            0,
            0,
            0,
            0, 
            altitude
        )
        time.sleep(1)

        while True:
            alt = self.location.alt
            if alt > altitude * 0.95:
                print("Hedeflenen yüksekliğe ulaşıldı")
                break
            else:
                print("Yükselik", alt)

    @property
    def attitude(self):
        while True:
            msg = self.vehicle.recv_match(type="ATTITUDE",blocking=True)
            if msg:
                msg = msg.to_dict()
                roll = msg.get("roll")
                pitch = msg.get("pitch")
                yaw = msg.get("yaw")
                yawspeed = msg.get("yawspeed")
                roll = int(((roll) * 180) / (math.pi))
                pitch = int(((pitch) * 180) / (math.pi))
                return attitude(roll,pitch,yaw,yawspeed)

    @property
    def location(self):
        while True:
            msg = self.vehicle.recv_match(type="GLOBAL_POSITION_INT",blocking=True)
            if msg:
                msg = msg.to_dict()
                lat = msg.get("lat") / 1.0e7
                lon = msg.get("lon") / 1.0e7
                alt = msg.get("relative_alt")/ 1000
                return location(lat,lon,alt)

    @property        
    def velocity(self):
        while True:
            msg = self.vehicle.recv_match(type="LOCAL_POSITION_NED", blocking=True)
            if msg:
                msg = msg.to_dict()
                vx = msg['vx']
                vy = msg['vy']
                vz = msg['vz']
                airspeed = (vx**2 + vy**2 + vz**2)**0.5
                return velocity(vx, vy, vz, airspeed)

    def get_waypoints(self):

        self.vehicle.mav.mission_request_list_send(
            self.vehicle.target_system,
            self.vehicle.target_component
        )

        msg = None
        while msg is None:
            msg = self.vehicle.recv_match(type='MISSION_COUNT', blocking=True)
        
        waypoint_count = msg.count
        waypoints = []


        for i in range(waypoint_count):
            self.vehicle.mav.mission_request_send(
                self.vehicle.target_system,
                self.vehicle.target_component,
                i
            )

            msg = None
            while msg is None:
                msg = self.vehicle.recv_match(type='MISSION_ITEM', blocking=True)

            if msg is None:
                print(f"Waypoint {i} alınamadı!")
                continue
       
            waypoints.append({
                'seq': msg.seq,
                'frame': msg.frame,
                'command': msg.command,
                'param1': msg.param1,
                'param2': msg.param2,
                'param3': msg.param3,
                'param4': msg.param4,
                'x': msg.x,
                'y': msg.y,
                'z': msg.z,
                'autocontinue': msg.autocontinue
            })
            time.sleep(0.02)

        return waypoints

    def verify_waypoints(self):
        self.vehicle.mav.mission_request_list_send(
            self.vehicle.target_system,
            self.vehicle.target_component
        )
        
        msg = self.vehicle.recv_match(type='MISSION_COUNT', blocking=True, timeout=5)
        if msg:
            return msg.count
        return 0

    def upload_waypoints(self, waypoints):
        try:
            print("Waypoint yükleme başlıyor...")
            
            current_wp_count = self.verify_waypoints()
            print(f"Mevcut waypoint sayısı: {current_wp_count}")
            
            if current_wp_count > 0:
                print("Mevcut waypointler temizleniyor...")
                self.vehicle.mav.mission_clear_all_send(
                    self.vehicle.target_system,
                    self.vehicle.target_component
                )
                time.sleep(2)
                
                if self.verify_waypoints() > 0:
                    print("Waypoint'ler temizlenemedi, tekrar deneniyor...")
                    time.sleep(1)
                    self.vehicle.mav.mission_clear_all_send(
                        self.vehicle.target_system,
                        self.vehicle.target_component
                    )
                    time.sleep(2)
            
            total_waypoints = len(waypoints)
            print(f"Yüklenecek waypoint sayısı: {total_waypoints}")
            
            current_location = self.location
            
            total_mission_items = total_waypoints + 1
            
            request_received = False
            for _ in range(3):
                self.vehicle.mav.mission_count_send(
                    self.vehicle.target_system,
                    self.vehicle.target_component,
                    total_mission_items
                )
                
                start_time = time.time()
                while time.time() - start_time < 3:
                    msg = self.vehicle.recv_match(type='MISSION_REQUEST', blocking=True, timeout=1)
                    if msg is not None and msg.seq == 0:
                        request_received = True
                        break
                
                if request_received:
                    break
                    
                time.sleep(1)
            
            if not request_received:
                return False, "İlk waypoint request alınamadı"
            
            self.vehicle.mav.mission_item_send(
                self.vehicle.target_system,
                self.vehicle.target_component,
                0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                0,
                1,
                0, 0, 0, 0,
                current_location.lat,
                current_location.lon,
                0
            )
            
            for i, (lat, lon, alt) in enumerate(waypoints, start=1):
                msg = self.vehicle.recv_match(type='MISSION_REQUEST', blocking=True, timeout=3)
                if msg is None or msg.seq != i:
                    return False, f"Waypoint {i} için request alınamadı"
                
                print(f"Waypoint {i} gönderiliyor: lat={lat}, lon={lon}, alt={alt}")
                
                self.vehicle.mav.mission_item_send(
                    self.vehicle.target_system,
                    self.vehicle.target_component,
                    i,
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                    0,
                    1,
                    0, 0, 0, 0,
                    lat, lon, alt
                )
                
                print("Mission başarıyla yüklendi")
            
            time.sleep(2)
            final_wp_count = self.verify_waypoints()
            expected_total = total_waypoints + 1
            
            if final_wp_count == expected_total:
                return True, f"{total_waypoints} waypoint başarıyla yüklendi."
            else:
                error_msg = f"Waypoint sayısı eşleşmiyor. Beklenen: {expected_total}, Mevcut: {final_wp_count}"
                print(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Waypoint yükleme hatası: {str(e)}"
            print(error_msg)
            return False, error_msg
        
    def isArmed(self):
        self.__arm_drone = self.vehicle.motors_armed()
        return True if self.__arm_drone else False
