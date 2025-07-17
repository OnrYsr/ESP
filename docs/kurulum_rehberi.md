# ESP32 Su Pompası Sistemi - Kurulum Rehberi

## Gerekli Malzemeler

### Elektronik Bileşenler
- **ESP32 DevKit** (herhangi bir model)
- **Su pompası** (5V/12V) - 3-6V mini pompa öneriyi
- **Röle modülü** (5V 1-Channel)
- **Nem sensörü** (analog soil moisture sensor)
- **LED** (durum göstergesi için)
- **Dirençler** (220Ω LED için)
- **Breadboard** ve jumper kablolar
- **Güç kaynağı** (pompa için uygun voltaj)

### Yazılım Gereksinimleri
- **Arduino IDE** (ESP32 board package ile)
- **Raspberry Pi OS** (Lite veya Desktop)
- **Python 3** (Flask, paho-mqtt kütüphaneleri)
- **Mosquitto** MQTT Broker

## Adım 1: Hardware Bağlantıları

### ESP32 Pin Bağlantıları
```
ESP32 GPIO2  -> Röle modülü IN pini
ESP32 GPIO4  -> Kontrol edilebilir LED pozitif bacak (220Ω direnç ile)
ESP32 GPIO13 -> Sistem durum LED pozitif bacak (220Ω direnç ile)
ESP32 A0     -> Nem sensörü analog çıkış
ESP32 3.3V   -> Nem sensörü VCC
ESP32 GND    -> Ortak toprak (nem sensörü, LED'ler, röle)
```

### Güç Bağlantıları
```
Röle modülü VCC -> 5V (ESP32 VIN veya harici güç)
Su pompası -> Röle NO (Normal Open) kontakları
Güç kaynağı -> Röle COM (Common) kontağı
```

### Bağlantı Şeması
```
[ESP32] --GPIO2--> [RÖLE] --NO/COM--> [SU POMPASI]
   |                   |
   |--GPIO4--> [KONTROL LED] (220Ω direnç ile)
   |--GPIO13-> [DURUM LED] (220Ω direnç ile)
   |                   |
   |--A0-----> [NEM SENSÖRÜ]
   |                   |
   |--3.3V/GND---------|
```

## Adım 2: Raspberry Pi Kurulumu

### 1. Sistem Güncelleme
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. MQTT Broker Kurulumu
```bash
# Otomatik kurulum için script'i çalıştır
cd raspberry-pi
chmod +x install_mosquitto.sh
./install_mosquitto.sh
```

### 3. Manuel Kurulum (opsiyonel)
```bash
# Mosquitto kurulumu
sudo apt install mosquitto mosquitto-clients -y

# Python kütüphaneleri
pip3 install paho-mqtt flask flask-cors

# Mosquitto servisini başlat
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

## Adım 3: ESP32 Programlama

### 1. Arduino IDE Kurulumu
- **File > Preferences > Additional Board Manager URLs'ye ekleyin:**
  ```
  https://dl.espressif.com/dl/package_esp32_index.json
  ```

### 2. Gerekli Kütüphaneleri Kurun
- **Tools > Manage Libraries**
- Arayın ve kurun:
  - `PubSubClient` (by Nick O'Leary)
  - `ArduinoJson` (by Benoit Blanchon)

### 3. Board Ayarları
```
Board: "ESP32 Dev Module"
Upload Speed: "921600"
CPU Frequency: "240MHz (WiFi/BT)"
Flash Mode: "QIO"
Flash Size: "4MB (32Mb)"
Port: [bilgisayarınıza bağlı port]
```

### 4. Kodu Yükleyin
- `esp32/water_pump_controller.ino` dosyasını Arduino IDE'de açın
- WiFi bilgilerinizi kontrol edin:
  ```cpp
  const char* ssid = "Zyxel_3691";               
  const char* password = "3883D488Y7";         
  const char* mqtt_server = "192.168.1.7";  // Raspberry Pi IP
  ```
- ESP32'ye yükleyin

## Adım 4: Web Dashboard Başlatma

### 1. Python Web Server'ı Çalıştırın
```bash
cd raspberry-pi
python3 web_server.py
```

### 2. Dashboard'a Erişim
- **Yerel erişim:** http://localhost:5000
- **Ağ erişimi:** http://192.168.1.7:5000
- **Mobil erişim:** Raspberry Pi IP'si ile

## Adım 5: İlk Test

### 1. Sistem Kontrolü
```bash
# MQTT broker çalışıyor mu?
sudo systemctl status mosquitto

# ESP32 bağlantısını kontrol et
mosquitto_sub -h localhost -t "system/status"
```

### 2. Manuel MQTT Testi
```bash
# Su pompasını aç
mosquitto_pub -h localhost -t "water/pump" -m "ON"

# Su pompasını kapat  
mosquitto_pub -h localhost -t "water/pump" -m "OFF"

# Sensör verilerini dinle
mosquitto_sub -h localhost -t "sensors/data"
```

### 3. Web Dashboard Testi
1. Dashboard'a git: http://192.168.1.7:5000
2. ESP32 bağlantı durumunu kontrol et
3. "POMPAYI AÇ" butonuna tıkla
4. "5 SANİYE TEST" butonunu dene
5. Nem sensörü verilerini gözlemle

## Troubleshooting (Sorun Giderme)

### ESP32 Bağlantı Sorunları
```bash
# WiFi bağlantısı kontrol
# Serial Monitor'de çıktıları inceleyin
# RSSI değerini kontrol edin (zayıf sinyal)
```

### MQTT Bağlantı Sorunları
```bash
# Port kontrolü
sudo netstat -tulpn | grep :1883

# Log kontrolü
sudo tail -f /var/log/mosquitto/mosquitto.log

# Manual test
mosquitto_pub -h 192.168.1.7 -t test -m "hello"
```

### Web Dashboard Sorunları
```bash
# Python hataları
python3 web_server.py

# Port kontrolü
sudo netstat -tulpn | grep :5000

# Firewall ayarları
sudo ufw allow 5000
```

## Güvenlik Notları

### MQTT Güvenliği
- Üretim ortamında kullanıcı adı/şifre ekleyin
- SSL/TLS kullanın
- ACL (Access Control List) yapılandırın

### Network Güvenliği
- Guest network kullanın
- Firewall kuralları ekleyin
- VPN üzerinden erişim

## Sonraki Adımlar

1. **Otomatik Sulama:** Nem seviyesine göre otomatik pompa kontrolü
2. **Veri Kayıt:** InfluxDB + Grafana entegrasyonu
3. **Mobil Uygulama:** React Native / Flutter app
4. **IoT Platform:** AWS IoT / Google Cloud IoT entegrasyonu
5. **Çoklu Sensör:** Sıcaklık, pH, ışık sensörleri ekleme

## Destek

Sorunlarla karşılaştığınızda:
1. Serial Monitor çıktılarını kontrol edin
2. MQTT log'larını inceleyin
3. Network bağlantısını test edin
4. Hardware bağlantılarını kontrol edin 