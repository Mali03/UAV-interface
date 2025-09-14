from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
import json
import base64
import os

class FlightIndicatorsWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.setupWebChannel()
        
    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Web view for flight indicators
        self.webView = QWebEngineView()
        layout.addWidget(self.webView)
        
        self.loadFlightIndicators()
        
    def setupWebChannel(self):
        self.channel = QWebChannel(self.webView.page())
        self.bridge = FlightDataBridge()
        self.channel.registerObject('pybridge', self.bridge)
        self.webView.page().setWebChannel(self.channel)
        
    def getSvgAsBase64(self, filename):
        svg_path = os.path.join("images", "flight_indicators", filename)
    
        with open(svg_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()
            return f"data:image/svg+xml;base64,{encoded}"
        
    def loadFlightIndicators(self):
        # SVG arkaplanlarını yükle
        horizon_ball = self.getSvgAsBase64("horizon_ball.svg")
        speed_mechanics = self.getSvgAsBase64("speed_mechanics.svg")
        altitude_ticks = self.getSvgAsBase64("altitude_ticks.svg")
        heading_yaw = self.getSvgAsBase64("heading_yaw.svg")
        turn_coordinator = self.getSvgAsBase64("turn_coordinator.svg")
        vertical_mechanics = self.getSvgAsBase64("vertical_mechanics.svg")
        fi_needle = self.getSvgAsBase64("fi_needle.svg")
        fi_circle = self.getSvgAsBase64("fi_circle.svg")
        horizon_mechanics = self.getSvgAsBase64("horizon_mechanics.svg")
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Professional Flight Indicators</title>
    <style>
        body {{
            margin: 0;
            padding: 5px;
            background-color: #000;
            font-family: 'Arial', sans-serif;
            color: white;
            overflow: hidden;
        }}
        .indicators-container {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: repeat(2, 1fr);
            gap: 8px;
            width: 100%;
            max-width: 500px;
            height: 280px;
            margin: 0 auto;
            padding: 5px;
        }}
        .indicator {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 6px;
            border: 1px solid #333;
            border-radius: 6px;
            background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
            box-shadow: 0 3px 10px rgba(0,0,0,0.5);
            transition: all 0.3s ease;
        }}
        .gauge-container {{
            position: relative;
            width: 120px;
            height: 120px;
            margin: 1px;
        }}
        .gauge-background {{
            width: 100%;
            height: 100%;
            border-radius: 50%;
            position: relative;
            overflow: hidden;
        }}
        .gauge-needle {{
            position: absolute;
            top: 50%;
            left: 50%;
            width: 3px;
            height: 40px;
            background: linear-gradient(to top, #ff0000, #ff6666);
            transform-origin: bottom center;
            transform: translate(-50%, -100%);
            transition: transform 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            z-index: 10;
            border-radius: 2px;
            box-shadow: 0 0 10px rgba(255,0,0,0.7);
        }}
        .gauge-center {{
            position: absolute;
            top: 50%;
            left: 50%;
            width: 10px;
            height: 10px;
            background: radial-gradient(circle, #333, #000);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            z-index: 15;
            border: 2px solid #666;
        }}
        .indicator-label {{
            color: #00ff00;
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            margin-top: 2px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            min-height: 12px;
        }}
        .attitude-container {{
            position: relative;
            width: 120px;
            height: 120px;
            margin: 1px;
            overflow: hidden;  /* Taşan kısımları gizle */
            border-radius: 50%; /* Dairesel sınır */
        }}
        .attitude-ball {{
            width: 100%;
            height: 100%;
            border-radius: 50%;
            position: relative;
            overflow: hidden;
            background-image: url('{horizon_ball if horizon_ball else ""}');
            background-size: cover;
            background-position: center;
            transition: transform 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);  /* Daha yumuşak ve uzun geçiş */
        }}
        .attitude-mechanics {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('{horizon_mechanics if horizon_mechanics else ""}');
            background-size: cover;
            background-position: center;
            pointer-events: none;
            z-index: 5;
            /* Çizgiler sabit kalacak - transform kaldırıldı */
        }}
        .aircraft-symbol {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #ffff00;
            font-size: 16px;
            font-weight: bold;
            z-index: 10;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }}
        
        /* Professional gauge backgrounds */
        .airspeed-gauge {{
            background-image: url('{speed_mechanics if speed_mechanics else ""}');
            background-size: cover;
            background-position: center;
        }}
        .altitude-gauge {{
            background-image: url('{altitude_ticks if altitude_ticks else ""}');
            background-size: cover;
            background-position: center;
        }}
        .heading-gauge {{
            background-image: url('{heading_yaw if heading_yaw else ""}');
            background-size: cover;
            background-position: center;
        }}
        .turn-gauge {{
            background-image: url('{turn_coordinator if turn_coordinator else ""}');
            background-size: cover;
            background-position: center;
        }}
        .vertical-gauge {{
            background-image: url('{vertical_mechanics if vertical_mechanics else ""}');
            background-size: cover;
            background-position: center;
        }}
    </style>
