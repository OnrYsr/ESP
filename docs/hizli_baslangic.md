# 🚀 Hızlı Başlangıç Rehberi

## ESP32 Su Pompası Sistemi - 15 Dakikada Kurulum

### 📦 Gereksinimler
- ESP32 DevKit + USB kablo
- Raspberry Pi (WiFi ile internete bağlı)
- Su pompası + Röle modülü
- Nem sensörü
- Jumper kablolar

### ⚡ Hızlı Kurulum (15 dakika)

#### 1. Hardware Bağlantı (5 dakika)
```
ESP32 GPIO2  -> Röle IN
ESP32 GPIO4  -> Kontrol LED + (220Ω direnç ile)
ESP32 GPIO13 -> Durum LED + (220Ω direnç ile)
ESP32 A0     -> Nem sensörü OUT
ESP32 3.3V   -> Nem sensörü VCC
ESP32 GND    -> Ortak GND
```

#### 2. Raspberry Pi Kurulum (5 dakika)
```bash
# Tek komutta tüm kurulum
cd raspberry-pi
chmod +x install_mosquitto.sh
./install_mosquitto.sh
```

#### 3. ESP32 Programlama (3 dakika)
1. Arduino IDE'de `esp32/water_pump_controller.ino` aç
2. WiFi bilgilerini düzenle:
   ```cpp
   const char* ssid = "YOUR_WIFI_NAME";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* mqtt_server = "RASPBERRY_PI_IP"; // örn: 192.168.1.7
   ```
3. ESP32'ye yükle

#### 4. Web Dashboard Başlat (2 dakita)
```bash
cd raspberry-pi
python3 web_server.py
```

### 🌐 Dashboard Erişimi
- **Local:** http://localhost:5000
- **Network:** http://192.168.1.7:5000
- **Mobile:** Raspberry Pi IP'si

### ✅ İlk Test (2 dakika)
1. 🌐 Web dashboard'a git
2. 🔌 ESP32 bağlantı durumunu kontrol et (🟢 yeşil nokta)
3. 🚰 "POMPAYI AÇ" butonuna tıkla
4. 💡 "LED'İ AÇ" butonuna tıkla (GPIO4'teki LED yanar)
5. 💧 Nem sensörü verilerini gözlemle
6. 🧪 "5 SANİYE TEST" butonunu dene

### 🎯 Başarı Göstergeleri
- ✅ ESP32 durumu: **BAĞLI**
- ✅ Pompa kontrolü çalışıyor
- ✅ LED kontrolü çalışıyor
- ✅ Nem sensörü veri gönderiyor
- ✅ Dashboard güncelleniyor

### 🚨 Sorun Giderme (1 dakika çözüm)

**ESP32 bağlanmıyor?**
```bash
# WiFi adı/şifre kontrol et
# Serial Monitor'ü aç (115200 baud)
```

**Web dashboard açılmıyor?**
```bash
# Raspberry Pi IP'sini kontrol et
hostname -I
```

**Pompa çalışmıyor?**
```bash
# Röle bağlantılarını kontrol et
# Güç kaynağını kontrol et
```

### 📱 MQTT Test Komutları
```bash
# Manuel pompa kontrolü
mosquitto_pub -h localhost -t "water/pump" -m "ON"
mosquitto_pub -h localhost -t "water/pump" -m "OFF"

# Manuel LED kontrolü
mosquitto_pub -h localhost -t "led/control" -m "ON"
mosquitto_pub -h localhost -t "led/control" -m "OFF"

# Sistem durumunu dinle
mosquitto_sub -h localhost -t "sensors/data"
```

### 🎊 Tebrikler!

Sisteminiz hazır! Artık yapabilecekleriniz:

1. **📱 Mobil Erişim:** Telefondan pompayı kontrol et
2. **🤖 Otomatik Sulama:** Nem seviyesine göre otomatik sulama
3. **📊 Veri Takibi:** Nem seviyesi grafiklerini izle
4. **🔄 Uzaktan Kontrol:** İnternetten erişim
5. **⚙️ Gelişmiş Özellikler:** Zamanlanmış sulama, SMS uyarı

### 📚 Sonraki Adımlar

- **Dokümantasyon:** `docs/kurulum_rehberi.md`
- **Test Rehberi:** `docs/test_rehberi.md`
- **Kod Detayları:** `esp32/` ve `raspberry-pi/` klasörleri

---

> 💡 **İpucu:** Sistem 7/24 çalışabilir. Güç kesintisinde otomatik olarak yeniden başlar!

**Destek için:** GitHub Issues | E-mail | WhatsApp 