#!/usr/bin/env python3
"""
MQTT Test Scripti
Pi'de çalıştır: python3 test_mqtt.py
"""

import paho.mqtt.client as mqtt
import time
import json

def on_connect(client, userdata, flags, rc):
    print(f"🔗 MQTT Broker bağlantı durumu: {rc}")
    if rc == 0:
        print("✅ MQTT Broker çalışıyor!")
        # Test topic'lerine abone ol
        client.subscribe("led1/status")
        client.subscribe("led2/status") 
        client.subscribe("system/status")
        client.subscribe("led1/control")
        client.subscribe("led2/control")
        print("📡 Test topic'lerine abone olundu")
    else:
        print("❌ MQTT Broker bağlantı hatası!")

def on_message(client, userdata, msg):
    topic = msg.topic
    message = msg.payload.decode('utf-8')
    print(f"📨 MQTT Mesaj: [{topic}] -> {message}")

def main():
    print("🚀 MQTT Test Başlatılıyor...")
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # Localhost MQTT broker'a bağlan
        client.connect('localhost', 1883, 60)
        print("⏳ MQTT dinleniyor... (10 saniye)")
        
        # Test mesajları gönder
        client.loop_start()
        
        print("\n💡 Test mesajları gönderiliyor...")
        client.publish("led1/control", "ON")
        time.sleep(1)
        client.publish("led1/control", "OFF") 
        time.sleep(1)
        client.publish("led2/control", "ON")
        time.sleep(1)
        client.publish("led2/control", "OFF")
        
        # 5 saniye daha dinle
        time.sleep(5)
        
        client.loop_stop()
        client.disconnect()
        print("\n✅ MQTT test tamamlandı.")
        
    except Exception as e:
        print(f"❌ MQTT Test hatası: {e}")

if __name__ == "__main__":
    main() 