#!/bin/bash

echo "===== ESP32 Su Pompası Sistemi - Raspberry Pi Kurulumu ====="
echo "MQTT Broker (Mosquitto) ve Python servisleri kuruluyor..."

# Sistem güncelleme
echo "Sistem güncelleniyor..."
sudo apt update && sudo apt upgrade -y

# Mosquitto MQTT Broker kurulumu
echo "Mosquitto MQTT Broker kuruluyor..."
sudo apt install mosquitto mosquitto-clients -y

# Python gereksinimler
echo "Python kütüphaneleri kuruluyor..."
sudo apt install python3 python3-pip -y
pip3 install paho-mqtt flask flask-cors

# Mosquitto konfigürasyonu
echo "Mosquitto konfigürasyonu ayarlanıyor..."
sudo cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.backup

# Basit konfigürasyon dosyası oluştur
sudo tee /etc/mosquitto/mosquitto.conf > /dev/null <<EOF
# Mosquitto MQTT Broker Konfigürasyonu
# ESP32 Su Pompası Sistemi için

listener 1883
allow_anonymous true
log_dest file /var/log/mosquitto/mosquitto.log
log_dest stdout
log_type error
log_type warning
log_type notice
log_type information
connection_messages true
log_timestamp true
EOF

# Mosquitto servisini başlat ve otomatik başlatmaya ekle
echo "Mosquitto servisi başlatılıyor..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Servis durumunu kontrol et
echo "Servis durumu:"
sudo systemctl status mosquitto --no-pager

# Test bağlantısı
echo "Test bağlantısı yapılıyor..."
mosquitto_pub -h localhost -t test/message -m "Mosquitto kurulumu başarılı!"

# Port kontrolü
echo "Port 1883 dinleniyor mu kontrol ediliyor..."
sudo netstat -tulpn | grep :1883

echo "===== Kurulum Tamamlandı ====="
echo "Raspberry Pi IP adresi:"
hostname -I

echo ""
echo "Test için:"
echo "1. MQTT Subscribe: mosquitto_sub -h localhost -t 'water/#'"
echo "2. MQTT Publish: mosquitto_pub -h localhost -t 'water/pump' -m 'ON'"
echo ""
echo "Web dashboard için python3 web_server.py komutunu çalıştırın" 