#include <WiFi.h>

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

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi!");
  Serial.println(WiFi.localIP());

  // Start the server
  server.begin();
}

void loop() {
  // Check if a client has connected
  WiFiClient client = server.available();
  if (client) {
    Serial.println("New Client Connected");

    while (client.connected()) {
      if (client.available()) {
        String command = client.readStringUntil('\n');
        Serial.print("Received command: ");
        Serial.println(command);

        // Process the command
        if (command == "EXTRUDE") {
          // Do something, e.g., turn on an LED
          Serial.println("Turning ON");
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
