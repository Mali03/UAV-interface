# UAV Ground Control Interface | İHA Yer Kontrol Arayüzü

EN - This project is a detailed GUI for UAVs such as drones and fixed-wing aircrafts. It allows you to control your UAV and perform autonomius tasks with visualized data. See **Example.mp4** for an overview of its features.

TR - Bu proje, dronlar ve sabit kanatlı uçaklar gibi İHA’lar için detaylı bir grafiksel arayüzdür. Proje, görselleştirilmiş veriler ile İHA'nızı kontrol etmenizi ve otonom görevler yapmanızı sağlar. Özelliklerine genel bir bakış için **Example.mp4** dosyasına göz atın.

![](https://i.imgur.com/suw47kf.jpeg)

# Languages
You can select your preferred languages below:

- [English](#English)
- [Türkçe](#Türkçe)

# English

The interface provides users with real-time telemetry data, the flight path on the map, control buttons, the route creation window, the drone camera view, and log records.

## Contents
- [Features](#features)
- [SITL Installation](#sitl-installation-linux)

## Features
- Real-time Telemetry
  - Velocity, altitude and vertical speed indicators.
  
  - Monitoring of flight parameters such as yaw rate and heading angle.
  
  - Real-time display of Pitch (P) and Roll (R) angles.

- Drone Camera View
  - Live drone camera feed

- Flight Path Visualization on Map
  - Drone position displayed on the map during flight

  - Predefined waypoints shown on the map

  - Route lines visualizing drone movement

- Control and Mission Management
  - Arm / Disarm: Activate or deactivate motors

  - Take Off: Automated takeoff to a target altitude

  - RTL (Return to Launch): Return drone to home point

  - Set Waypoint: Add mission points directly on the map

  - Start Mission: Set the mode to auto

  - Flight mode selection (GUIDED, AUTO, etc.) with options
 
- Mission and Flight Logs

  - Timestamped log of all commands and mission statuses

## SITL Installation (Linux)

Step-by-step guide to test GUI on simulation

### Installing git
```
sudo apt-get update
sudo apt-get upgrade

sudo apt-get install git
sudo apt-get install gitk git-gui
```
### Cloning ArduPilot 
```
git clone https://github.com/ArduPilot/ardupilot.git
```
### Installing necessary dependencies
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
### Installing MAVProxy
```
sudo pip install future pymavlink MAVProxy
```
### Starting SITL
```
cd ~/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py -w
```
# Türkçe

Arayüz, gerçek zamanlı telemetri verilerini, harita üzerinde uçuş rotasını, kontrol butonlarını, rota oluşturma penceresini, drone kamera görüntüsünü ve log kayıtlarını kullanıcıya sunar.
