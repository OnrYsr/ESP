#include <WiFi.h>
#include <PubSubClient.h>

// WiFi ayarları
const char* ssid = "Zyxel_3691";               
const char* password = "3883D488Y7";         
const char* mqtt_server = "192.168.1.7";      // Raspberry Pi IP

// Pin tanımlamaları
const int PUMP_PIN = 2;          // Su pompası röle pini (GPIO2)
const int LED_PIN = 13;          // Durum LED'i (GPIO13)
const int CONTROL_LED_PIN = 4;   // Kontrol edilebilir LED (GPIO4)
const int MOISTURE_PIN = A0;     // Nem sensörü analog pini (A0)

// MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

// Değişkenler
bool pumpState = false;
bool controlLedState = false;    // Kontrol edilebilir LED durumu
int moistureLevel = 0;
unsigned long lastSensorRead = 0;
const unsigned long SENSOR_INTERVAL = 5000; // 5 saniye

void setup() {
  Serial.begin(115200);
  
  // Pin modları
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(CONTROL_LED_PIN, OUTPUT);
  pinMode(MOISTURE_PIN, INPUT);
  
  // Başlangıç durumu
  digitalWrite(PUMP_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(CONTROL_LED_PIN, LOW);
  
  Serial.println("ESP32 Su Pompası Kontrolcüsü Başlatılıyor...");
  
  // WiFi bağlantısı
  setupWiFi();
  
  // MQTT ayarları
  client.setServer(mqtt_server, 1883);
  client.setCallback(onMqttMessage);
  
  Serial.println("Sistem hazır!");
  blinkLED(3); // Hazır sinyali
}

void setupWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("WiFi'ye bağlanıyor");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Bağlantı sırasında LED yanıp sönsün
  }
  
  Serial.println();
  Serial.print("WiFi bağlandı! IP: ");
  Serial.println(WiFi.localIP());
  digitalWrite(LED_PIN, HIGH); // Bağlantı başarılı
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.printf("MQTT Mesajı alındı [%s]: %s\n", topic, message.c_str());
  
  // Su pompası kontrolü
  if (String(topic) == "water/pump") {
    if (message == "ON" || message == "1") {
      controlPump(true);
    } else if (message == "OFF" || message == "0") {
      controlPump(false);
    }
  }
  
  // LED kontrolü
  if (String(topic) == "led/control") {
    if (message == "ON" || message == "1") {
      controlLED(true);
    } else if (message == "OFF" || message == "0") {
      controlLED(false);
    }
  }
  
  // Sistem komutları
  if (String(topic) == "system/command") {
    if (message == "status") {
      sendSystemStatus();
    } else if (message == "restart") {
      ESP.restart();
    }
  }
}

void controlPump(bool state) {
  pumpState = state;
  digitalWrite(PUMP_PIN, state ? HIGH : LOW);
  
  String status = state ? "ON" : "OFF";
  Serial.printf("Su pompası: %s\n", status.c_str());
  
  // MQTT ile durumu bildir
  client.publish("water/pump/status", status.c_str());
  
  // LED durumu güncelle
  digitalWrite(LED_PIN, state ? HIGH : LOW);
}

void controlLED(bool state) {
  controlLedState = state;
  digitalWrite(CONTROL_LED_PIN, state ? HIGH : LOW);
  
  String status = state ? "ON" : "OFF";
  Serial.printf("Kontrol LED'i: %s\n", status.c_str());
  
  // MQTT ile durumu bildir
  client.publish("led/status", status.c_str());
}

void readSensors() {
  // Nem sensörü oku
  moistureLevel = analogRead(MOISTURE_PIN);
  int moisturePercent = map(moistureLevel, 0, 4095, 0, 100);
  
  // Basit string formatında veri hazırla (JSON olmadan)
  String sensorData = "moisture:" + String(moistureLevel) + 
                     ",moisture_percent:" + String(moisturePercent) +
                     ",pump_state:" + (pumpState ? "true" : "false") +
                     ",led_state:" + (controlLedState ? "true" : "false") +
                     ",timestamp:" + String(millis());
  
  // MQTT ile gönder
  client.publish("sensors/data", sensorData.c_str());
  
  Serial.printf("Sensör verisi: Nem=%d (%d%%), Pompa=%s, LED=%s\n", 
    moistureLevel, 
    moisturePercent,
    pumpState ? "ON" : "OFF",
    controlLedState ? "ON" : "OFF"
  );
}

void sendSystemStatus() {
  // Basit string formatında sistem durumu
  String statusData = "device:ESP32_WaterController," +
                     String("wifi_signal:") + String(WiFi.RSSI()) +
                     ",free_heap:" + String(ESP.getFreeHeap()) +
                     ",uptime:" + String(millis()) +
                     ",pump_state:" + (pumpState ? "true" : "false") +
                     ",led_state:" + (controlLedState ? "true" : "false") +
                     ",moisture_level:" + String(moistureLevel);
  
  client.publish("system/status", statusData.c_str());
  Serial.println("Sistem durumu gönderildi");
}

void blinkLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("MQTT'ye bağlanıyor...");
    
    if (client.connect("ESP32WaterController")) {
      Serial.println("bağlandı!");
      
      // Topic'lere abone ol
      client.subscribe("water/pump");
      client.subscribe("led/control");
      client.subscribe("system/command");
      
      // Bağlantı durumunu bildir
      client.publish("system/status", "ESP32 Connected");
      blinkLED(2); // Bağlantı sinyali
      
    } else {
      Serial.printf("başarısız, rc=%d 5 saniye sonra tekrar dene\n", client.state());
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
  
  // Sensör verilerini oku (belirli aralıklarla)
  if (millis() - lastSensorRead > SENSOR_INTERVAL) {
    readSensors();
    lastSensorRead = millis();
  }
  
  delay(100); // CPU'yu meşgul etme
} 