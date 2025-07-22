# Akıllı Sulama Sistemi (ESP32 + AWS EC2)

## Proje Açıklaması
Bu proje ESP32 mikrocontroller ve AWS EC2 sunucusu kullanarak bulut tabanlı akıllı bir sulama sistemi oluşturur. 
- **ESP32**: Sensörler ve su pompasını kontrol eder, WiFi üzerinden AWS'ye bağlanır
- **AWS EC2**: MQTT broker (Mosquitto) ve web dashboard sunucusu olarak çalışır
- **MQTT**: ESP32 ve AWS EC2 arasında haberleşme protokolü
- **Web Dashboard**: ESP32'yi uzaktan kontrol etmek için browser tabanlı arayüz

## Proje Yapısı
```
ESP/
├── esp32/              # ESP32 Arduino kodu
├── raspberry-pi/       # AWS EC2 Python servisleri (eski isim korundu)
├── web-dashboard/      # Web arayüzü (HTML/CSS/JS)
└── docs/              # Dokümantasyon
```

## Sistem Bileşenleri

### Hardware
- ESP32 DevKit
- Su pompası (5V/12V) 
- 3x Nem sensörü (analog soil moisture sensor)
- Röle modülü
- 2x Kontrol LED'i + 1x Durum LED'i

### Cloud Infrastructure
- **AWS EC2 Instance** (Ubuntu 20.04+)
  - IP: `56.228.30.48`
  - MQTT Broker (Mosquitto) - Port 1883
  - Web Dashboard - Port 5000
  - Systemd otomatik servis yönetimi

## 🚀 Hızlı Başlangıç

### 1. ESP32 Programlama
```cpp
// esp32/water_pump_controller.ino dosyasında:
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";  
const char* mqtt_server = "56.228.30.48";  // AWS EC2 IP
```

### 2. AWS EC2 Servisleri
```bash
# MQTT Broker otomatik çalışıyor
sudo systemctl status mosquitto

# Web Dashboard otomatik çalışıyor  
sudo systemctl status esp32-web.service
```

### 3. Web Dashboard Erişimi
```
🌐 http://56.228.30.48:5000
```

### 4. Sistem Testi
- ESP32'yi güçlendir
- Web dashboard'da bağlantı durumunu kontrol et
- LED/Pompa kontrollerini test et
- Nem sensörü verilerini gözlemle

## 📡 MQTT Topic'ler
- `led1/control` - LED 1 kontrolü (ON/OFF)
- `led1/status` - LED 1 durum geri bildirimi
- `led2/control` - LED 2 kontrolü (ON/OFF)
- `led2/status` - LED 2 durum geri bildirimi
- `pump/control` - Su pompası kontrolü (ON/OFF)
- `pump/status` - Su pompası durum geri bildirimi
- `sensors/data` - 3x Nem sensörü verileri (JSON format)
- `system/status` - ESP32 sistem durumu
- `system/command` - Sistem komutları (status, restart, all_on, all_off)

## 🔧 Teknik Detaylar

### ESP32 Pin Konfigürasyonu
```
GPIO2  -> Durum LED (Built-in blue LED)
GPIO4  -> Kontrol LED 1
GPIO5  -> Kontrol LED 2  
GPIO14 -> Su pompası röle kontrolü
GPIO32 -> Nem sensörü 1
GPIO33 -> Nem sensörü 2
GPIO34 -> Nem sensörü 3
```

### AWS EC2 Sistemd Servisleri
```bash
# MQTT Broker
sudo systemctl {start|stop|status} mosquitto

# Web Dashboard  
sudo systemctl {start|stop|status} esp32-web.service

# Servis logları
sudo journalctl -u esp32-web.service -f
```

### Security Group Ayarları
```
Port 22   (SSH)  - Yönetim erişimi
Port 1883 (MQTT) - ESP32 bağlantısı  
Port 5000 (HTTP) - Web dashboard erişimi
```

## 📊 Özellikler
- ✅ 3x Nem sensörü simultane okuma
- ✅ 2x LED + 1x Su pompası kontrolü
- ✅ Gerçek zamanlı web dashboard
- ✅ MQTT ile düşük gecikme haberleşme
- ✅ ESP32 otomatik yeniden bağlanma
- ✅ AWS EC2 otomatik servis başlatma
- ✅ SQLite database veri kayıt
- ✅ Mobil uyumlu responsive tasarım

## 📚 Dokümantasyon
- `docs/hizli_baslangic.md` - 15 dakikada kurulum
- `docs/kurulum_rehberi.md` - Detaylı kurulum adımları
- `docs/test_rehberi.md` - Sistem test prosedürleri

## 🌟 Demo
**Web Dashboard:** http://56.228.30.48:5000

**Test MQTT Komutları:**
```bash
# LED kontrolü
mosquitto_pub -h 56.228.30.48 -t "led1/control" -m "ON"
mosquitto_pub -h 56.228.30.48 -t "pump/control" -m "ON"

# Sensör verilerini dinle
mosquitto_sub -h 56.228.30.48 -t "sensors/data"
``` 