</head>
<body>
    <div class="indicators-container">
        <div class="indicator">
            <div class="gauge-container">
                <div class="gauge-background airspeed-gauge">
                    <div class="gauge-needle" id="airspeedNeedle"></div>
                    <div class="gauge-center"></div>
                </div>
            </div>
            <div class="indicator-label" id="airspeedLabel">Hız: 0 m/s</div>
        </div>
        
        <div class="indicator">
            <div class="attitude-container">
                <div class="attitude-ball" id="attitudeBall">
                </div>
                <div class="attitude-mechanics" id="attitudeMechanics">
                    <div class="aircraft-symbol">✈</div>
                </div>
            </div>
            <div class="indicator-label" id="attitudeLabel">P:0° R:0°</div>
        </div>
        
        <div class="indicator">
            <div class="gauge-container">
                <div class="gauge-background altitude-gauge">
                    <div class="gauge-needle" id="altitudeNeedle"></div>
                    <div class="gauge-center"></div>
                </div>
            </div>
            <div class="indicator-label" id="altitudeLabel">İrtifa: 0 m</div>
        </div>
        
        <div class="indicator">
            <div class="gauge-container">
                <div class="gauge-background turn-gauge">
                    <div class="gauge-needle" id="turnNeedle"></div>
                    <div class="gauge-center"></div>
                </div>
            </div>
            <div class="indicator-label" id="turnLabel">Dönüş hızı: 0°/s</div>
        </div>
        
        <div class="indicator">
            <div class="gauge-container">
                <div class="gauge-background heading-gauge">
                    <div class="gauge-needle" id="headingNeedle"></div>
                    <div class="gauge-center"></div>
                </div>
            </div>
            <div class="indicator-label" id="headingLabel">Baş açısı: 0°</div>
        </div>
        
        <div class="indicator">
            <div class="gauge-container">
                <div class="gauge-background vertical-gauge">
                    <div class="gauge-needle" id="varioNeedle"></div>
                    <div class="gauge-center"></div>
                </div>
            </div>
            <div class="indicator-label" id="varioLabel">Dikey hız: 0 m/s</div>
        </div>
    </div>

    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        let flightData = {{}};
        
        function updateIndicators(data) {{
            flightData = data;
            
            // Update airspeed with smooth animation
            const airspeed = data.airspeed || 0;
            const airspeedAngle = Math.min((airspeed * 10) * 2, 340); // Scale for realistic movement
            document.getElementById('airspeedNeedle').style.transform = 
                `translate(-50%, -100%) rotate(${{airspeedAngle}}deg)`;
            
            // Update attitude with realistic 3D movement
            let pitch = ((data.pitch || 0) * 180) / Math.PI;
            let roll = ((data.roll || 0) * 180) / Math.PI;
            
            // Sınırları kontrol et - pitch ve roll değerlerini sınırla
            pitch = Math.max(-90, Math.min(90, pitch));  // Pitch: -90° ile +90° arası
            roll = Math.max(-90, Math.min(90, roll));    // Roll: -90° ile +90° arası
            
            // Pitch için hafif yukarı-aşağı hareket (sınırlı)
            const pitchTranslate = Math.max(-15, Math.min(15, pitch * 0.3)); // Hafif hareket: maksimum ±15px
            
            // Arka plan hareket eder, çizgiler sabit kalır
            const attitudeBall = document.getElementById('attitudeBall');
            
            // Apply pitch and roll transforms to background (rotation + hafif yukarı hareket)
            if (attitudeBall) {{
                attitudeBall.style.transform = `rotate(${{roll}}deg) translateY(${{-pitchTranslate}}px)`;
            }}
            
            // Update altitude
            const altitude = data.altitude || 0;
            const altitudeAngle = altitude * 3.6; // 100m = 360°, 10m = 36° (10'ar 10'ar artış)
            document.getElementById('altitudeNeedle').style.transform = 
                `translate(-50%, -100%) rotate(${{altitudeAngle}}deg)`;
            
            // Update turn rate
            const turnRate = data.turn_rate || 0;
            const turnAngle = Math.max(-60, Math.min(60, turnRate * 6)); // Limit to realistic range
            document.getElementById('turnNeedle').style.transform = 
                `translate(-50%, -100%) rotate(${{turnAngle}}deg)`;
            
            // Update heading - 0-360 derece aralığında tut
            let heading = ((data.heading || 0) * 180) / Math.PI;
            // Modulo işlemi ile 0-360 aralığında tut
            heading = ((heading % 360) + 360) % 360;
            document.getElementById('headingNeedle').style.transform = 
                `translate(-50%, -100%) rotate(${{heading}}deg)`;
            
            // Update vertical speed
            const verticalSpeed = data.vertical_speed || 0;
            const varioAngle = Math.max(-90, Math.min(90, verticalSpeed * 15)); // Scale and limit
            document.getElementById('varioNeedle').style.transform = 
                `translate(-50%, -100%) rotate(${{varioAngle}}deg)`;
            
            // Update labels with current values
            document.getElementById('airspeedLabel').textContent = `Hız: ${{airspeed.toFixed(1)}} m/s`;
            document.getElementById('attitudeLabel').textContent = `P:${{pitch.toFixed(1)}}° R:${{roll.toFixed(1)}}°`;
            document.getElementById('altitudeLabel').textContent = `İrtifa: ${{altitude.toFixed(1)}} m`;
            document.getElementById('turnLabel').textContent = `Dönüş hızı: ${{turnRate.toFixed(1)}}°/s`;
            document.getElementById('headingLabel').textContent = `Baş açısı: ${{heading.toFixed(1)}}°`;
            document.getElementById('varioLabel').textContent = `Dikey hız: ${{verticalSpeed.toFixed(1)}} m/s`;
        }}
        
        // WebChannel setup
        new QWebChannel(qt.webChannelTransport, function(channel) {{
            window.pybridge = channel.objects.pybridge;
        }});
        
        // Expose function to Python
        window.updateFlightData = updateIndicators;
        
        // Initialize with smooth animations
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Professional Flight Indicators Loaded');
        }});
    </script>
</body>
</html>
        """
        self.webView.setHtml(html_content)
        
    def updateFlightData(self, flight_data):
        """Uçuş verilerini güncelle"""
        script = f"window.updateFlightData({json.dumps(flight_data)});"
        self.webView.page().runJavaScript(script)

class FlightDataBridge(QtCore.QObject):
    """Python-JavaScript köprüsü"""
    def __init__(self):
        super().__init__()

    @QtCore.pyqtSlot(str)
    def logMessage(self, message):
        print(f"Web mesajı: {message}")