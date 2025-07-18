#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 Dual LED Kontrol Sistemi - Web Server
Raspberry Pi MQTT Hub ve Web Dashboard
"""

import json
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
    'system_info': {}
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
        if topic == MQTT_TOPICS['led1_status']:
            system_data['led1_state'] = (message == 'ON')
            system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
            
        elif topic == MQTT_TOPICS['led2_status']:
            system_data['led2_state'] = (message == 'ON')
            system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
                
        elif topic == MQTT_TOPICS['system_status']:
            if "ESP32" in message or "Connected" in message:
                system_data['esp32_connected'] = True
                system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
                
            # JSON formatında sistem bilgisi ise
            try:
                data = json.loads(message)
                system_data['system_info'] = data
                system_data['led1_state'] = data.get('led1_state', False)
                system_data['led2_state'] = data.get('led2_state', False)
                system_data['esp32_connected'] = True
                system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
            except json.JSONDecodeError:
                pass
                
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

@app.route('/api/led1/on', methods=['GET', 'POST'])
def led1_on():
    """LED1 açma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['led1_control'], 'ON')
        return jsonify({
            'success': True,
            'message': 'LED1 açma komutu gönderildi'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/led1/off', methods=['GET', 'POST'])
def led1_off():
    """LED1 kapatma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['led1_control'], 'OFF')
        return jsonify({
            'success': True,
            'message': 'LED1 kapatma komutu gönderildi'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/led2/on', methods=['GET', 'POST'])
def led2_on():
    """LED2 açma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['led2_control'], 'ON')
        return jsonify({
            'success': True,
            'message': 'LED2 açma komutu gönderildi'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/led2/off', methods=['GET', 'POST'])
def led2_off():
    """LED2 kapatma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['led2_control'], 'OFF')
        return jsonify({
            'success': True,
            'message': 'LED2 kapatma komutu gönderildi'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/all/on', methods=['GET', 'POST'])
def all_leds_on():
    """Tüm LED'leri açma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['system_command'], 'all_on')
        return jsonify({
            'success': True,
            'message': 'Tüm LED açma komutu gönderildi'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/all/off', methods=['GET', 'POST'])
def all_leds_off():
    """Tüm LED'leri kapatma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['system_command'], 'all_off')
        return jsonify({
            'success': True,
            'message': 'Tüm LED kapatma komutu gönderildi'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/restart', methods=['GET', 'POST'])
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

@app.route('/api/test/led1')
def test_led1():
    """Test için LED1'i 3 saniye yanıp söndür"""
    try:
        def led_test():
            mqtt_client.publish(MQTT_TOPICS['led1_control'], 'ON')
            time.sleep(1)
            mqtt_client.publish(MQTT_TOPICS['led1_control'], 'OFF')
            time.sleep(0.5)
            mqtt_client.publish(MQTT_TOPICS['led1_control'], 'ON')
            time.sleep(1)
            mqtt_client.publish(MQTT_TOPICS['led1_control'], 'OFF')
        
        threading.Thread(target=led_test).start()
        
        return jsonify({
            'success': True,
            'message': 'LED1 test başlatıldı'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Test hatası: {str(e)}'
        }), 500

@app.route('/api/test/led2')
def test_led2():
    """Test için LED2'yi 3 saniye yanıp söndür"""
    try:
        def led_test():
            mqtt_client.publish(MQTT_TOPICS['led2_control'], 'ON')
            time.sleep(1)
            mqtt_client.publish(MQTT_TOPICS['led2_control'], 'OFF')
            time.sleep(0.5)
            mqtt_client.publish(MQTT_TOPICS['led2_control'], 'ON')
            time.sleep(1)
            mqtt_client.publish(MQTT_TOPICS['led2_control'], 'OFF')
        
        threading.Thread(target=led_test).start()
        
        return jsonify({
            'success': True,
            'message': 'LED2 test başlatıldı'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Test hatası: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("ESP32 Dual LED Kontrol Sistemi Web Server Başlatılıyor...")
    print("=" * 50)
    
    # MQTT'yi başlat
    setup_mqtt()
    
    # Flask web server'ı başlat
    print("Web server başlatılıyor: http://0.0.0.0:5000")
    print("Dashboard: http://192.168.1.7:5000")  # Raspberry Pi IP
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) 