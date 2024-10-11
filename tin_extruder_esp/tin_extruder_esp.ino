#include <WiFi.h>
#include <ESPmDNS.h>
#include <NetworkUdp.h>
#include <ArduinoOTA.h>
#define STEP 27
#define DIR 26

#define F_FWD 32  // 7
#define F_RVE 33  // 8

const char *ssid = "VKA5Y3-M1013S";
const char *password = "homberger";

WiFiServer server(4242);

IPAddress local_IP(192, 168, 137, 40);
IPAddress gateway(192, 168, 137, 1);
IPAddress subnet(255, 255, 0, 0);
int status = 0;
void setup() {
  Serial.begin(115200);
  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("STA Failed to configure");
  }
  Serial.println("Booting");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.waitForConnectResult() != WL_CONNECTED) {
    Serial.println("Connection Failed! Rebooting...");
    delay(5000);
    ESP.restart();
  }
  pinMode(STEP, OUTPUT);
  pinMode(DIR, OUTPUT);
  pinMode(F_FWD, INPUT_PULLUP);
  pinMode(F_RVE, INPUT_PULLUP);
  digitalWrite(DIR, 0);  // Set Man Forward
  // Port defaults to 3232
  // ArduinoOTA.setPort(3232);

  // Hostname defaults to esp3232-[MAC]
  // ArduinoOTA.setHostname("myesp32");

  // No authentication by default
  // ArduinoOTA.setPassword("admin");

  // Password can be set with it's md5 value as well
  // MD5(admin) = 21232f297a57a5a743894a0e4a801fc3
  // ArduinoOTA.setPasswordHash("21232f297a57a5a743894a0e4a801fc3");

  ArduinoOTA
    .onStart([]() {
      String type;
      if (ArduinoOTA.getCommand() == U_FLASH) {
        type = "sketch";
      } else {  // U_SPIFFS
        type = "filesystem";
      }

      // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
      Serial.println("Start updating " + type);
    })
    .onEnd([]() {
      Serial.println("\nEnd");
    })
    .onProgress([](unsigned int progress, unsigned int total) {
      Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
    })
    .onError([](ota_error_t error) {
      Serial.printf("Error[%u]: ", error);
      if (error == OTA_AUTH_ERROR) {
        Serial.println("Auth Failed");
      } else if (error == OTA_BEGIN_ERROR) {
        Serial.println("Begin Failed");
      } else if (error == OTA_CONNECT_ERROR) {
        Serial.println("Connect Failed");
      } else if (error == OTA_RECEIVE_ERROR) {
        Serial.println("Receive Failed");
      } else if (error == OTA_END_ERROR) {
        Serial.println("End Failed");
      }
    });

  ArduinoOTA.begin();
  server.begin();
  Serial.println("Ready");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {

  WiFiClient client = server.available();
  while (digitalRead(F_FWD) == HIGH) {
    digitalWrite(DIR, 0);  // Forward
    digitalWrite(STEP, 1);
    delayMicroseconds(500);
    digitalWrite(STEP, 0);
    delayMicroseconds(500);
  }
  while (digitalRead(F_RVE) == HIGH) {
    digitalWrite(DIR, 1);  // Forward
    digitalWrite(STEP, 1);
    delayMicroseconds(500);
    digitalWrite(STEP, 0);
    delayMicroseconds(500);
  }
  if (client) {
    Serial.println("New Client Connected");

    while (client.connected()) {
      if (client.available()) {
        String command = client.readStringUntil('\n');
        command.trim();

        int steps = command.toInt();

        // Process the command
        if (steps != 0) {
          if (steps > 0) {
            digitalWrite(DIR, 0);
          } else if (steps < 0) {
            digitalWrite(DIR, 1);
            steps *= -1;
          }

          for (int i = 0; i < steps; i++) {
            digitalWrite(STEP, 1);
            delay(1);
            digitalWrite(STEP, 0);
            delay(1);
          }
          client.println("DONE");
        }
      }
    }
    client.stop();
  }

  Serial.println("Client Disconnected");
}
ArduinoOTA.handle();
}
