from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from windows.MainWindow import Ui_MainWindow
from windows.ConnectingWindow import Ui_ConnectingWindow
from windows.WaypointWindow import Ui_WaypointWindow
from windows.WaypointsSettingWindow import Ui_WaypointsSettingWindow
import sys
import io
import folium
from mav_library import Drone
import time
import os
import base64
import cv2
import socket
import pickle
import numpy as np
from windows.FlightDataWidget import FlightIndicatorsWidget
from datetime import datetime

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "/home/usr/lib/x86_64-linux-gnu/qt5/plugins"
os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"

mapBaslangicKoordinati = (40.18765752437741, 29.128429079470234)

class FlightDataThread(QThread):
    updateSignal = pyqtSignal(dict)

    def __init__(self, drone):
        super().__init__()
        self.drone = drone
        self.running = True

    def run(self):
        while self.running:
            try:
                # Drone verileri
                flight_data = {
                    "airspeed": self.drone.velocity.airspeed or 0,
                    "altitude": self.drone.location.alt or 0,
                    "roll": self.drone.attitude.roll or 0,
                    "pitch": self.drone.attitude.pitch or 0,
                    "heading": self.drone.attitude.yaw or 0,
                    "turn_rate": (self.drone.attitude.yawspeed or 0) * 57.2958,  # radyan/s'den derece/s'ye
                    "vertical_speed": self.drone.velocity.vz or 0
                }
                self.updateSignal.emit(flight_data)
                
                time.sleep(0.2) # 200ms
                
            except Exception as e:
                print(f"Flight data thread hatası: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()

class MapUpdateThread(QThread):
    def __init__(self, drone):
        super().__init__()
        self.drone = drone
        self.running = True
        self.last_update = 0
        self.update_interval = 0.1 # 100ms'de bir güncelle (10 FPS)

    def run(self):
        while self.running:
            try:
                current_time = time.time()
                if current_time - self.last_update >= self.update_interval:
                    lat = self.drone.location.lat
                    lon = self.drone.location.lon
                    
                    if (isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and 
                        -90 <= lat <= 90 and -180 <= lon <= 180):
                        script = f'updateMarkerPosition({lat}, {lon}); addTrailPoint({lat}, {lon});'
                        QtCore.QMetaObject.invokeMethod(self.parent(), 
                                                      "updateMapJS",
                                                      Qt.QueuedConnection,
                                                      QtCore.Q_ARG(str, script))
                        
                    self.last_update = current_time
                
                time.sleep(0.05) # 50ms bekle
                
            except Exception as e:
                print(f"Map update thread hatası: {e}")
                time.sleep(0.1)

    def stop(self):
        self.running = False
        self.wait()

class CameraThread(QThread):
    changePixmap = pyqtSignal(QImage)
    connectionStatus = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)

    def __init__(self, host="localhost", port=5000):
        super().__init__()
        self.host = host
        self.port = port
        self.maxLength = 1472
        self.sock = None
        self.running = True
        self.frameInfo = None
        self.buffer = None

    # UDP ile görüntü aktarımı için
    """
    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.host, self.port))
            self.sock.settimeout(1.0)
            
            self.connectionStatus.emit("Bağlantı kuruldu.")
            self.connectionStatus.emit("Görüntü bekleniyor...")
            
            while self.running:
                try:
                    data, address = self.sock.recvfrom(self.maxLength)
                    
                    if len(data) < 100:
                        try:
                            self.frameInfo = pickle.loads(data)
                        except Exception as e:
                            self.errorOccurred.emit(f"Pickle hatası: {e}")
                            continue
                            
                        if self.frameInfo:
                            numsOfPacks = self.frameInfo["packs"]

                            for i in range(numsOfPacks):
                                if not self.running:
                                    break
                                    
                                try:
                                    data, address = self.sock.recvfrom(self.maxLength)
                                    
                                    if i == 0:
                                        self.buffer = data
                                    else:
                                        self.buffer += data
                                except socket.timeout:
                                    continue
                                except Exception as e:
                                    self.errorOccurred.emit(f"Paket alma hatası: {e}")
                                    break

                            if self.running and self.buffer:
                                frame = np.frombuffer(self.buffer, dtype=np.uint8)
                                frame = frame.reshape(frame.shape[0], 1)
                                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                                
                                if frame is not None and isinstance(frame, np.ndarray):
                                    frame = cv2.flip(frame, 1)
                                    
                                    rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                    h, w, ch = rgbImage.shape
                                    bytesPerLine = ch * w
                                    
                                    convertToQtFormat = QImage(
                                        rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888
                                    )
                                    
                                    p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                                    
                                    self.changePixmap.emit(p)
                                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.errorOccurred.emit(f"Veri alma hatası: {e}")
                    break
                    
        except Exception as e:
            self.errorOccurred.emit(f"Bağlantı kurulamadı: {e}")
        finally:
            self.cleanup()
    """

    # Bilgisayarın kamerası (Test için)
    def run(self):
        self.cap = cv2.VideoCapture(0)

        while self.running:
            ret, frame = self.cap.read()
            frame = cv2.flip(frame,1)

            if ret:
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)

                self.changePixmap.emit(p)

    def stop(self):
        self.running = False
        self.cleanup()
        self.quit()
        self.wait()

    def cleanup(self):
        if self.sock:
            try:
                self.sock.close()
                self.connectionStatus.emit("Bağlantı sonlandırıldı.")
            except:
                pass
            self.sock = None

    def setConnection(self, host, port):
        self.host = host
        self.port = port

