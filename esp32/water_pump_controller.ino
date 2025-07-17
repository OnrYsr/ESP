#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi ayarları
const char* ssid = "Zyxel_3691";               
const char* password = "3883D488Y7";         
const char* mqtt_server = "192.168.1.7";      // Raspberry Pi IP

// Pin tanımlamaları
const int STATUS_LED_PIN = 13;    // Durum LED'i (GPIO13) - WiFi durumu
const int LED1_PIN = 2;           // Kontrol edilebilir LED 1 (GPIO2) - GPIO4 yerine
const int LED2_PIN = 5;           // Kontrol edilebilir LED 2 (GPIO5)

// MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

// Değişkenler
bool led1State = false;          // LED 1 durumu
bool led2State = false;          // LED 2 durumu
unsigned long lastStatusSend = 0;
const unsigned long STATUS_INTERVAL = 10000; // 10 saniye

void setup() {
  Serial.begin(115200);
  
  // Pin modları
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  
  // Başlangıç durumu
  digitalWrite(STATUS_LED_PIN, LOW);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);
  
  Serial.println("ESP32 Dual LED Kontrol Sistemi Başlatılıyor...");
  Serial.printf("LED1 Pin: %d\n", LED1_PIN);
  Serial.printf("LED2 Pin: %d\n", LED2_PIN);
  
  // LED test
  Serial.println("LED test başlıyor...");
  digitalWrite(LED1_PIN, HIGH);
  delay(500);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, HIGH);
  delay(500);
  digitalWrite(LED2_PIN, LOW);
  Serial.println("LED test tamamlandı.");
  
  // WiFi bağlantısı
  setupWiFi();
  
  // MQTT ayarları
  client.setServer(mqtt_server, 1883);
  client.setCallback(onMqttMessage);
  
  Serial.println("Sistem hazır!");
  blinkStatusLED(3); // Hazır sinyali
}

void setupWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("WiFi'ye bağlanıyor");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN)); // Bağlantı sırasında LED yanıp sönsün
  }
  
  Serial.println();
  Serial.print("WiFi bağlandı! IP: ");
  Serial.println(WiFi.localIP());
  digitalWrite(STATUS_LED_PIN, HIGH); // Bağlantı başarılı
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
  
  // Sistem komutları
  if (String(topic) == "system/command") {
    if (message == "status") {
      sendSystemStatus();
    } else if (message == "restart") {
      ESP.restart();
    } else if (message == "all_on") {
      controlLED1(true);
      controlLED2(true);
    } else if (message == "all_off") {
      controlLED1(false);
      controlLED2(false);
    }
  }
}

void controlLED1(bool state) {
  led1State = state;
  digitalWrite(LED1_PIN, state ? HIGH : LOW);
  
  String status = state ? "ON" : "OFF";
  Serial.printf("LED 1 (GPIO%d): %s\n", LED1_PIN, status.c_str());
  
  // MQTT ile durumu bildir
  client.publish("led1/status", status.c_str());
}

void controlLED2(bool state) {
  led2State = state;
  digitalWrite(LED2_PIN, state ? HIGH : LOW);
  
  String status = state ? "ON" : "OFF";
  Serial.printf("LED 2 (GPIO%d): %s\n", LED2_PIN, status.c_str());
  
  // MQTT ile durumu bildir
  client.publish("led2/status", status.c_str());
}

void sendSystemStatus() {
  StaticJsonDocument<200> doc;
  doc["device"] = "ESP32_DualLED_Controller";
  doc["wifi_signal"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["uptime"] = millis();
  doc["led1_state"] = led1State;
  doc["led2_state"] = led2State;
  doc["timestamp"] = millis();
  
  String statusData;
  serializeJson(doc, statusData);
  
  client.publish("system/status", statusData.c_str());
  
  Serial.printf("Sistem durumu: LED1=%s, LED2=%s, WiFi=%ddBm\n", 
    led1State ? "ON" : "OFF",
    led2State ? "ON" : "OFF",
    WiFi.RSSI()
  );
}

void blinkStatusLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(200);
    digitalWrite(STATUS_LED_PIN, LOW);
    delay(200);
  }
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("MQTT'ye bağlanıyor...");
    
    if (client.connect("ESP32DualLEDController")) {
      Serial.println("bağlandı!");
      
      // Topic'lere abone ol
      client.subscribe("led1/control");
      client.subscribe("led2/control");
      client.subscribe("system/command");
      
      // Bağlantı durumunu bildir
      client.publish("system/status", "ESP32 Dual LED Connected");
      sendSystemStatus(); // İlk durum bilgisi
      blinkStatusLED(2); // Bağlantı sinyali
      
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
  
  // Periyodik durum gönderimi (10 saniyede bir)
  if (millis() - lastStatusSend > STATUS_INTERVAL) {
    sendSystemStatus();
    lastStatusSend = millis();
  }
  
  delay(100); // CPU'yu meşgul etme
} 