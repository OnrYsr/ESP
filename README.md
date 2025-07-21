# Akıllı Sulama Sistemi (ESP32 + Raspberry Pi)

## Proje Açıklaması
Bu proje ESP32 mikrocontroller ve Raspberry Pi kullanarak akıllı bir sulama sistemi oluşturur. 
- **ESP32**: Sensörler ve su pompasını kontrol eder
- **Raspberry Pi**: MQTT hub olarak çalışır ve web dashboard sunar
- **MQTT**: ESP32 ve Raspberry Pi arasında haberleşme protokolü

## Proje Yapısı
```
ESP/
├── esp32/              # ESP32 Arduino kodu
├── raspberry-pi/       # Raspberry Pi Python servisleri
├── web-dashboard/      # Web arayüzü (HTML/CSS/JS)
└── docs/              # Dokümantasyon
```

## Sistem Bileşenleri
- ESP32 DevKit
- Su pompası (5V/12V)
- Nem sensörü (analog/digital)
- Röle modülü
- Raspberry Pi (MQTT broker + web server)

## Kurulum
1. ESP32 kodunu yükle
2. Raspberry Pi'de MQTT broker kur
3. Web dashboard'u çalıştır-
4. Sistem testini yap

## MQTT Topic'ler
- `water/pump` - Su pompası kontrolü (ON/OFF)
- `water/pump/status` - Su pompası durum geri bildirimi
- `led/control` - LED kontrolü (ON/OFF)
- `led/status` - LED durum geri bildirimi
- `sensors/data` - Sensör verileri (JSON format)
- `system/status` - Sistem durumu
- `system/command` - Sistem komutları (status, restart) 