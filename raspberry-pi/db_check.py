#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database İçerik Kontrol Scripti
"""

import sqlite3
from database import get_db_connection

def check_database():
    """Database içeriğini kontrol et"""
    print("🗄️ SQLite Database İçerik Kontrolü")
    print("=" * 40)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Tabloları listele
        print("\n📋 Tablolar:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Cihazları listele
        print("\n🔌 Cihazlar:")
        cursor.execute("SELECT id, device_name, device_type, esp32_pin, device_status FROM devices;")
        devices = cursor.fetchall()
        for device in devices:
            print(f"  ID: {device[0]} | {device[1]} | {device[2]} | GPIO{device[3]} | {device[4]}")
        
        # Kullanıcıları listele
        print("\n👤 Kullanıcılar:")
        cursor.execute("SELECT id, username, role FROM users;")
        users = cursor.fetchall()
        for user in users:
            print(f"  ID: {user[0]} | {user[1]} | {user[2]}")
        
        # Senaryoları listele
        print("\n🎯 Senaryolar:")
        cursor.execute("SELECT id, scenario_name, description, is_active FROM scenarios;")
        scenarios = cursor.fetchall()
        for scenario in scenarios:
            status = "✅ Aktif" if scenario[3] else "❌ Pasif"
            print(f"  ID: {scenario[0]} | {scenario[1]} | {status}")
            print(f"     Açıklama: {scenario[2]}")
        
        # Son sensör okumalarını göster
        print("\n📊 Son Sensör Okumaları:")
        cursor.execute("""
            SELECT d.device_name, dr.raw_value, dr.processed_value, dr.unit, dr.timestamp 
            FROM device_readings dr
            JOIN devices d ON dr.device_id = d.id
            WHERE d.device_type = 'moisture_sensor'
            ORDER BY dr.timestamp DESC
            LIMIT 10
        """)
        readings = cursor.fetchall()
        if readings:
            for reading in readings:
                print(f"  {reading[0]} | Ham: {reading[1]} | İşlenmiş: {reading[2]}{reading[3]} | {reading[4]}")
        else:
            print("  Henüz sensör okuması yok")
        
        # Son eylemleri göster
        print("\n⚡ Son Cihaz Eylemleri:")
        cursor.execute("""
            SELECT d.device_name, da.action_type, da.action_value, da.trigger_source, da.timestamp 
            FROM device_actions da
            JOIN devices d ON da.device_id = d.id
            ORDER BY da.timestamp DESC
            LIMIT 10
        """)
        actions = cursor.fetchall()
        if actions:
            for action in actions:
                print(f"  {action[0]} | {action[1]} | {action[2]} | {action[3]} | {action[4]}")
        else:
            print("  Henüz eylem kaydı yok")
        
        # Sistem loglarını göster
        print("\n📝 Son Sistem Logları:")
        cursor.execute("""
            SELECT log_level, message, module, timestamp 
            FROM system_logs 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        logs = cursor.fetchall()
        if logs:
            for log in logs:
                level_icon = "🔴" if log[0] == "ERROR" else "🟡" if log[0] == "WARNING" else "🟢"
                print(f"  {level_icon} [{log[0]}] {log[1]} | {log[2]} | {log[3]}")
        else:
            print("  Henüz log kaydı yok")
            
        print("\n✅ Database kontrolü tamamlandı!")
        
    except Exception as e:
        print(f"❌ Database kontrol hatası: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_database() 