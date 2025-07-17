# ESP32 Su Pompası Sistemi - Test Rehberi

## Test Aşaması 1: Temel Su Pompası Kontrolü

### Ön Hazırlık
1. ✅ ESP32 kodunu yükle (`esp32/water_pump_controller.ino`)
2. ✅ Raspberry Pi'de MQTT broker kurulumunu tamamla
3. ✅ Web dashboard'u başlat (`python3 web_server.py`)
4. ✅ Hardware bağlantılarını kontrol et

### Test Senaryoları

#### Test 1: MQTT Bağlantı Kontrolü
```bash
# Terminal 1: MQTT mesajlarını dinle
mosquitto_sub -h localhost -t '#' -v

# Terminal 2: Test mesajı gönder
mosquitto_pub -h localhost -t test/message -m "Test mesajı"
```

**Beklenen Sonuç:** Terminal 1'de mesajın göründüğünü doğrula

#### Test 2: ESP32 Bağlantı Durumu
1. ESP32'yi güçlendir
2. Serial Monitor'ü aç (115200 baud)
3. ESP32'nin WiFi'ye bağlandığını kontrol et
4. MQTT broker'a bağlantıyı doğrula

**Beklenen Serial Monitor Çıktısı:**
```
ESP32 Su Pompası Kontrolcüsü Başlatılıyor...
WiFi'ye bağlanıyor........
WiFi bağlandı! IP: 192.168.1.XXX
MQTT'ye bağlanıyor...bağlandı!
Sistem hazır!
```

#### Test 3: Web Dashboard Erişimi
1. **Yerel Raspberry Pi'den:** http://localhost:5000
2. **Network'ten:** http://192.168.1.7:5000
3. Dashboard'da ESP32 bağlantı durumunu kontrol et

**Beklenen Sonuç:** 
- ESP32 durumu: 🟢 BAĞLI
- Son güncelleme zamanı güncelleniyor
- Nem sensörü verisi geliyor

#### Test 4: Manuel Su Pompası Kontrolü

**MQTT ile Test:**
```bash
# Pompayı aç
mosquitto_pub -h localhost -t "water/pump" -m "ON"

# 5 saniye bekle, sonra kapat
mosquitto_pub -h localhost -t "water/pump" -m "OFF"
```

**Web Dashboard ile Test:**
1. "POMPAYI AÇ" butonuna tıkla
2. Röle'nin çalıştığını duy/gör
3. ESP32'de LED'in yandığını kontrol et
4. "POMPAYI KAPAT" butonuna tıkla

**Beklenen Sonuçlar:**
- Röle modülü "tık" sesi çıkarır
- ESP32'de GPIO13 LED'i yanar/söner (sistem durumu)
- Web dashboard'da pompa durumu güncellenir
- Serial Monitor'de "Su pompası: ON/OFF" mesajı görünür

#### Test 5: Nem Sensörü Okuma
1. Nem sensörünü kuru topraklara sok
2. Web dashboard'da nem seviyesini gözlemle
3. Sensörü ıslak topraklara sok
4. Değişimin web'de göründüğünü kontrol et

**Beklenen Sonuçlar:**
- Kuru toprak: 0-30% nem
- Normal toprak: 30-70% nem  
- Islak toprak: 70-100% nem
- Web dashboard'da çubuk grafik güncellenir

#### Test 6: LED Kontrolü
**MQTT ile Test:**
```bash
# LED'i aç
mosquitto_pub -h localhost -t "led/control" -m "ON"

# LED'i kapat
mosquitto_pub -h localhost -t "led/control" -m "OFF"
```

**Web Dashboard ile Test:**
1. "LED'İ AÇ" butonuna tıkla
2. GPIO4'teki LED'in yandığını kontrol et
3. "LED'İ KAPAT" butonuna tıkla
4. LED'in söndüğünü kontrol et

**Beklenen Sonuçlar:**
- GPIO4'teki LED yanar/söner
- Web dashboard'da LED durumu güncellenir  
- Serial Monitor'de "Kontrol LED'i: ON/OFF" mesajı görünür

