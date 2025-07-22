#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 Akıllı Sulama Sistemi - SQLite Database
Veritabanı şeması ve yardımcı fonksiyonlar
"""

import sqlite3
import json
from datetime import datetime
import os

# Database dosya yolu
DB_PATH = os.path.join(os.path.dirname(__file__), 'irrigation_system.db')

def get_db_connection():
    """SQLite veritabanı bağlantısı"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Dict-like access
    return conn

def init_database():
    """Veritabanını ve tabloları oluştur"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Kullanıcılar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100),
                password_hash VARCHAR(255),
                role VARCHAR(20) DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # 2. Cihazlar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                device_name VARCHAR(100) NOT NULL,
                device_type VARCHAR(50) NOT NULL,
                esp32_pin INTEGER,
                device_status VARCHAR(20) DEFAULT 'active',
                device_location VARCHAR(100),
                calibration_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 3. Cihaz okumaları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                raw_value INTEGER,
                processed_value REAL,
                unit VARCHAR(10),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id)
            )
        ''')
        
        # 4. Cihaz eylemleri tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                action_value VARCHAR(100),
                trigger_source VARCHAR(50) DEFAULT 'manual',
                user_id INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 5. Senaryolar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                scenario_name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 6. Senaryo koşulları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scenario_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                device_id INTEGER NOT NULL,
                condition_type VARCHAR(50) NOT NULL,
                condition_value VARCHAR(100) NOT NULL,
                logical_operator VARCHAR(10) DEFAULT 'AND',
                condition_order INTEGER DEFAULT 1,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id),
                FOREIGN KEY (device_id) REFERENCES devices(id)
            )
        ''')
        
        # 7. Senaryo eylemleri tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scenario_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                target_device_id INTEGER NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                action_value VARCHAR(100),
                action_delay INTEGER DEFAULT 0,
                action_order INTEGER DEFAULT 1,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id),
                FOREIGN KEY (target_device_id) REFERENCES devices(id)
            )
        ''')
        
        # 8. Senaryo logları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scenario_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                execution_status VARCHAR(50) NOT NULL,
                trigger_reason TEXT,
                actions_executed TEXT,
                execution_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
            )
        ''')
        
        # 9. Sistem logları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_level VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                module VARCHAR(50),
                user_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        print("✅ Veritabanı tabloları başarıyla oluşturuldu!")
        
        # Varsayılan veriler ekle
        insert_default_data(conn)
        
    except Exception as e:
        print(f"❌ Veritabanı oluşturma hatası: {e}")
        conn.rollback()
    finally:
        conn.close()

def insert_default_data(conn):
    """Varsayılan verileri ekle"""
    cursor = conn.cursor()
    
    try:
        # Varsayılan kullanıcı
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, username, email, role)
            VALUES (1, 'admin', 'admin@irrigation.local', 'admin')
        ''')
        
        # Mevcut cihazları ekle
        devices_data = [
            (1, 'LED 1', 'led', 2, 'active', 'ESP32 GPIO2'),
            (2, 'LED 2', 'led', 5, 'active', 'ESP32 GPIO5'),
            (3, 'Su Pompası', 'pump', 14, 'active', 'ESP32 GPIO14'),
            (4, 'Nem Sensörü 1', 'moisture_sensor', 32, 'active', 'ESP32 GPIO32'),
            (5, 'Nem Sensörü 2', 'moisture_sensor', 33, 'active', 'ESP32 GPIO33'),
            (6, 'Nem Sensörü 3', 'moisture_sensor', 34, 'active', 'ESP32 GPIO34'),
        ]
        
        for device in devices_data:
            cursor.execute('''
                INSERT OR IGNORE INTO devices (id, device_name, device_type, esp32_pin, device_status, device_location)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', device)
        
        # Örnek senaryo
        cursor.execute('''
            INSERT OR IGNORE INTO scenarios (id, scenario_name, description, is_active)
            VALUES (1, 'Otomatik Sulama', 'Nem seviyesi düşük olduğunda otomatik sulama', 1)
        ''')
        
        conn.commit()
        print("✅ Varsayılan veriler eklendi!")
        
    except Exception as e:
        print(f"❌ Varsayılan veri ekleme hatası: {e}")

# Database helper fonksiyonları
def log_system_event(message, level='INFO', module='system', user_id=1):
    """Sistem olayını logla"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO system_logs (log_level, message, module, user_id)
            VALUES (?, ?, ?, ?)
        ''', (level, message, module, user_id))
        conn.commit()
    except Exception as e:
        print(f"Log kaydetme hatası: {e}")
    finally:
        conn.close()

def save_device_reading(device_id, raw_value, processed_value, unit='%'):
    """Cihaz okumasını kaydet"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO device_readings (device_id, raw_value, processed_value, unit)
            VALUES (?, ?, ?, ?)
        ''', (device_id, raw_value, processed_value, unit))
        conn.commit()
    except Exception as e:
        print(f"Cihaz okuma kaydetme hatası: {e}")
    finally:
        conn.close()