class ParamLoadThread(QThread):
    progress_update = pyqtSignal(str)
    progress_bar_update = pyqtSignal(int)
    finished = pyqtSignal(bool, str, object)
    
    def __init__(self, port, baud_rate):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.drone = None

    def run(self):
        try:
            self.progress_update.emit("Yükleniyor...")
            self.progress_bar_update.emit(0) # Başlangıç değeri

            self.drone = Drone(self.port, baud=self.baud_rate)

            self.progress_update.emit("Bağlantı kuruluyor...")
            self.progress_bar_update.emit(10)

            self.drone.vehicle.mav.param_request_list_send(self.drone.vehicle.target_system, self.drone.vehicle.target_component)

            params_received = set()
            timeout = 30
            start_time = time.time()
            total_params = None

            while True:
                msg = self.drone.vehicle.recv_match(type='PARAM_VALUE', blocking=True, timeout=timeout)
                if msg is None:
                    print("Parametreleri tam alırken zaman aşımı!")
                    break

                params_received.add(msg.param_id)
                
                # İlk mesajda toplam parametre sayısını al
                if total_params is None:
                    total_params = msg.param_count
                
                # Progress bar güncelleme
                if total_params:
                    progress = int((len(params_received) / total_params) * 90) + 10  # 10-100 arası
                    self.progress_bar_update.emit(progress)
                    self.progress_update.emit(f"Parametreler yükleniyor... ({len(params_received)}/{total_params})")

                if len(params_received) >= total_params:
                    self.progress_bar_update.emit(100)
                    self.progress_update.emit("Parametreler yüklendi!")
                    self.finished.emit(True, "Bağlantı başarılı!", self.drone)
                    break

                # Timeout kontrolü
                if time.time() - start_time > timeout:
                    print("Parametreleri alırken zaman aşımı oldu!")
                    self.finished.emit(False, "Bağlantı zaman aşımına uğradı!", None)
                    break

        except Exception as e:
            print(e)
            self.finished.emit(False, f"Bağlantı hatası: {str(e)}", None)

class MissionThread(QThread):
    missionCompleted = pyqtSignal()

    def __init__(self, drone):
        super().__init__()
        self.drone = drone

    def run(self):
        print("Görev başladı.")
        self.drone.mode = "AUTO"
        self.missionCompleted.emit()

class ModeChangeThread(QThread):
    modeChanged = pyqtSignal()

    def __init__(self, drone, label, combo):
        super().__init__()
        self.drone = drone
        self.label = label
        self.combo = combo

    def run(self):
        currentMode = self.combo.currentText()
        self.drone.mode = currentMode
        self.modeChanged.emit()

class ArmDisarmThread(QThread):
    armed = pyqtSignal()
    disarmed = pyqtSignal()

    def __init__(self, drone, label, status):
        super().__init__()
        self.drone = drone
        self.label = label
        self.status = status

    def run(self):
        if self.status == True: # Arm et
            self.drone.arm_disarm(True)
            
            self.armed.emit()
        else: # Disarm et
            self.drone.arm_disarm(False)

            self.disarmed.emit()

class ChangeAltLabel(QThread):

    def __init__(self, drone, label):
        super().__init__()
        self.drone = drone
        self.label = label
        self.running = True

    def run(self):
        while self.running:
            self.label.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Şuanki yükseklik</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#fffe08;">{self.drone.location.alt}</span></p></body></html>')

            time.sleep(0.5)
    
    def stop(self):
        self.running = False
        self.wait()

class TakeOffThread(QThread):
    reached = pyqtSignal()

    def __init__(self, drone, label, alt):
        super().__init__()
        self.drone = drone
        self.label = label
        self.alt = alt

    def run(self):
        self.altLabelThread = ChangeAltLabel(self.drone, self.label)
        self.altLabelThread.start()

        self.drone.takeoff(self.alt)

        self.altLabelThread.stop()

        self.reached.emit()

class WaypointLoadThread(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)

    def __init__(self, drone, coordinates):
        super().__init__()
        self.drone = drone
        self.coordinates = coordinates

    def run(self):
        try:
            self.progress.emit(0, "Waypoint'ler yükleniyor...")
            success, message = self.drone.upload_waypoints(self.coordinates)
            
            if success:
                self.progress.emit(100, message)
                self.finished.emit(True, message)
            else:
                self.progress.emit(0, message)
                self.finished.emit(False, message)
                
        except Exception as e:
            self.progress.emit(0, str(e))
            self.finished.emit(False, f"Waypoint'ler yüklenirken hata oluştu: {str(e)}")



