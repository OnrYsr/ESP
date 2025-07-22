#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 Dual LED Kontrol Sistemi - Web Server
Raspberry Pi MQTT Hub ve Web Dashboard + SQLite Database + Authentication
"""

import json
import time
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import paho.mqtt.client as mqtt

# Database import
from database import (
    init_database, log_system_event, save_device_reading, 
    save_device_action, get_device_by_pin, get_recent_readings
)

# Flask app
app = Flask(__name__)
CORS(app)

# Flask-Login configuration
app.secret_key = 'esp32-iot-secure-key-2024!@#'  # Production'da environment variable kullanın
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmalısınız.'

# User Model (Simple in-memory user)
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# Hardcoded user (Production'da database'den alın)
users = {
    'admin': User('1', 'admin', 'esp32secure2024!'),  # Şifreyi değiştirin!
}

@login_manager.user_loader
def load_user(user_id):
    for username, user in users.items():
        if user.id == user_id:
            return user
    return None

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username].password == password:
            login_user(users[username])
            log_system_event(f"Kullanıcı giriş yaptı: {username}", "INFO", "auth")
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre!', 'error')
            log_system_event(f"Başarısız giriş denemesi: {username}", "WARNING", "auth")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    log_system_event(f"Kullanıcı çıkış yaptı: {username}", "INFO", "auth")
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('login'))

# Global değişkenler
system_data = {
    'led1_state': False,
    'led2_state': False,
    'pump_state': False,
    'moisture1_raw': 0,
    'moisture1_percent': 0,
    'moisture2_raw': 0,
    'moisture2_percent': 0,
    'moisture3_raw': 0,
    'moisture3_percent': 0,
    'last_update': None,
    'esp32_connected': False,
    'system_info': {},
    'sensor_history': []
}

# MQTT ayarları
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPICS = {
    'led1_control': 'led1/control',
    'led1_status': 'led1/status',
    'led2_control': 'led2/control', 
    'led2_status': 'led2/status',
    'pump_control': 'pump/control',
    'pump_status': 'pump/status',
    'sensors_data': 'sensors/data',
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
            
            # Database'e cihaz eylemini kaydet
            led1_device = get_device_by_pin(2)  # GPIO2
            if led1_device:
                save_device_action(led1_device['id'], 'status_update', message, 'mqtt')
            
        elif topic == MQTT_TOPICS['led2_status']:
            system_data['led2_state'] = (message == 'ON')
            system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
            
            # Database'e cihaz eylemini kaydet
            led2_device = get_device_by_pin(5)  # GPIO5
            if led2_device:
                save_device_action(led2_device['id'], 'status_update', message, 'mqtt')
            
        elif topic == MQTT_TOPICS['pump_status']:
            system_data['pump_state'] = (message == 'ON')
            system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
            
            # Database'e cihaz eylemini kaydet
            pump_device = get_device_by_pin(14)  # GPIO14
            if pump_device:
                save_device_action(pump_device['id'], 'status_update', message, 'mqtt')
            
        elif topic == MQTT_TOPICS['sensors_data']:
            # Sensör verilerini işle
            data = json.loads(message)
            system_data['moisture1_raw'] = data.get('sensor1', {}).get('raw', 0)
            system_data['moisture1_percent'] = data.get('sensor1', {}).get('percent', 0)
            system_data['moisture2_raw'] = data.get('sensor2', {}).get('raw', 0)
            system_data['moisture2_percent'] = data.get('sensor2', {}).get('percent', 0)
            system_data['moisture3_raw'] = data.get('sensor3', {}).get('raw', 0)
            system_data['moisture3_percent'] = data.get('sensor3', {}).get('percent', 0)
            system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
            
            # Database'e sensör okumalarını kaydet
            moisture1_device = get_device_by_pin(32)  # GPIO32
            moisture2_device = get_device_by_pin(33)  # GPIO33
            moisture3_device = get_device_by_pin(34)  # GPIO34
            
            if moisture1_device:
                save_device_reading(moisture1_device['id'], 
                                  system_data['moisture1_raw'], 
                                  system_data['moisture1_percent'], '%')
                                  
            if moisture2_device:
                save_device_reading(moisture2_device['id'], 
                                  system_data['moisture2_raw'], 
                                  system_data['moisture2_percent'], '%')
                                  
            if moisture3_device:
                save_device_reading(moisture3_device['id'], 
                                  system_data['moisture3_raw'], 
                                  system_data['moisture3_percent'], '%')
            
            # Sensör geçmişi kaydet (bellekte de tut)
            history_entry = {
                'time': datetime.now().strftime('%H:%M:%S'),
                'moisture1': system_data['moisture1_percent'],
                'moisture2': system_data['moisture2_percent'],
                'moisture3': system_data['moisture3_percent']
            }
            system_data['sensor_history'].append(history_entry)
            if len(system_data['sensor_history']) > 50:
                system_data['sensor_history'].pop(0)
                
        elif topic == MQTT_TOPICS['system_status']:
            if "ESP32" in message or "Connected" in message:
                system_data['esp32_connected'] = True
                system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
                log_system_event(f"ESP32 bağlantı durumu: {message}", "INFO", "mqtt")
                
            # JSON formatında sistem bilgisi ise
            try:
                data = json.loads(message)
                system_data['system_info'] = data
                system_data['led1_state'] = data.get('led1_state', False)
                system_data['led2_state'] = data.get('led2_state', False)
                system_data['pump_state'] = data.get('pump_state', False)
                system_data['moisture1_raw'] = data.get('moisture1_raw', 0)
                system_data['moisture1_percent'] = data.get('moisture1_percent', 0)
                system_data['moisture2_raw'] = data.get('moisture2_raw', 0)
                system_data['moisture2_percent'] = data.get('moisture2_percent', 0)
                system_data['moisture3_raw'] = data.get('moisture3_raw', 0)
                system_data['moisture3_percent'] = data.get('moisture3_percent', 0)
                system_data['esp32_connected'] = True
                system_data['last_update'] = datetime.now().strftime('%H:%M:%S')
                
                # Sistem durumu logla
                log_system_event(f"ESP32 sistem durumu güncellendi", "INFO", "mqtt")
                
            except json.JSONDecodeError:
                pass
                
    except Exception as e:
        print(f"Mesaj işleme hatası: {e}")
        log_system_event(f"MQTT mesaj işleme hatası: {e}", "ERROR", "mqtt")

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
@login_required
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/api/status')
@login_required
def get_status():
    """Sistem durumu API"""
    return jsonify(system_data)

@app.route('/api/led1/on', methods=['GET', 'POST'])
@login_required
def led1_on():
    """LED1 açma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['led1_control'], 'ON')
        
        # Database'e manuel eylem kaydet
        led1_device = get_device_by_pin(2)
        if led1_device:
            save_device_action(led1_device['id'], 'turn_on', 'ON', 'web_manual')
        
        log_system_event("LED1 manuel olarak açıldı", "INFO", "web_api")
        return jsonify({
            'success': True,
            'message': 'LED1 açma komutu gönderildi'
        })
    except Exception as e:
        log_system_event(f"LED1 açma hatası: {e}", "ERROR", "web_api")
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/led1/off', methods=['GET', 'POST'])
@login_required
def led1_off():
    """LED1 kapatma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['led1_control'], 'OFF')
        
        # Database'e manuel eylem kaydet
        led1_device = get_device_by_pin(2)
        if led1_device:
            save_device_action(led1_device['id'], 'turn_off', 'OFF', 'web_manual')
        
        log_system_event("LED1 manuel olarak kapatıldı", "INFO", "web_api")
        return jsonify({
            'success': True,
            'message': 'LED1 kapatma komutu gönderildi'
        })
    except Exception as e:
        log_system_event(f"LED1 kapatma hatası: {e}", "ERROR", "web_api")
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/led2/on', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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

@app.route('/api/pump/on', methods=['GET', 'POST'])
@login_required
def pump_on():
    """Su pompası açma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['pump_control'], 'ON')
        
        # Database'e manuel eylem kaydet
        pump_device = get_device_by_pin(14)
        if pump_device:
            save_device_action(pump_device['id'], 'turn_on', 'ON', 'web_manual')
        
        log_system_event("Su pompası manuel olarak açıldı", "INFO", "web_api")
        return jsonify({
            'success': True,
            'message': 'Su pompası açma komutu gönderildi'
        })
    except Exception as e:
        log_system_event(f"Su pompası açma hatası: {e}", "ERROR", "web_api")
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/pump/off', methods=['GET', 'POST'])
@login_required
def pump_off():
    """Su pompası kapatma API"""
    try:
        mqtt_client.publish(MQTT_TOPICS['pump_control'], 'OFF')
        return jsonify({
            'success': True,
            'message': 'Su pompası kapatma komutu gönderildi'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/restart', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
    print("ESP32 Dual LED + Pump + Database Kontrol Sistemi Web Server Başlatılıyor...")
    print("=" * 70)
    
    # Database'i başlat
    print("🗄️ SQLite Database başlatılıyor...")
    try:
        init_database()
        log_system_event("Web server başlatıldı", "INFO", "web_server")
        print("✅ Database hazır!")
    except Exception as e:
        print(f"❌ Database başlatma hatası: {e}")
        exit(1)
    
    # MQTT'yi başlat
    print("📡 MQTT Client başlatılıyor...")
    setup_mqtt()
    
    # Flask web server'ı başlat
    print("🌐 Web server başlatılıyor: http://0.0.0.0:5000")
    print("📱 Dashboard: http://192.168.1.7:5000")  # Raspberry Pi IP
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) 