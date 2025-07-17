#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 Dual LED Kontrol Sistemi - Web Server
Raspberry Pi MQTT Hub ve Web Dashboard
"""

import time
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt

# Flask app
app = Flask(__name__)
CORS(app)

# Global değişkenler
system_data = {
    'led1_state': False,
    'led2_state': False,
    'last_update': None,
    'esp32_connected': False,
    'status_history': []
}

# MQTT ayarları
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPICS = {
    'led1_control': 'led1/control',
    'led1_status': 'led1/status',
    'led2_control': 'led2/control',
    'led2_status': 'led2/status',
    'system_status': 'system/status',
    'system_command': 'system/command'
}

# MQTT Client
mqtt_client = mqtt.Client()

def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT bağlantı callback"""
    if rc == 0:
        print("✅ MQTT Broker'a bağlandı!")
        # Tüm topic'lere abone ol
        for topic in MQTT_TOPICS.values():
            client.subscribe(topic)
            print(f"📡 Abone olundu: {topic}")
    else:
        print(f"❌ MQTT bağlantı hatası: {rc}")

def on_mqtt_message(client, userdata, msg):
    """MQTT mesaj callback"""
    topic = msg.topic
    message = msg.payload.decode('utf-8')
    
    print(f"📨 MQTT Mesajı [{topic}]: {message}")
    
    try:
        if topic == MQTT_TOPICS['led1_status']:
            old_state = system_data['led1_state']
            system_data['led1_state'] = (message == 'ON')
            system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
            print(f"🔴 LED1 durumu: {old_state} → {system_data['led1_state']}")
            
        elif topic == MQTT_TOPICS['led2_status']:
            old_state = system_data['led2_state']
            system_data['led2_state'] = (message == 'ON')
            system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
            print(f"🔵 LED2 durumu: {old_state} → {system_data['led2_state']}")
            
        elif topic == MQTT_TOPICS['system_status']:
            if "ESP32" in message:
                system_data['esp32_connected'] = True
                system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
                print(f"🔗 ESP32 bağlandı: {message}")
                
                # Durum geçmişi kaydet (son 50 kayıt)
                history_entry = {
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'led1': system_data['led1_state'],
                    'led2': system_data['led2_state']
                }
                system_data['status_history'].append(history_entry)
                if len(system_data['status_history']) > 50:
                    system_data['status_history'].pop(0)
    
    except Exception as e:
        print(f"❌ MQTT mesaj işleme hatası: {e}")

# MQTT setup
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

def start_mqtt():
    """MQTT bağlantısını başlat"""
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"MQTT bağlantı hatası: {e}")

# Web routes
@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Sistem durumu API"""
    print(f"📊 Durum isteği: {system_data}")
    return jsonify(system_data)

@app.route('/api/led1/<action>')
def api_led1_control(action):
    """LED 1 kontrolü API"""
    try:
        print(f"🎛️ LED1 kontrol isteği: {action}")
        if action.lower() == 'on':
            mqtt_client.publish(MQTT_TOPICS['led1_control'], 'ON')
            print(f"📤 MQTT gönderildi: {MQTT_TOPICS['led1_control']} -> ON")
            return jsonify({'status': 'success', 'message': 'LED 1 açıldı'})
        elif action.lower() == 'off':
            mqtt_client.publish(MQTT_TOPICS['led1_control'], 'OFF')
            print(f"📤 MQTT gönderildi: {MQTT_TOPICS['led1_control']} -> OFF")
            return jsonify({'status': 'success', 'message': 'LED 1 kapatıldı'})
        else:
            return jsonify({'status': 'error', 'message': 'Geçersiz komut'})
    except Exception as e:
        print(f"❌ LED1 kontrol hatası: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/led2/<action>')
def api_led2_control(action):
    """LED 2 kontrolü API"""
    try:
        print(f"🎛️ LED2 kontrol isteği: {action}")
        if action.lower() == 'on':
            mqtt_client.publish(MQTT_TOPICS['led2_control'], 'ON')
            print(f"📤 MQTT gönderildi: {MQTT_TOPICS['led2_control']} -> ON")
            return jsonify({'status': 'success', 'message': 'LED 2 açıldı'})
        elif action.lower() == 'off':
            mqtt_client.publish(MQTT_TOPICS['led2_control'], 'OFF')
            print(f"📤 MQTT gönderildi: {MQTT_TOPICS['led2_control']} -> OFF")
            return jsonify({'status': 'success', 'message': 'LED 2 kapatıldı'})
        else:
            return jsonify({'status': 'error', 'message': 'Geçersiz komut'})
    except Exception as e:
        print(f"❌ LED2 kontrol hatası: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/all/<action>')
def api_all_leds_control(action):
    """Tüm LED'leri kontrol et API"""
    try:
        if action.lower() == 'on':
            mqtt_client.publish(MQTT_TOPICS['system_command'], 'all_on')
            return jsonify({'status': 'success', 'message': 'Tüm LED\'ler açıldı'})
        elif action.lower() == 'off':
            mqtt_client.publish(MQTT_TOPICS['system_command'], 'all_off')
            return jsonify({'status': 'success', 'message': 'Tüm LED\'ler kapatıldı'})
        else:
            return jsonify({'status': 'error', 'message': 'Geçersiz komut'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/restart')
def api_restart():
    """ESP32 yeniden başlatma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['system_command'], 'restart')
        return jsonify({'status': 'success', 'message': 'ESP32 yeniden başlatılıyor'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/history')
def api_history():
    """Durum geçmişi API"""
    return jsonify(system_data['status_history'])

def status_monitor():
    """ESP32 bağlantı durumu izleme"""
    while True:
        time.sleep(30)  # 30 saniyede bir kontrol
        now = datetime.now()
        if system_data['last_update']:
            last_update = datetime.strptime(system_data['last_update'], '%H:%M:%S').replace(
                year=now.year, month=now.month, day=now.day)
            
            # 60 saniyeden fazla güncelleme yoksa bağlantı kopmuş kabul et
            if (now - last_update).total_seconds() > 60:
                system_data['esp32_connected'] = False

if __name__ == '__main__':
    print("ESP32 Dual LED Kontrol Sistemi Web Server")
    print("========================================")
    
    # MQTT bağlantısını başlat
    start_mqtt()
    
    # Durum izleme thread'ini başlat
    monitor_thread = threading.Thread(target=status_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    print("Web server başlatılıyor...")
    print("Dashboard: http://192.168.1.7:5000")
    
    # Flask uygulamasını başlat
    app.run(host='0.0.0.0', port=5000, debug=False) 