#### Test 7: Otomatik Test Fonksiyonu
1. Web dashboard'da "5 SANİYE TEST" butonuna tıkla
2. Pompa otomatik olarak 5 saniye çalışır
3. Otomatik olarak kapanır

**Beklenen Sonuç:** 
- Pompa 5 saniye açık kalır
- Sonra otomatik kapanır
- Web'de log mesajı: "🧪 Test başlatıldı - pompa 5 saniye çalışacak"

### Başarı Kriterleri

**✅ Test Başarılı Sayılır Eğer:**
- [ ] ESP32 WiFi'ye bağlanıyor
- [ ] MQTT broker ile iletişim kuruyor
- [ ] Web dashboard ESP32'yi algılıyor
- [ ] Pompa manuel olarak açılıp kapanabiliyor
- [ ] LED manuel olarak açılıp kapanabiliyor
- [ ] Nem sensörü değerleri okuyor
- [ ] 5 saniye test çalışıyor
- [ ] Sistem 30 dakika kesintisiz çalışıyor

### Yaygın Sorunlar ve Çözümleri

#### ESP32 WiFi'ye Bağlanamıyor
```cpp
// WiFi ayarlarını kontrol et
const char* ssid = "Zyxel_3691";               
const char* password = "3883D488Y7";         
```
- WiFi adı/şifre doğru mu?
- WiFi sinyal gücü yeterli mi?
- 2.4GHz ağda mı? (5GHz desteklenmez)

#### MQTT Bağlantısı Başarısız
```bash
# Mosquitto çalışıyor mu?
sudo systemctl status mosquitto

# Port dinleniyor mu?
sudo netstat -tulpn | grep :1883
```

#### Pompa Çalışmıyor
- Röle modülü doğru bağlı mı?
- Güç kaynağı bağlı mı?
- GPIO2 doğru pin mi?
- Röle voltajı (5V) doğru mu?

#### Web Dashboard Açılmıyor
```bash
# Python server çalışıyor mu?
python3 web_server.py

# Port dinleniyor mu?
sudo netstat -tulpn | grep :5000

# IP adresi doğru mu?
hostname -I
```

### Test Raporu Şablonu

```markdown
# Test Raporu - [Tarih]

## Test Özeti
- Başlangıç Saati: 
- Bitiş Saati:
- Test Durumu: ✅ Başarılı / ❌ Başarısız

## Test Sonuçları
- [x] ESP32 WiFi Bağlantısı
- [x] MQTT İletişimi  
- [x] Web Dashboard Erişimi
- [x] Pompa Kontrolü
- [x] Nem Sensörü
- [x] Otomatik Test

## Gözlemler
- ESP32 IP Adresi: 192.168.1.XXX
- Sinyal Gücü: -XX dBm
- Pompa Tepki Süresi: X saniye
- Nem Sensörü Aralığı: XXX-XXXX

## Sorunlar
1. [Varsa sorunları listele]

## Sonraki Adımlar
1. Otomatik sulama algoritması ekle
2. Veri logging sistemi kur
3. Mobil erişim sağla
```

### Test Sonrası Doğrulama

**24 Saat Test:**
- Sistemi 24 saat boyunca çalışır durumda bırak
- Her 1 saatte bir web dashboard'u kontrol et
- MQTT bağlantısının kesilip kesilmediğini gözlemle
- ESP32'nin yeniden başlayıp başlamadığını kontrol et

**Ağ Kesintisi Testi:**
- WiFi'yi 5 dakika kapat
- ESP32'nin otomatik yeniden bağlanmasını gözlemle
- MQTT mesajlarının tekrar gelmeye başlamasını kontrol et

**Güç Kesintisi Testi:**
- ESP32'nin güç bağlantısını kes
- Tekrar güçlendir
- Sistem'in otomatik olarak çalışmaya başlamasını doğrula

Bu testlerin hepsi başarılı geçildikten sonra **Aşama 2: Otomatik Sulama**'ya geçilebilir. 