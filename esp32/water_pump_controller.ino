#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi ayarları
const char* ssid = "Zyxel_3691";               
const char* password = "3883D488Y7";         
const char* mqtt_server = "56.228.30.48";      // AWS EC2 IP (eski: 192.168.1.7)

// Pin tanımlamaları
const int STATUS_LED_PIN = 2;     // Durum LED'i (GPIO2) - Dahili mavi LED - WiFi/MQTT durumu
const int LED1_PIN = 4;           // Kontrol edilebilir LED 1 (GPIO4) - GPIO2 yerine dahili LED kullandığımız için
const int LED2_PIN = 5;           // Kontrol edilebilir LED 2 (GPIO5)
const int PUMP_PIN = 14;          // Su pompası kontrolü (GPIO14) - transistör ile

// Analog nem sensörleri
const int MOISTURE1_PIN = 32;     // Nem sensörü 1 (GPIO32)
const int MOISTURE2_PIN = 33;     // Nem sensörü 2 (GPIO33)
const int MOISTURE3_PIN = 34;     // Nem sensörü 3 (GPIO34)

// MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

// Değişkenler
bool led1State = false;          // LED 1 durumu
bool led2State = false;          // LED 2 durumu
bool pumpState = false;          // Su pompası durumu

// Nem sensörü değişkenleri
int moisture1Raw = 0;            // Nem sensörü 1 ham değer (0-4095)
int moisture2Raw = 0;            // Nem sensörü 2 ham değer (0-4095)
int moisture3Raw = 0;            // Nem sensörü 3 ham değer (0-4095)
int moisture1Percent = 0;        // Nem sensörü 1 yüzde (0-100)
int moisture2Percent = 0;        // Nem sensörü 2 yüzde (0-100)
int moisture3Percent = 0;        // Nem sensörü 3 yüzde (0-100)

unsigned long lastStatusSend = 0;
unsigned long lastSensorRead = 0;
const unsigned long STATUS_INTERVAL = 10000; // 10 saniye
const unsigned long SENSOR_INTERVAL = 5000;  // 5 saniye - sensör okuma

void setup() {
  Serial.begin(115200);
  
  // Pin modları
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);
  
  // Başlangıç durumu
  digitalWrite(STATUS_LED_PIN, LOW);  // Mavi LED kapalı (henüz bağlantı yok)
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);
  digitalWrite(PUMP_PIN, LOW);
  
  Serial.println("🚀 ESP32 Dual LED + Pump Kontrol Sistemi Başlatılıyor...");
  Serial.println("🔴 Kırmızı LED: Enerji durumu (otomatik)");
  Serial.println("🔵 Mavi LED: Bağlantı durumu (GPIO2)");
  Serial.printf("LED1 Pin: %d\n", LED1_PIN);
  Serial.printf("LED2 Pin: %d\n", LED2_PIN);
  Serial.printf("Pump Pin: %d\n", PUMP_PIN);
  Serial.printf("Moisture1 Pin: %d\n", MOISTURE1_PIN);
  Serial.printf("Moisture2 Pin: %d\n", MOISTURE2_PIN);
  Serial.printf("Moisture3 Pin: %d\n", MOISTURE3_PIN);
  
  // Sistem başlangıç LED gösterisi
  Serial.println("💡 Sistem LED testi başlıyor...");
  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED_PIN, HIGH);  // Mavi LED aç
    delay(200);
    digitalWrite(STATUS_LED_PIN, LOW);   // Mavi LED kapat
    delay(200);
  }
  Serial.println("✅ LED test tamamlandı.");
  
  // Kontrol LED'leri test
  Serial.println("🧪 Kontrol LED'leri test ediliyor...");
  digitalWrite(LED1_PIN, HIGH);
  delay(500);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, HIGH);
  delay(500);
  digitalWrite(LED2_PIN, LOW);
  Serial.println("✅ Kontrol LED test tamamlandı.");
  
  // Pump test
  Serial.println("🚰 Pump test başlıyor...");
  digitalWrite(PUMP_PIN, HIGH);
  delay(1000);
  digitalWrite(PUMP_PIN, LOW);
  Serial.println("✅ Pump test tamamlandı.");
  
  // Nem sensörü test
  Serial.println("🌱 Nem sensörü test başlıyor...");
  readMoistureSensors();
  Serial.printf("Sensör1: %d (%d%%), Sensör2: %d (%d%%), Sensör3: %d (%d%%)\n", 
    moisture1Raw, moisture1Percent, moisture2Raw, moisture2Percent, moisture3Raw, moisture3Percent);
  Serial.println("✅ Nem sensörü test tamamlandı.");
  
  // WiFi bağlantısı
  Serial.println("📡 WiFi bağlantısı başlatılıyor...");
  setupWiFi();
  
  // MQTT ayarları
  client.setServer(mqtt_server, 1883);
  client.setCallback(onMqttMessage);
  
  Serial.println("🎯 Sistem hazır!");
}

void setupWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("📡 WiFi'ye bağlanıyor");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    // WiFi bağlantısı sırasında mavi LED yanıp sönsün
    digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
  }
  
  Serial.println();
  Serial.print("✅ WiFi bağlandı! IP: ");
  Serial.println(WiFi.localIP());
  
  // WiFi bağlandığında mavi LED sabit yansın
  digitalWrite(STATUS_LED_PIN, HIGH);
  Serial.println("🔵 Mavi LED: WiFi bağlantısı başarılı");
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.printf("MQTT Mesajı alındı [%s]: %s\n", topic, message.c_str());
  
  // LED 1 kontrolü
  if (String(topic) == "led1/control") {
    if (message == "ON" || message == "1") {
      controlLED1(true);
    } else if (message == "OFF" || message == "0") {
      controlLED1(false);
    }
  }
  
  // LED 2 kontrolü
  if (String(topic) == "led2/control") {
    if (message == "ON" || message == "1") {
      controlLED2(true);
    } else if (message == "OFF" || message == "0") {
      controlLED2(false);
    }
  }
  
  // Su pompası kontrolü
  if (String(topic) == "pump/control") {
    if (message == "ON" || message == "1") {
      controlPump(true);
    } else if (message == "OFF" || message == "0") {
      controlPump(false);
    }
  }
  
  // Sistem komutları
  if (String(topic) == "system/command") {
    if (message == "status") {
      sendSystemStatus();
    } else if (message == "restart") {
      ESP.restart();
    } else if (message == "all_on") {
      controlLED1(true);
      controlLED2(true);
      controlPump(true);
    } else if (message == "all_off") {
      controlLED1(false);
      controlLED2(false);
      controlPump(false);
    }
  }
}

void controlLED1(bool state) {
  led1State = state;
  digitalWrite(LED1_PIN, state ? HIGH : LOW);
  
  String status = state ? "ON" : "OFF";
  Serial.printf("💡 LED 1 (GPIO%d): %s\n", LED1_PIN, status.c_str());
  
  // MQTT ile durumu bildir
  client.publish("led1/status", status.c_str());
}

void controlLED2(bool state) {
  led2State = state;
  digitalWrite(LED2_PIN, state ? HIGH : LOW);
  
  String status = state ? "ON" : "OFF";
  Serial.printf("💡 LED 2 (GPIO%d): %s\n", LED2_PIN, status.c_str());
  
  // MQTT ile durumu bildir
  client.publish("led2/status", status.c_str());
}

void controlPump(bool state) {
  pumpState = state;
  digitalWrite(PUMP_PIN, state ? HIGH : LOW);
  
  String status = state ? "ON" : "OFF";
  Serial.printf("🚰 Pump (GPIO%d): %s\n", PUMP_PIN, status.c_str());
  
  // MQTT ile durumu bildir
  client.publish("pump/status", status.c_str());
}

void readMoistureSensors() {
  // Analog değerleri oku (0-4095)
  moisture1Raw = analogRead(MOISTURE1_PIN);
  moisture2Raw = analogRead(MOISTURE2_PIN);
  moisture3Raw = analogRead(MOISTURE3_PIN);
  
  // Yüzde değerine çevir (nem sensörleri genelde ters çalışır)
  // 4095 = kuru toprak (0% nem), 0 = ıslak toprak (100% nem)
  moisture1Percent = map(moisture1Raw, 4095, 0, 0, 100);
  moisture2Percent = map(moisture2Raw, 4095, 0, 0, 100);
  moisture3Percent = map(moisture3Raw, 4095, 0, 0, 100);
  
  // Negatif değerleri sıfırla
  moisture1Percent = constrain(moisture1Percent, 0, 100);
  moisture2Percent = constrain(moisture2Percent, 0, 100);
  moisture3Percent = constrain(moisture3Percent, 0, 100);
}

