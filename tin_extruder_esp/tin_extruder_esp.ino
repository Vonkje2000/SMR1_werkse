#include <WiFi.h>
#define STEP 27
#define DIR 26
#define hand_forward 36
#define hand_backward 39
// Replace with your network credentials
const char *ssid = "VKA5Y3-M1013S";
const char *password = "homberger";

WiFiServer server(4242);  // Create a server on port 80
IPAddress ip(192, 168, 137, 40);

void setup() {
	Serial.begin(115200);

	// Connect to Wi-Fi
	Serial.print("Connecting to ");
	Serial.println(ssid);
	WiFi.begin(ssid, password);
	WiFi.config(ip);

	pinMode(STEP, OUTPUT);
	pinMode(DIR, OUTPUT);
	pinMode(hand_forward, INPUT_PULLUP);
	pinMode(hand_forward, INPUT_PULLUP);
	
	Serial.println("Connecting to WiFi");
	while (WiFi.status() != WL_CONNECTED) {
		delay(300);
		Serial.print(".");
	}
	Serial.println();

	Serial.println("Connected to WiFi!");
	Serial.println(WiFi.localIP());
	digitalWrite(DIR, 0);
	// Start the server
	server.begin();
}

void loop() {

	WiFiClient client = server.available();
	if (client) {
		//Serial.println("New Client Connected");

		while (client.connected()) {
			if (client.available()) {
				String command = client.readStringUntil('\n');
				command.trim();

				int steps = command.toInt();

				// Process the command
				if (steps != 0) {
					if (steps > 0){
						digitalWrite(DIR, 0);
					} else if(steps < 0){
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

		// Close the connection
		client.stop();
	}

	if(digitalRead(hand_forward)){
		digitalWrite(DIR, 0);
		digitalWrite(STEP, 1);
		delay(1);
		digitalWrite(STEP, 0);
		delay(1);
	}

	if(digitalRead(hand_backward)){
		digitalWrite(DIR, 1);
		digitalWrite(STEP, 1);
		delay(1);
		digitalWrite(STEP, 0);
		delay(1);
	}
}
