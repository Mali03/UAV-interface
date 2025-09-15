import cv2
import socket
import math
import pickle

host = "127.0.0.1"
port = 5000
maxLength = 1472

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #? UDP
except Exception as e:
    print(f"Bağlantı kurulamadı: {e}")
finally:
    print("Bağlantı kuruldu.")

print("Kamera açılıyor...")

cap = cv2.VideoCapture(0)
boolean, frame = cap.read()

print("Kamera açıldı veri akışı yapılıyor.")

while boolean: #? frame varsa True döner
    booleanval, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50]) #? kameradan alınan veri jpg formatına sıkıştırılır (50 -> sıkıştırma kalitesi)

    if booleanval:
        buffer = buffer.tobytes() #? sıkıştırılan görüntüyü byte array'e dönüştürülür
        bufferSize = len(buffer) #? bayt olarak boyutu

        numOfPacks = 1 #? bölünme sayısı
        if bufferSize > maxLength:
            numOfPacks = math.ceil(bufferSize/maxLength) #? çerçevenin boyutu maxlengthden büyükse parçalanır

        frameDict = { "packs": numOfPacks } #? parça sayısı gönderilir
        
        try:
            sock.sendto(pickle.dumps(frameDict), (host, port))
        except OSError as e:
            if e.errno == 101:
                print("İnternet erişimi koptu. İnternet erişimi bekleniyor.")
                continue
        
        left = 0
        right = maxLength

        for i in range(numOfPacks):
            data = buffer[left:right]
            left = right #? gönderilen parçalar atlanır ve yenileri eklenir
            right += maxLength

            try:
                sock.sendto(data, (host, port))
            except OSError as e:
                if e.errno == 101:
                    print("İnternet erişimi koptu. İnternet erişimi bekleniyor.")
                    continue

    boolean, frame = cap.read()

sock.close()

print("Bağlantı sonlandırıldı.")