void sendSensorData() {
  StaticJsonDocument<300> doc;
  doc["device"] = "ESP32_Moisture_Sensors";
  doc["sensor1"]["raw"] = moisture1Raw;
  doc["sensor1"]["percent"] = moisture1Percent;
  doc["sensor2"]["raw"] = moisture2Raw;
  doc["sensor2"]["percent"] = moisture2Percent;
  doc["sensor3"]["raw"] = moisture3Raw;
  doc["sensor3"]["percent"] = moisture3Percent;
  doc["timestamp"] = millis();
  
  String sensorData;
  serializeJson(doc, sensorData);
  
  client.publish("sensors/data", sensorData.c_str());
  
  Serial.printf("🌱 Sensör verileri: S1=%d%%, S2=%d%%, S3=%d%%\n", 
    moisture1Percent, moisture2Percent, moisture3Percent);
}

void sendSystemStatus() {
  StaticJsonDocument<400> doc;
  doc["device"] = "ESP32_DualLED_Controller";
  doc["wifi_signal"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["uptime"] = millis();
  doc["led1_state"] = led1State;
  doc["led2_state"] = led2State;
  doc["pump_state"] = pumpState;
  doc["moisture1_raw"] = moisture1Raw;
  doc["moisture1_percent"] = moisture1Percent;
  doc["moisture2_raw"] = moisture2Raw;
  doc["moisture2_percent"] = moisture2Percent;
  doc["moisture3_raw"] = moisture3Raw;
  doc["moisture3_percent"] = moisture3Percent;
  doc["status_led"] = digitalRead(STATUS_LED_PIN) ? "CONNECTED" : "DISCONNECTED";
  doc["timestamp"] = millis();
  
  String statusData;
  serializeJson(doc, statusData);
  
  client.publish("system/status", statusData.c_str());
  
  Serial.printf("📊 Sistem durumu: LED1=%s, LED2=%s, Pump=%s, WiFi=%ddBm, S1=%d%%, S2=%d%%, S3=%d%%, Status=🔵%s\n", 
    led1State ? "ON" : "OFF",
    led2State ? "ON" : "OFF",
    pumpState ? "ON" : "OFF",
    WiFi.RSSI(),
    moisture1Percent, moisture2Percent, moisture3Percent,
    digitalRead(STATUS_LED_PIN) ? "CONNECTED" : "DISCONNECTED"
  );
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("📡 MQTT'ye bağlanıyor...");
    
    // MQTT bağlantısı sırasında mavi LED hızlı yanıp sönsün
    for (int i = 0; i < 5; i++) {
      digitalWrite(STATUS_LED_PIN, HIGH);
      delay(100);
      digitalWrite(STATUS_LED_PIN, LOW);
      delay(100);
    }
    
    if (client.connect("ESP32DualLEDController")) {
      Serial.println("✅ MQTT bağlandı!");
      
      // MQTT bağlantısı başarılı - mavi LED sabit yak
      digitalWrite(STATUS_LED_PIN, HIGH);
      Serial.println("🔵 Mavi LED: MQTT bağlantısı başarılı");
      
      // Topic'lere abone ol
      client.subscribe("led1/control");
      client.subscribe("led2/control");
      client.subscribe("pump/control");
      client.subscribe("system/command");
      
      // Bağlantı durumunu bildir
      client.publish("system/status", "ESP32 Dual LED Connected");
      sendSystemStatus(); // İlk durum bilgisi
      
      Serial.println("📡 MQTT topic'lerine abone olundu");
      
    } else {
      Serial.printf("❌ MQTT bağlantı hatası, rc=%d\n", client.state());
      Serial.println("🔵 5 saniye sonra tekrar denenecek...");
      
      // Bağlantı hatası - mavi LED söndür
      digitalWrite(STATUS_LED_PIN, LOW);
      delay(5000);
    }
  }
}

void loop() {
  // MQTT bağlantısını kontrol et
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  // Periyodik sensör okuma (5 saniyede bir)
  if (millis() - lastSensorRead > SENSOR_INTERVAL) {
    readMoistureSensors();
    sendSensorData();
    lastSensorRead = millis();
  }
  
  // Periyodik durum gönderimi (10 saniyede bir)
  if (millis() - lastStatusSend > STATUS_INTERVAL) {
    sendSystemStatus();
    lastStatusSend = millis();
  }
  
  delay(100); // CPU'yu meşgul etme
} 