#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 Su Pompası Sistemi - Web Server (ArduinoJson olmadan)
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
    'pump_state': False,
    'led_state': False,
    'moisture_level': 0,
    'moisture_percent': 0,
    'last_update': None,
    'esp32_connected': False,
    'sensor_history': []
}

# MQTT ayarları
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPICS = {
    'pump_control': 'water/pump',
    'pump_status': 'water/pump/status',
    'led_control': 'led/control',
    'led_status': 'led/status',
    'sensor_data': 'sensors/data',
    'system_status': 'system/status',
    'system_command': 'system/command'
}

# MQTT Client
mqtt_client = mqtt.Client()

def parse_simple_data(data_string):
    """Basit veri formatını parse et: 'key1:value1,key2:value2'"""
    result = {}
    try:
        pairs = data_string.split(',')
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                # Boolean değerleri çevir
                if value.lower() == 'true':
                    result[key] = True
                elif value.lower() == 'false':
                    result[key] = False
                else:
                    # Sayı olup olmadığını kontrol et
                    try:
                        result[key] = int(value)
                    except ValueError:
                        result[key] = value
    except Exception as e:
        print(f"Veri parse hatası: {e}")
    return result

def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT bağlantı callback"""
    if rc == 0:
        print("MQTT Broker'a bağlandı!")
        # Tüm topic'lere abone ol
        for topic in MQTT_TOPICS.values():
            client.subscribe(topic)
            print(f"Abone olundu: {topic}")
    else:
        print(f"MQTT bağlantı hatası: {rc}")

def on_mqtt_message(client, userdata, msg):
    """MQTT mesaj callback"""
    topic = msg.topic
    message = msg.payload.decode('utf-8')
    
    print(f"MQTT Mesajı [{topic}]: {message}")
    
    try:
        if topic == MQTT_TOPICS['pump_status']:
            system_data['pump_state'] = (message == 'ON')
            system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
            
        elif topic == MQTT_TOPICS['led_status']:
            system_data['led_state'] = (message == 'ON')
            system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
            
        elif topic == MQTT_TOPICS['sensor_data']:
            # Basit format parse et: "moisture:1234,moisture_percent:30,pump_state:true"
            data = parse_simple_data(message)
            if data:
                system_data['moisture_level'] = data.get('moisture', 0)
                system_data['moisture_percent'] = data.get('moisture_percent', 0)
                system_data['pump_state'] = data.get('pump_state', False)
                system_data['led_state'] = data.get('led_state', False)
                system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
                
                # Sensör geçmişi kaydet (son 50 kayıt)
                history_entry = {
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'moisture': system_data['moisture_percent'],
                    'pump': system_data['pump_state'],
                    'led': system_data['led_state']
                }
                system_data['sensor_history'].append(history_entry)
                if len(system_data['sensor_history']) > 50:
                    system_data['sensor_history'].pop(0)
                
        elif topic == MQTT_TOPICS['system_status']:
            if "ESP32" in message:
                system_data['esp32_connected'] = True
                system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
                
    except Exception as e:
        print(f"Mesaj işleme hatası: {e}")

def setup_mqtt():
    """MQTT client'ı yapılandır"""
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("MQTT thread başlatıldı")
    except Exception as e:
        print(f"MQTT bağlantı hatası: {e}")

# Web Routes
@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Sistem durumu API"""
    return jsonify(system_data)

@app.route('/api/pump', methods=['POST'])
def control_pump():
    """Su pompası kontrolü API"""
    try:
        data = request.get_json()
        state = data.get('state', False)
        
        # MQTT ile ESP32'ye komut gönder
        command = "ON" if state else "OFF"
        mqtt_client.publish(MQTT_TOPICS['pump_control'], command)
        
        return jsonify({
            'success': True,
            'message': f'Pompa komutu gönderildi: {command}',
            'state': state
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/led', methods=['POST'])
def control_led():
    """LED kontrolü API"""
    try:
        data = request.get_json()
        state = data.get('state', False)
        
        # MQTT ile ESP32'ye komut gönder
        command = "ON" if state else "OFF"
        mqtt_client.publish(MQTT_TOPICS['led_control'], command)
        
        return jsonify({
            'success': True,
            'message': f'LED komutu gönderildi: {command}',
            'state': state
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/system/restart', methods=['POST'])
def restart_esp32():
    """ESP32'yi yeniden başlat"""
    try:
        mqtt_client.publish(MQTT_TOPICS['system_command'], 'restart')
        return jsonify({
            'success': True,
            'message': 'ESP32 yeniden başlatma komutu gönderildi'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/history')
def get_history():
    """Sensör geçmişi API"""
    return jsonify(system_data['sensor_history'])

@app.route('/api/test/pump')
def test_pump():
    """Test için pompayı 5 saniye çalıştır"""
    try:
        # Pompayı aç
        mqtt_client.publish(MQTT_TOPICS['pump_control'], 'ON')
        
        # 5 saniye bekle (arka planda)
        def delayed_stop():
            time.sleep(5)
            mqtt_client.publish(MQTT_TOPICS['pump_control'], 'OFF')
        
        threading.Thread(target=delayed_stop).start()
        
        return jsonify({
            'success': True,
            'message': 'Test başlatıldı - pompa 5 saniye çalışacak'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Test hatası: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("ESP32 Su Pompası Sistemi Web Server Başlatılıyor... (Basit Versiyon)")
    print("=" * 50)
    
    # MQTT'yi başlat
    setup_mqtt()
    
    # Flask web server'ı başlat
    print("Web server başlatılıyor: http://0.0.0.0:5000")
    print("Dashboard: http://192.168.1.7:5000")  # Raspberry Pi IP
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) 