class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        print("Arayüz başlatıldı")
        self.showMaximized()
        self.ui.centralwidget.setStyleSheet("background-color: rgb(0, 0, 0)")
        
        self.icon_base64 = self.getIconBase64()
        
        self.createInitialMap()

        self.ui.BaglanButton.clicked.connect(self.connect)

        self.droneConnected = False
        self.missionCompleted = True
        
        self.ui.gorevButton.clicked.connect(self.gorev)

        self.ui.rtlButton.clicked.connect(self.rtl)

        self.marker = None

        self.pixMap = QPixmap("images/quad.png")
        self.ui.logoLabel.setPixmap(self.pixMap)

        # Flight indicators widget'ı dataLabel yerine ekle
        self.flight_indicators = FlightIndicatorsWidget()
        self.ui.dataLabel.setParent(None) # Eski label'ı kaldır
        
        # Widget'ı doğrudan centralwidget'a ekle
        self.flight_indicators.setParent(self.ui.centralwidget)
        self.flight_indicators.setGeometry(self.ui.dataLabel.geometry()) # Eski label'ın konumunu kullan
        self.flight_indicators.show()

        self.ui.modButton.clicked.connect(self.modeChange)

        self.ui.waypointButton.clicked.connect(self.openWpWindow)

        self.ui.armButton.clicked.connect(self.arm)
        self.ui.disarmButton.clicked.connect(self.disarm)

        self.ui.takeOffButton.clicked.connect(self.takeoff)

        # logTable ayarları
        self.ui.logTable.setColumnCount(2)
        self.ui.logTable.setHorizontalHeaderLabels(["Tarih", "Mesaj"])
        self.ui.logTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        
        # Sütun genişliklerini ayarla
        self.setupLogTableColumns()

    def setupLogTableColumns(self):
        total_width = self.ui.logTable.viewport().width()
        self.ui.logTable.setColumnWidth(0, int(total_width * 0.25)) # Tarih: %25
        self.ui.logTable.setColumnWidth(1, int(total_width * 0.75)) # Mesaj: %75

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self.ui, 'logTable'):
            self.setupLogTableColumns()

    def tabloItemEkle(self, message):
        row = self.ui.logTable.rowCount()
        self.ui.logTable.insertRow(row)
        
        time_str = datetime.now().strftime("%H:%M:%S")
        time_item = QtWidgets.QTableWidgetItem(time_str)
        time_item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.ui.logTable.setItem(row, 0, time_item)
        
        message_item = QtWidgets.QTableWidgetItem(str(message))
        message_item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.ui.logTable.setItem(row, 1, message_item)

        self.ui.logTable.scrollToBottom()

    @QtCore.pyqtSlot(str)
    def updateMapJS(self, script):
        """JavaScript kodunu ana thread'de çalıştır"""
        try:
            self.webView.page().runJavaScript(script)
        except Exception as e:
            print(f"Map JS güncelleme hatası: {e}")

    def arm(self):
        if self.droneConnected is False:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Lütfen önce drone'a bağlanın.")
            msg.setWindowTitle("Uyarı")
            msg.exec_()
        else:
            if self.drone.mode != "GUIDED":
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Motorları çalıştırmak için önce \"GUIDED\" moduna geçin.")
                msg.setWindowTitle("Uyarı")
                msg.exec_()
            else:
                self.tabloItemEkle("Motorlar'a arm emri verildi..")
                self.ui.armLabel.setText("<html><head/><body><p><span style=\" font-weight:600; color:#fffe08;\">Arm ediliyor...</span></p></body></html>")
                self.armThread = ArmDisarmThread(self.drone, self.ui.armLabel, True)
                self.armThread.armed.connect(self.armed)
                self.armThread.start()

    def armed(self):
        self.ui.armLabel.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Arm</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#42FF2F;">Armed</span></p></body></html>')
        self.tabloItemEkle("Motorlar arm edildi.")

    def disarm(self):
        if self.droneConnected is False:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Lütfen önce drone'a bağlanın.")
            msg.setWindowTitle("Uyarı")
            msg.exec_()
        else:
            self.tabloItemEkle("Motorlar'a disarm emri verildi..")
            self.ui.armLabel.setText("<html><head/><body><p><span style=\" font-weight:600; color:#fffe08;\">Disarm ediliyor...</span></p></body></html>")
            self.armThread = ArmDisarmThread(self.drone, self.ui.armLabel, False)
            self.armThread.disarmed.connect(self.disarmed)
            self.armThread.start()

    def disarmed(self):
        self.ui.armLabel.setText("<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Arm</span><span style=\" font-weight:600;\">: </span><span style=\" font-weight:600; color:#ff0000;\">Disarmed</span></p></body></html>")
        self.tabloItemEkle("Motorlar disarm edildi.")

    def takeoff(self):
        if self.droneConnected is False:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Lütfen önce drone'a bağlanın.")
            msg.setWindowTitle("Uyarı")
            msg.exec_()
        else:
            hedeflenenYukseklik = self.ui.takeOffYukseklik.value()

            self.takeoffLabel = TakeOffThread(self.drone, self.ui.yukseklikLabel, hedeflenenYukseklik)
            self.takeoffLabel.reached.connect(self.altReached)
            self.takeoffLabel.start()
            self.tabloItemEkle(f"{hedeflenenYukseklik}m yüksekliğe take off emri verildi.")

    def altReached(self):
        self.ui.yukseklikLabel.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Ulaşılan yükseklik</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#42FF2F;">{self.drone.location.alt}</span></p></body></html>')
        self.tabloItemEkle("Hedeflenen yüksekliğe çıkıldı. Görev başlatılabilir.")

    def openWpWindow(self):
        if self.droneConnected is False:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Lütfen önce drone'a bağlanın.")
            msg.setWindowTitle("Uyarı")
            msg.exec_()
        else:
            self.waypointWindow = QtWidgets.QMainWindow()
            self.uiWpWindow = Ui_WaypointWindow()
            self.uiWpWindow.setupUi(self.waypointWindow)
            self.uiWpWindow.centralwidget.setStyleSheet("background-color: rgb(0, 0, 0)")
            self.waypointWindow.show()

            self.uiWpWindow.yukleButton.clicked.connect(self.wpYukle)
            self.uiWpWindow.okuButton.clicked.connect(self.wpOku)

            header = self.uiWpWindow.coordinateWidget.horizontalHeader()
            header.setDefaultAlignment(Qt.AlignCenter)
            header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            
            vertical_header = self.uiWpWindow.coordinateWidget.verticalHeader()
            vertical_header.setDefaultAlignment(Qt.AlignCenter)
            
            for row in range(self.uiWpWindow.coordinateWidget.rowCount()):
                for col in range(self.uiWpWindow.coordinateWidget.columnCount()):
                    item = self.uiWpWindow.coordinateWidget.item(row, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item = QtWidgets.QTableWidgetItem("")
                        item.setTextAlignment(Qt.AlignCenter)
                        self.uiWpWindow.coordinateWidget.setItem(row, col, item)
            
            self.wpm = folium.Map(
                location=(self.drone.location.lat, self.drone.location.lon),
                zoom_start=20,
                tiles=folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr="QuadRuplet", max_zoom=22)
            )
        
            script = f"""
                <script src=\"qrc:///qtwebchannel/qwebchannel.js\"></script>
                <script>
                    var droneMarker = null;
                    var droneMap = null;
                    var droneIcon = {f'L.icon({{ iconUrl: "{self.icon_base64}", iconSize: [50, 50], iconAnchor: [25, 25] }})' if self.icon_base64 else 'null'};
                    var droneTrail = [];
                    var trailLayer = null;
                    var trackingEnabled = true;

                    var clickIndex = 1;
                    var pybridge = null;

                    new QWebChannel(qt.webChannelTransport, function(channel) {{
                        pybridge = channel.objects.pybridge;
                    }});

                    document.addEventListener('DOMContentLoaded', function() {{
                        var mapDiv = document.querySelector('.folium-map');
                        droneMap = window[mapDiv.id.replace('map_', 'map_')];

                        if (droneMap && !droneMarker && droneIcon) {{
                            droneMarker = L.marker([{self.drone.location.lat}, {self.drone.location.lon}], {{icon: droneIcon}}).addTo(droneMap);
                        }}

                        droneMap.on('click', function(e) {{
                            var lat = e.latlng.lat;
                            var lng = e.latlng.lng;

                            L.marker([lat, lng]).addTo(droneMap)
                              .bindTooltip(String(clickIndex), {{
                                    permanent: true,
                                    direction: 'center',
                                    offset: [-15, -30],
                                    className: 'waypoint-label',
                                    opacity: 1,
                                    interactive: false
                                }}).openPopup();

                            if (pybridge) {{
                                pybridge.sendCoordinates(lat, lng, clickIndex);
                            }}

                            clickIndex += 1;
                        }});
                    }});
                
                    window.initializeMarker = function(lat, lng) {{
                        if (droneMap && !droneMarker) {{
                            droneMarker = L.marker([lat, lng], droneIcon ? {{icon: droneIcon}} : {{}}).addTo(droneMap);
                            droneMap.setView([lat, lng], droneMap.getZoom());
                        }}
                    }};
                
                    window.updateMarkerPosition = function(lat, lng) {{
                        if (droneMarker && droneMap) {{
                            droneMarker.setLatLng([lat, lng]);
                            if (trackingEnabled) {{
                                droneMap.setView([lat, lng], droneMap.getZoom());
                            }}
                        }}
                    }};

                    window.removeDroneMarker = function() {{
                        if (droneMarker) {{
                            droneMap.removeLayer(droneMarker);
                            droneMarker = null;
                        }}
                    }};

                    window.addTrailPoint = function(lat, lng) {{
                        var newPoint = [lat,lng];
                        droneTrail.push(newPoint);

                        if (trailLayer) {{
                            droneMap.removeLayer(trailLayer);
                        }}

                        if (droneTrail.length > 1) {{
                            trailLayer = L.polyline(droneTrail, {{color: 'yellow'}}).addTo(droneMap);
                        }}

                        setTimeout(function() {{
                            if (droneTrail.length > 1) {{
                                droneTrail.shift();

                                if (trailLayer) {{
                                    droneMap.removeLayer(trailLayer);
                                }}

                                if (droneTrail.length > 1) {{
                                    trailLayer = L.polyline(droneTrail, {{color: 'yellow'}}).addTo(droneMap);
                                }}
                            }}
                        }}, 10000)
                    }}
                
                    // Toggle tracking state
                    window.toggleTracking = function() {{
                        trackingEnabled = !trackingEnabled;
                        return trackingEnabled;
                    }}
                </script>
            """
        
            self.wpm.get_root().html.add_child(folium.Element(script))

            data = io.BytesIO()
            self.wpm.save(data, close_file=False)
            self.wpWebView = QWebEngineView()

            class WebBridge(QtCore.QObject):
                def __init__(self, table_widget):
                    super().__init__()
                    self.table_widget = table_widget

                @QtCore.pyqtSlot(float, float, int)
                def sendCoordinates(self, lat, lng, idx):
                    if self.table_widget.rowCount() < idx:
                        self.table_widget.setRowCount(idx)
                    
                    lat_item = QtWidgets.QTableWidgetItem(f"{lat:.8f}")
                    lng_item = QtWidgets.QTableWidgetItem(f"{lng:.8f}")
                    alt_item = QtWidgets.QTableWidgetItem(str(10))
                    
                    lat_item.setTextAlignment(Qt.AlignCenter)
                    lng_item.setTextAlignment(Qt.AlignCenter)
                    alt_item.setTextAlignment(Qt.AlignCenter)
                    
                    self.table_widget.setItem(idx-1, 0, lat_item)
                    self.table_widget.setItem(idx-1, 1, lng_item)
                    self.table_widget.setItem(idx-1, 2, alt_item)

            self._wp_bridge = WebBridge(self.uiWpWindow.coordinateWidget)
            channel = QWebChannel(self.wpWebView.page())
            channel.registerObject('pybridge', self._wp_bridge)
            self.wpWebView.page().setWebChannel(channel)

            self.wpWebView.setHtml(data.getvalue().decode())
            self.uiWpWindow.mapCLayout.addWidget(self.wpWebView)

    def wpOku(self):
        if not self.droneConnected:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("Önce drone'a bağlanmalısınız!")
            msg.setWindowTitle("Uyarı")
            msg.exec_()
            return
            
        waypoints = self.drone.get_waypoints()
        
        if not waypoints or len(waypoints) <= 1:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("Drone'da kayıtlı waypoint bulunmuyor.")
            msg.setWindowTitle("Bilgi")
            msg.exec_()
            return
            
        self.uiWpWindow.coordinateWidget.setRowCount(len(waypoints) - 1)
        
        # Markerları temizle
        markers_script = """
            if (window.waypointMarkers) {
                window.waypointMarkers.forEach(function(marker) {
                    droneMap.removeLayer(marker);
                });
            }
            window.waypointMarkers = [];
            
            if (window.waypointPath) {
                droneMap.removeLayer(window.waypointPath);
            }
        """
        
        path_coords = []
        for i, wp in enumerate(waypoints[1:], start=1):
            lat_item = QtWidgets.QTableWidgetItem(f"{wp['x']:.8f}")
            lon_item = QtWidgets.QTableWidgetItem(f"{wp['y']:.8f}")
            alt_item = QtWidgets.QTableWidgetItem(f"{wp['z']:.1f}")
            
            lat_item.setTextAlignment(Qt.AlignCenter)
            lon_item.setTextAlignment(Qt.AlignCenter)
            alt_item.setTextAlignment(Qt.AlignCenter)
            
            self.uiWpWindow.coordinateWidget.setItem(i-1, 0, lat_item)
            self.uiWpWindow.coordinateWidget.setItem(i-1, 1, lon_item)
            self.uiWpWindow.coordinateWidget.setItem(i-1, 2, alt_item)
            
            markers_script += f"""
                var marker = L.marker([{wp['x']}, {wp['y']}]).addTo(droneMap)
                    .bindTooltip('{i}', {{
                        permanent: true,
                        direction: 'center',
                        offset: [-15, -30],
                        className: 'waypoint-label',
                        opacity: 1,
                        interactive: false
                    }});
                window.waypointMarkers.push(marker);
            """
            
            path_coords.append([wp['x'], wp['y']])
        
        if len(path_coords) > 1:
            path_coords_str = str(path_coords).replace('(', '[').replace(')', ']')
            markers_script += f"""
                window.waypointPath = L.polyline({path_coords_str}, {{
                    color: 'red',
                    weight: 2,
                    opacity: 0.8
                }}).addTo(droneMap);
                
                // Tüm waypoint'leri görecek şekilde haritayı ayarla
                var bounds = L.latLngBounds({path_coords_str});
                droneMap.fitBounds(bounds, {{padding: [50, 50]}});
            """
        
        self.wpWebView.page().runJavaScript(markers_script)

    def readTableCoordinates(self):
        coordinates = []
        table = self.uiWpWindow.coordinateWidget
        
        for row in range(table.rowCount()):
            lat_item = table.item(row, 0)
            lon_item = table.item(row, 1)
            alt_item = table.item(row, 2)
            
            if lat_item and lon_item and alt_item and lat_item.text() and lon_item.text() and alt_item.text():
                try:
                    lat = float(lat_item.text())
                    lon = float(lon_item.text())
                    alt = float(alt_item.text())
                    coordinates.append((lat, lon, alt))
                except ValueError:
                    continue
        
        return coordinates

    def wpYukle(self):
        coordinates = self.readTableCoordinates()
        
        if not coordinates:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("Tabloda geçerli koordinat bulunamadı.")
            msg.setWindowTitle("Uyarı")
            msg.exec_()
            return
            
        self.uiWpWindow.yukleButton.setEnabled(False)
        self.uiWpWindow.yukleButton.setText("Yükleniyor...")

        self.wpSettingsWindow = QtWidgets.QMainWindow()
        self.uiWpSettingsWindow = Ui_WaypointsSettingWindow()
        self.uiWpSettingsWindow.setupUi(self.wpSettingsWindow)
        self.wpSettingsWindow.show()

        self.wpSettingsWindow.repaint()
        screen = QtWidgets.QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.wpSettingsWindow.frameGeometry()

        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.wpSettingsWindow.move(x, y)

        self.uiWpSettingsWindow.settingProgressBar.setVisible(True)
        self.uiWpSettingsWindow.settingProgressBar.setValue(0)
        self.uiWpSettingsWindow.settingLabel.setVisible(True)
        self.uiWpSettingsWindow.settingLabel.setText("Başlatılıyor...")
        
        self.wpLoadThread = WaypointLoadThread(self.drone, coordinates)
        self.wpLoadThread.finished.connect(self.onWaypointLoadFinished)
        self.wpLoadThread.progress.connect(self.onWaypointLoadProgress)
        self.wpLoadThread.start()

    def onWaypointLoadProgress(self, progress, message):
        self.uiWpSettingsWindow.settingProgressBar.setValue(progress)
        self.uiWpSettingsWindow.settingLabel.setText(message)

    def onWaypointLoadFinished(self, success):
        self.uiWpWindow.yukleButton.setEnabled(True)
        self.uiWpWindow.yukleButton.setText("Yükle")
        
        if hasattr(self, 'wpSettingsWindow'):
            QtCore.QTimer.singleShot(1000, self.wpSettingsWindow.close)
        
        if success:
            coordinates = self.readTableCoordinates()
            if coordinates:
                markers_script = """
                    if (window.waypointMarkers) {
                        window.waypointMarkers.forEach(function(marker) {
                            droneMap.removeLayer(marker);
                        });
                    }
                    window.waypointMarkers = [];
                """
                
                # Waypoint markerları
                for i, (lat, lon, alt) in enumerate(coordinates, 1):
                    markers_script += f"""
                        var marker = L.marker([{lat}, {lon}]).addTo(droneMap)
                            .bindTooltip('{i}', {{
                                permanent: true,
                                direction: 'center',
                                offset: [-15, -30],
                                className: 'waypoint-label',
                                opacity: 1,
                                interactive: false
                            }});
                        window.waypointMarkers.push(marker);
                    """
                
                if len(coordinates) > 1:
                    path_coords = [[lat, lon] for lat, lon, _ in coordinates]
                    path_coords_str = str(path_coords).replace('(', '[').replace(')', ']')
                    
                    markers_script += f"""
                        if (window.waypointPath) {{
                            droneMap.removeLayer(window.waypointPath);
                        }}

                        window.waypointPath = L.polyline({path_coords_str}, {{
                            color: 'red',
                            weight: 2,
                            opacity: 0.8
                        }}).addTo(droneMap);
                    """
                
                self.webView.page().runJavaScript(markers_script)

    def rtl(self):
        if self.droneConnected is False:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Lütfen önce drone'a bağlanın.")
            msg.setWindowTitle("Uyarı")
            msg.exec_()
        else:
            index = self.ui.modCombo.findText("RTL")
            self.ui.modCombo.setCurrentIndex(index)

            self.modeChange()

    def closeEvent(self, event):
        if hasattr(self, 'map_thread') and self.map_thread:
            self.map_thread.stop()
            self.map_thread.wait()
        if hasattr(self, 'cameraThread'):
            self.cameraThread.stop()
            self.cameraThread.wait()
        event.accept()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.ui.cameraLabel.setPixmap(QPixmap.fromImage(image))
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.resize(1800, 1200)
        self.ui.cameraLabel.resize(640, 480)
        th = CameraThread(self)
        th.changePixmap.connect(self.setImage)
        th.start()
        self.show()

    def modeChange(self):
        if self.droneConnected is False:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Lütfen önce drone'a bağlanın.")
            msg.setWindowTitle("Uyarı")
            msg.exec_()
        else:
            self.ui.modLabel.setText("<html><head/><body><p><span style=\" font-weight:600; color:#fffe08;\">Mod ayarlanıyor...</span></p></body></html>")
            self.modeThread = ModeChangeThread(self.drone, self.ui.modLabel, self.ui.modCombo)
            self.modeThread.modeChanged.connect(self.onModeChanged)
            self.modeThread.start()

    def onModeChanged(self):
        self.ui.modLabel.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Şuanki mod</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#42FF2F;">{self.drone.mode}</span></p></body></html>')
        self.tabloItemEkle(f"Mod değiştirildi. Yeni mod: {self.drone.mode}")

    def connect(self):
        if self.droneConnected is False:
            self.connectingWindow = QtWidgets.QMainWindow()
            self.uiConnectingWindow = Ui_ConnectingWindow()
            self.uiConnectingWindow.setupUi(self.connectingWindow)
            self.connectingWindow.show()

            # Progress bar'ı sıfırla
            self.uiConnectingWindow.parameterProgressBar.setValue(0)

            # Pencereyi ortala
            self.connectingWindow.repaint()
            screen = QtWidgets.QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            window_geometry = self.connectingWindow.frameGeometry()

            x = (screen_geometry.width() - window_geometry.width()) // 2
            y = (screen_geometry.height() - window_geometry.height()) // 2
            self.connectingWindow.move(x, y)

            self.port = self.ui.PortCombo.currentText()
            self.baudRate = int(self.ui.BaudrateCombo.currentText())

            self.paramThread = ParamLoadThread(self.port, self.baudRate)
            self.paramThread.progress_update.connect(self.updateLoadingText)
            self.paramThread.progress_bar_update.connect(self.updateProgressBar)
            self.paramThread.finished.connect(self.onConnectionFinished)
            self.paramThread.start()
        else:
            # Waypoint markerlarını ve çizgileri temizle
            clear_markers_script = """
                if (window.waypointMarkers) {
                    window.waypointMarkers.forEach(function(marker) {
                        droneMap.removeLayer(marker);
                    });
                    window.waypointMarkers = [];
                }
                if (window.waypointPath) {
                    droneMap.removeLayer(window.waypointPath);
                    window.waypointPath = null;
                }
            """
            self.webView.page().runJavaScript(clear_markers_script)
            
            self.map_thread.stop()
            self.flight_data_thread.stop()
            
            self.drone.vehicle.close()
            self.droneConnected = False
            self.ui.BaglanButton.setText("Bağlan")
            self.ui.BaglanButton.setStyleSheet("background-color: rgb(239, 41, 41)")
            self.ui.bilgiLabel.setStyleSheet("color: rgb(255, 255, 255)")
            self.ui.bilgiLabel.setText("Bağlantı koparıldı.")
            print("Bağlantı koparıldı.")

            self.cameraThread.stop()

            self.ui.modLabel.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Şuanki mod</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#ff0000;">Bağlantı yok</span></p></body></html>')
            self.ui.armLabel.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Arm</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#ff0000;">Bağlantı yok</span></p></body></html>')
            self.ui.yukseklikLabel.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Yükseklik</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#ff0000;">Bağlantı yok</span></p></body></html>')

    def getIconBase64(self):
        possible_paths = [
            "images/drone.png",
            "../images/drone.png",
            os.path.join(os.path.dirname(__file__), "images/drone.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "images/drone.png")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode()
                        return f"data:image/png;base64,{encoded_string}"
                except Exception as e:
                    print(f"Icon okuma hatası: {e}")
                    continue
        
        print("Uyarı: Drone ikonu bulunamadı! Varsayılan marker kullanılacak.")
        return None

    def updateLoadingText(self, text):
        self.uiConnectingWindow.connectingLabel.setAlignment(Qt.AlignCenter)
        self.uiConnectingWindow.connectingLabel.setText(text)

    def updateProgressBar(self, value):
        self.uiConnectingWindow.parameterProgressBar.setValue(value)

    def onConnectionFinished(self, success, message, drone):
        self.uiConnectingWindow.connectingLabel.setText(message)
        if success:
            self.cameraThread = CameraThread("192.168.172.209")
            self.cameraThread.changePixmap.connect(self.setImage)
            self.cameraThread.start()

            self.drone = drone
            self.droneConnected = True

            self.webView.page().runJavaScript(
                f'initializeMarker({self.drone.location.lat}, {self.drone.location.lon});'
            )
            
            # Mevcut waypoint'leri haritada göster
            waypoints = self.drone.get_waypoints()
            print(waypoints)
            if waypoints and len(waypoints) > 0:
                markers_script = """
                    if (window.waypointMarkers) {
                        window.waypointMarkers.forEach(function(marker) {
                            droneMap.removeLayer(marker);
                        });
                    }
                    window.waypointMarkers = [];
                """
                
                # Waypoint markerları
                for i, wp in enumerate(waypoints):
                    if i == 0 or i == 8:  # TODO
                        continue
                    markers_script += f"""
                        var marker = L.marker([{wp['x']}, {wp['y']}]).addTo(droneMap)
                            .bindTooltip('{i}', {{
                                permanent: true,
                                direction: 'center',
                                offset: [-15, -30],
                                className: 'waypoint-label',
                                opacity: 1,
                                interactive: false
                            }});
                        window.waypointMarkers.push(marker);
                    """
                
                if len(waypoints) > 1:
                    path_coords = [[wp['x'], wp['y']] for i, wp in enumerate(waypoints[1:], 1) if i != 8] # TODO path_coords = [[wp['x'], wp['y']] for wp in waypoints[1:]]
                    path_coords_str = str(path_coords).replace('(', '[').replace(')', ']')
                    
                    markers_script += f"""
                        // Önceki path'i temizle
                        if (window.waypointPath) {{
                            droneMap.removeLayer(window.waypointPath);
                        }}
                        // Yeni path'i çiz
                        window.waypointPath = L.polyline({path_coords_str}, {{
                            color: 'red',
                            weight: 2,
                            opacity: 0.8
                        }}).addTo(droneMap);
                    """
                
                self.webView.page().runJavaScript(markers_script)
            
            self.map_thread = MapUpdateThread(self.drone)
            self.map_thread.setParent(self)  # Parent'ı ayarla
            self.map_thread.start()
            time.sleep(1)
            self.connectingWindow.close()
            self.ui.BaglanButton.setText("Bağlandı")
            self.ui.bilgiLabel.setStyleSheet("color: rgb(255, 255, 255)")
            self.ui.bilgiLabel.setText(f"Bağlantı kuruldu.\nPort: {self.port} - Baud rate: {self.baudRate}")
            self.ui.BaglanButton.setStyleSheet("background-color: rgb(115, 210, 22)")

            index = self.ui.modCombo.findText(self.drone.mode)

            self.ui.modLabel.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Şuanki mod</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#42FF2F;">{self.drone.mode}</span></p></body></html>')

            if index >= 0:
                self.ui.modCombo.setCurrentIndex(index)

            if self.drone.isArmed():
                self.ui.armLabel.setText("<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Arm</span><span style=\" font-weight:600;\">: </span><span style=\" font-weight:600; color:#42FF2F;\">Armed</span></p></body></html>")
            else:
                self.ui.armLabel.setText("<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline;\">Arm</span><span style=\" font-weight:600;\">: </span><span style=\" font-weight:600; color:#ff0000;\">Disarmed</span></p></body></html>")

            self.ui.yukseklikLabel.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Şuanki yükseklik</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#42FF2F;">{self.drone.location.alt}</span></p></body></html>')

            QtCore.QTimer.singleShot(1000, self.startFlightDataThread)

    def startFlightDataThread(self):
        self.flight_data_thread = FlightDataThread(self.drone)
        self.flight_data_thread.updateSignal.connect(self.updateFlightIndicators)
        self.flight_data_thread.start()

    def updateFlightIndicators(self, flight_data):
        self.flight_indicators.updateFlightData(flight_data)

    def gorev(self):
        if self.droneConnected is False:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Lütfen önce drone'a bağlanın.")
            msg.setWindowTitle("Uyarı")
            msg.exec_()
        else:
            self.tabloItemEkle("Görev başlatıldı.")
            self.missionCompleted = False
            self.ui.gorevButton.setStyleSheet("background-color: rgb(253, 255, 53)")
            self.ui.gorevButton.setText("Görev Yapılıyor...")
            self.tabloItemEkle("Görevin tamamlanması bekleniyor...")
            self.missionThread = MissionThread(self.drone)
            self.missionThread.missionCompleted.connect(self.onMissionCompleted)
            self.missionThread.start()

    def onMissionCompleted(self):
        self.ui.gorevButton.setStyleSheet("background-color: rgb(55, 255, 0)")
        self.ui.gorevButton.setText("Görev Tamamlandı")
        self.ui.modLabel.setText(f'<html><head/><body><p><span style=" font-weight:600; text-decoration: underline;">Şuanki mod</span><span style=" font-weight:600;">: </span><span style=" font-weight:600; color:#42FF2F;">{self.drone.mode}</span></p></body></html>')
        self.missionCompleted = True
    
    def createInitialMap(self):
        self.m = folium.Map(
            location=mapBaslangicKoordinati,
            zoom_start=20,
            tiles=folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr="QuadRuplet", max_zoom=22)
        )
    
        script = f"""
            <script>
                var droneMarker = null;
                var droneMap = null;
                var droneIcon = {f'L.icon({{ iconUrl: "{self.icon_base64}", iconSize: [50, 50], iconAnchor: [25, 25] }})' if self.icon_base64 else 'null'};
                var droneTrail = [];
                var trailLayer = null;
                var trackingEnabled = true;  // Tracking mode on by default

                document.addEventListener('DOMContentLoaded', function() {{
                    var mapDiv = document.querySelector('.folium-map');
                    droneMap = window[mapDiv.id.replace('map_', 'map_')];
                
                    // Create custom control button
                    L.Control.TrackingButton = L.Control.extend({{
                        options: {{
                            position: 'bottomleft'
                        }},
                        onAdd: function(map) {{
                            var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                            var button = L.DomUtil.create('a', 'tracking-button', container);
                            button.innerHTML = "🎯";
                            button.title = "Drone Takibi";
                            button.style.display = "flex";
                            button.style.justifyContent = "center";
                            button.style.alignItems = "center";
                            button.style.width = "30px";
                            button.style.height = "30px";
                            button.style.backgroundColor = "#4CAF50";
                            button.style.color = "white";
                            button.style.cursor = "pointer";
                            button.style.fontSize = "16px";
                            button.style.textDecoration = "none";
                        
                            L.DomEvent.on(button, 'click', function() {{
                                trackingEnabled = !trackingEnabled;
                                if (trackingEnabled) {{
                                    button.style.backgroundColor = "#4CAF50";
                                    button.title = "Drone Takibi: Aktif";
                                }} else {{
                                    button.style.backgroundColor = "#F44336";
                                    button.title = "Drone Takibi: Pasif";
                                }}
                            }});

                            L.DomEvent.disableClickPropagation(container);
                            return container;
                        }}
                    }});
                
                    new L.Control.TrackingButton().addTo(droneMap);
                }});
            
                window.initializeMarker = function(lat, lng) {{
                    if (droneMap && !droneMarker) {{
                        droneMarker = L.marker([lat, lng], droneIcon ? {{icon: droneIcon}} : {{}}).addTo(droneMap);
                        droneMap.setView([lat, lng], droneMap.getZoom());
                    }}
                }};
            
                window.updateMarkerPosition = function(lat, lng) {{
                    if (droneMarker && droneMap) {{
                        droneMarker.setLatLng([lat, lng]);
                        if (trackingEnabled) {{
                            droneMap.setView([lat, lng], droneMap.getZoom());
                        }}
                    }}
                }};

                window.removeDroneMarker = function() {{
                    if (droneMarker) {{
                        droneMap.removeLayer(droneMarker);
                        droneMarker = null;
                    }}
                }};

                window.addTrailPoint = function(lat, lng) {{
                    var newPoint = [lat,lng];
                    droneTrail.push(newPoint);

                    if (trailLayer) {{
                        droneMap.removeLayer(trailLayer);
                    }}

                    if (droneTrail.length > 1) {{
                        trailLayer = L.polyline(droneTrail, {{color: 'yellow'}}).addTo(droneMap);
                    }}

                    setTimeout(function() {{
                        if (droneTrail.length > 1) {{
                            droneTrail.shift();

                            if (trailLayer) {{
                                droneMap.removeLayer(trailLayer);
                            }}

                            if (droneTrail.length > 1) {{
                                trailLayer = L.polyline(droneTrail, {{color: 'yellow'}}).addTo(droneMap);
                            }}
                        }}
                    }}, 10000)
                }}
            
                // Toggle tracking state
                window.toggleTracking = function() {{
                    trackingEnabled = !trackingEnabled;
                    return trackingEnabled;
                }}
            </script>
        """
    
        self.m.get_root().html.add_child(folium.Element(script))

        data = io.BytesIO()
        self.m.save(data, close_file=False)
        self.webView = QWebEngineView()
        self.webView.setHtml(data.getvalue().decode())
        self.ui.mapLayout.addWidget(self.webView)

    def updateMarker(self):
        if self.droneConnected is True:
            try:
                lat = self.drone.location.lat
                lon = self.drone.location.lon
        
                if (isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and 
                    -90 <= lat <= 90 and -180 <= lon <= 180):
                    self.webView.page().runJavaScript(
                        f'updateMarkerPosition({lat}, {lon});'
                    )

                    self.webView.page().runJavaScript(
                        f'addTrailPoint({lat}, {lon});'
                    )
                else:
                    print(f"Geçersiz koordinatlar: lat={lat}, lon={lon}")
            
            except Exception as e:
                print(f"Güncelleme hatası: {str(e)}")
        else:
            self.webView.page().runJavaScript("removeDroneMarker();")


def app():
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    win.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    app()