def save_device_action(device_id, action_type, action_value, trigger_source='manual', user_id=1):
    """Cihaz eylemini kaydet"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO device_actions (device_id, action_type, action_value, trigger_source, user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (device_id, action_type, action_value, trigger_source, user_id))
        conn.commit()
    except Exception as e:
        print(f"Cihaz eylem kaydetme hatası: {e}")
    finally:
        conn.close()

def get_device_by_pin(esp32_pin):
    """GPIO pin numarasına göre cihaz bilgisi getir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM devices WHERE esp32_pin = ?', (esp32_pin,))
        device = cursor.fetchone()
        return dict(device) if device else None
    except Exception as e:
        print(f"Cihaz sorgulama hatası: {e}")
        return None
    finally:
        conn.close()

def get_recent_readings(device_id, limit=50):
    """Son cihaz okumalarını getir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM device_readings 
            WHERE device_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (device_id, limit))
        readings = cursor.fetchall()
        return [dict(row) for row in readings]
    except Exception as e:
        print(f"Okuma geçmişi sorgulama hatası: {e}")
        return []
    finally:
        conn.close()

# ===========================================
# USER MANAGEMENT FUNCTIONS
# ===========================================

from werkzeug.security import generate_password_hash, check_password_hash

def create_user(username, password, email=None, role='user'):
    """Yeni kullanıcı oluştur"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Şifreyi hashle
        password_hash = generate_password_hash(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, role))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        log_system_event(f"Yeni kullanıcı oluşturuldu: {username}", "INFO", "user_management")
        return user_id
        
    except sqlite3.IntegrityError:
        print(f"❌ Kullanıcı adı zaten mevcut: {username}")
        return None
    except Exception as e:
        print(f"❌ Kullanıcı oluşturma hatası: {e}")
        return None
    finally:
        conn.close()

def authenticate_user(username, password):
    """Kullanıcı doğrulama"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, username, password_hash, role, email
            FROM users 
            WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # Son giriş zamanını güncelle
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (user['id'],))
            conn.commit()
            
            log_system_event(f"Kullanıcı giriş yaptı: {username}", "INFO", "auth")
            return dict(user)
        else:
            log_system_event(f"Başarısız giriş denemesi: {username}", "WARNING", "auth")
            return None
            
    except Exception as e:
        print(f"❌ Kimlik doğrulama hatası: {e}")
        return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    """ID ile kullanıcı getir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, username, email, role, created_at, last_login
            FROM users 
            WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        return dict(user) if user else None
        
    except Exception as e:
        print(f"❌ Kullanıcı sorgu hatası: {e}")
        return None
    finally:
        conn.close()

def get_user_devices(user_id):
    """Kullanıcının cihazlarını getir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, device_name, device_type, esp32_pin, device_status, device_location
            FROM devices 
            WHERE user_id = ? AND device_status = 'active'
            ORDER BY device_name
        ''', (user_id,))
        
        devices = cursor.fetchall()
        return [dict(row) for row in devices]
        
    except Exception as e:
        print(f"❌ Kullanıcı cihazları sorgu hatası: {e}")
        return []
    finally:
        conn.close()

def create_default_admin():
    """Varsayılan admin kullanıcısı oluştur"""
    admin_exists = authenticate_user('admin', 'dummy_check')
    
    if not admin_exists:
        admin_id = create_user(
            username='admin',
            password='esp32secure2024!',
            email='admin@esp32-iot.local',
            role='admin'
        )
        
        if admin_id:
            print("✅ Varsayılan admin kullanıcısı oluşturuldu")
            print("👤 Kullanıcı: admin")
            print("🔒 Şifre: esp32secure2024!")
            return admin_id
    else:
        print("ℹ️  Admin kullanıcısı zaten mevcut")
        return None

def get_all_users():
    """Tüm kullanıcıları listele (admin için)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, username, email, role, created_at, last_login
            FROM users 
            ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        return [dict(row) for row in users]
        
    except Exception as e:
        print(f"❌ Kullanıcı listesi sorgu hatası: {e}")
        return []
    finally:
        conn.close()

if __name__ == '__main__':
    # Test için veritabanını oluştur
    print("🗄️ SQLite veritabanı oluşturuluyor...")
    init_database()
    print("✅ Veritabanı hazır!")
    
    # Varsayılan admin kullanıcısını oluştur
    create_default_admin()
    
    # Test verileri
    log_system_event("Database sistem başlatıldı", "INFO", "database")
    print("📊 Test verileri eklendi!") 