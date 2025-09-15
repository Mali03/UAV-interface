# UAV Ground Control Interface | İHA Yer Kontrol Arayüzü 🚀

![Python](https://img.shields.io/badge/Python-3.12-blue)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15.10-green)
![PyMavlink](https://img.shields.io/badge/PyMavlink-2.4.47-orange)

EN - This project is a detailed GUI for UAVs such as drones and fixed-wing aircrafts. It allows you to control your UAV and perform autonomius tasks with visualized data. See **Example.mp4** for an overview of its features.

TR - Bu proje, dronelar ve sabit kanatlı İHA’lar için detaylı bir grafiksel arayüzdür. Proje, görselleştirilmiş veriler ile İHA'nızı kontrol etmenizi ve otonom görevler yapmanızı sağlar. Özelliklerine genel bir bakış için **Example.mp4** dosyasına göz atın.

![](https://i.imgur.com/suw47kf.jpeg)

# 🌍 Languages
You can select your preferred languages below:

- [English](#English)
- [Türkçe](#Türkçe)

# English

The interface provides users with real-time telemetry data, the flight path on the map, control buttons, the route creation window, the UAV camera view, and log records.

## 🧾 Contents
- [Features](#-features)
- [Installation](#-installation)
- [SITL Simulation Installation](#-sitl-simulation-installation-linux)
- [Qt Designer Installation](#-qt-designer-installation-linux)
- [Used Technologies](#-used-technologies)
- [License](#-license)
- [Need help](#-need-help)

## 🔍 Features
- Real-time Telemetry
  - Velocity, altitude and vertical speed indicators.
  
  - Monitoring of flight parameters such as yaw rate and heading angle.
  
  - Real-time display of Pitch (P) and Roll (R) angles.

- UAV Camera View
  - Live UAV camera feed

- Flight Path Visualization on Map
  - UAV position displayed on the map during flight

  - Predefined waypoints shown on the map

  - Route lines visualizing UAV movement

- Control and Mission Management
  - Arm / Disarm: Activate or deactivate motors

  - Take Off: Automated takeoff to a target altitude

  - RTL (Return to Launch): Return drone to home point

  - Set Waypoint: Add mission points directly on the map

  - Start Mission: Set the mode to AUTO

  - Flight mode selection (GUIDED, AUTO, etc.) with options
 
- Mission and Flight Logs

  - Timestamped log of all commands and mission statuses

## 🛠 Installation
### Clone this repository
```
git clone https://github.com/Mali03/UAV-interface.git
cd UAV-interface
```

### Install dependencies
```
pip install PyQt5 (If it doesn't work -> sudo apt install python3-pyqt5)
pip install PyQtWebEngine (If it doesn't work -> sudo apt install python3-pyqt5.qtwebengine)
```

### Start the GUI
```
python gui.py
```

For testing go [SITL Simulation Installation](#-sitl-simulation-installation-linux)

## ⚙ SITL Simulation Installation (Linux)

Step-by-step guide to test GUI on simulation

### Install git
```
sudo apt-get update
sudo apt-get upgrade

sudo apt-get install git
sudo apt-get install gitk git-gui
```
### Clone ArduPilot 
```
git clone https://github.com/ArduPilot/ardupilot.git
```
### Install necessary dependencies
```
cd ardupilot
git submodule update --init --recursive

sudo apt install python-matplotlib python-serial python-wxgtk4.0 python-wxtools python-lxml python-scipy python-opencv ccache gawk python-pip python-pexpect

gedit ~/.bashrc

// put this 2 code to the end and save
export PATH=$PATH:$HOME/ardupilot/Tools/autotest
export PATH=/usr/lib/ccache:$PATH

. ~/.bashrc
```
### Install MAVProxy
```
sudo pip install future pymavlink MAVProxy
```
### Start SITL Simulation
```
cd ~/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py -w
```

### Connect from GUI to simulation
Select ip and port to `udpin:localhost:14550` and click on **Bağlan** button.

### Camera view flow
If you want to test camera view transmission, after connection has finished execute the `client_camera.py` file.

## 🖼 Qt Designer Installation (Linux)
You can design the interface with opening `.ui` files in Qt Designer.

After editing the `.ui` file you need to convert `.ui` to `.py` with executing this commands:

`pyuic5 -x windows/MainWindow.ui -o windows/MainWindow.py`

or `python3 -m PyQt5.uic.pyuic -x windows/MainWindow.ui -o windows/MainWindow.py`.

### Install Qt Designer
```
sudo apt-get install qttools5-dev-tools
sudo apt-get install qttools5-dev
```

## 🌐 Used Technologies
- PyQT5 (Qt Framework) and PyQtWebEngine (Map integration)
- PyMavlink (Mavlink protocol)
- Folium (Map)
- Opencv-python (Camera)
- Socket (Live camera view transmission)

## 📚 License
This project is licensed under the **MIT License** - see the [LICENSE](https://github.com/Mali03/UAV-interface/blob/main/LICENSE) file for details.

## ❓ Need Help
If you need any help contact me on [LinkedIn](https://www.linkedin.com/in/mali03/).

# Türkçe

Arayüz, gerçek zamanlı telemetri verilerini, harita üzerinde uçuş rotasını, kontrol butonlarını, rota oluşturma penceresini, İHA kamera görüntüsünü ve log kayıtlarını kullanıcıya sunar.

## 🧾 İçerikler
- [Özellikler](#-özellikler)
- [Kurulum](#-kurulum)
- [SITL Simülasyon Kurulumu](#-sitl-simülasyon-kurulumu-linux)
- [Qt Designer Kurulumu](#-qt-designer-kurulumu-linux)
- [Kullanılan Teknolojiler](#-kullanılan-teknolojiler)
- [Lisans](#-lisans)
- [Yardım](#-yardım)

## 🔍 Özellikler
- Gerçek Zamanli Telemetri
  - Hız, yükseklik and dikey hız göstergeleri.
   
  - Yaw açısı, baş açısı gibi uçuş parametrelerini görüntüleme
  
  - Pitch (P) ve Roll (R) açılarının gerçek zamanlı gösterimi.

- İHA Kamera Görüntüsü
  - Canlı İHA kamera yayını

- Haritada Uçuş Rotası Görselleştirmesi
  - Uçuş sırasında haritada görüntülenen İHA konumu

  - Haritada gösterilen önceden tanımlanmış yol haritası

  - İHA hareketini görselleştiren rota çizgileri

- Kontrol ve Görev Yönetimi
  - Arm / Disarm: Motorları aktif ve deaktif et

  - Take Off: Hedef irtifaya otonom kalkış yap

  - RTL (Return to Launch): Home noktasına geri dön

  - Waypoint Ayarla: Harita üzerinden görev noktası tanımla

  - Görevi Başlat: Mod'u AUTO'ya ayarla

  - Uçuş Modu Seç (GUIDED, AUTO, vs.)
 
- Görev ve Uçuş Kayıtları

  - Zaman damgalı tüm komut ve görev durumu kayıtları

## 🛠 Kurulum
### Bu repository'i klonla
```
git clone https://github.com/Mali03/UAV-interface.git
cd UAV-interface
```

### Bağlılıklari yükle
```
pip install PyQt5 (If it doesn't work -> sudo apt install python3-pyqt5)
pip install PyQtWebEngine (If it doesn't work -> sudo apt install python3-pyqt5.qtwebengine)
```

### Arayüzü başlat
```
python gui.py
```

Test etmek için [SITL Simülasyon Kurulumu](#-sitl-simülasyon-kurulumu-linux)'e git

## ⚙ SITL Simülasyon Kurulumu (Linux)

Adım adım arayüzü simülasyonda test etmek rehber 

### Git'i indir
```
sudo apt-get update
sudo apt-get upgrade

sudo apt-get install git
sudo apt-get install gitk git-gui
```
### ArduPilot'u klonla
```
git clone https://github.com/ArduPilot/ardupilot.git
```
### Gerekli bağlılıkları yükle
```
cd ardupilot
git submodule update --init --recursive

sudo apt install python-matplotlib python-serial python-wxgtk4.0 python-wxtools python-lxml python-scipy python-opencv ccache gawk python-pip python-pexpect

gedit ~/.bashrc

// bu 2 kodu en sona koy ve kaydet
export PATH=$PATH:$HOME/ardupilot/Tools/autotest
export PATH=/usr/lib/ccache:$PATH

. ~/.bashrc
```
### MAVProxy'yi yükle
```
sudo pip install future pymavlink MAVProxy
```
### SITL simülasyonunu başlat
```
cd ~/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py -w
```

### Arayüz üzerinden simülasyona bağlan 
IP ve portu `udpin:localhost:14550` olarak seç ve **Bağlan** butonuna tıkla.

### Kamera görüntü akışı
Kamera görüntü aktarımını test etmek için bağlandıktan sonra `client_camera.py` dosyasını çalıştır.

## 🖼 Qt Designer Kurulumu (Linux)
`.ui` dosyalarını Qt Designer üzerinden açarak arayüzü dizayn edebilirsiniz.

`.ui` dosyasını düzenledikten sonra `.ui` uzantısından `.py` uzantısına çevirmen için şu kodu çalıştırman gerekiyor:

`pyuic5 -x windows/MainWindow.ui -o windows/MainWindow.py`

veya `python3 -m PyQt5.uic.pyuic -x windows/MainWindow.ui -o windows/MainWindow.py` .

### Qt Designer'ı yükle
```
sudo apt-get install qttools5-dev-tools
sudo apt-get install qttools5-dev
```

## 🌐 Kullanılan Teknolojiler
- PyQT5 (Qt Framework'ü) and PyQtWebEngine (Harita Entegrasyonu)
- PyMavlink (Mavlink protokolü)
- Folium (Harita)
- Opencv-python (Kamera)
- Socket (Canlı kamera görüntü iletimi)

## 📚 Lisans
Bu proje **MIT Lisans** altında lisanslanmıştır - detaylar için [LICENSE](https://github.com/Mali03/UAV-interface/blob/main/LICENSE) dosyasını incele.

## ❓ Yardım
Eğer bir yardıma ihtiyacın varsa bana [LinkedIn](https://www.linkedin.com/in/mali03/) üzerinden ulaş.
