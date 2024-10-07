#include <WiFi.h>
#define STEP 27
#define DIR 26
// Replace with your network credentials
const char *ssid = "VKA5Y3-M1013S";
const char *password = "homberger";

WiFiServer server(4242);  // Create a server on port 80

void setup() {
  Serial.begin(115200);

  // Connect to Wi-Fi
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  pinMode(STEP, OUTPUT);
  pinMode(DIR, OUTPUT);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi!");
  Serial.println(WiFi.localIP());
  digitalWrite(DIR, 1);
  // Start the server
  server.begin();
}

void loop() {

  // delay(1000);
  //Check if a client has connected
    WiFiClient client = server.available();
  if (client) {
    Serial.println("New Client Connected");

    while (client.connected()) {
      if (client.available()) {
        String command = client.readStringUntil('\n');
        command.trim();
        Serial.print("Received command: ");
        Serial.println(command);

        // Process the command
        if (command == "EXTRUDE") {
          // Do something, e.g., turn on an LED
          Serial.println("Spinning");
          client.println("ACK");
          for (int i = 0; i < 100; i++) {
            Serial.println(digitalRead(STEP));
            digitalWrite(STEP, !digitalRead(STEP));
            delay(10);
          }
        } else {
          Serial.println("Unknown Command");
        }
      }
    }

    // Close the connection
    client.stop();
    Serial.println("Client Disconnected");
  }
}
