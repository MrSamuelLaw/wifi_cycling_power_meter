#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WebSocketsServer.h>

// --------------------------------------------------
//    _____                _     _____        __
//   / ____|              | |   |  __ \      / _|
//  | |     ___  _ __  ___| |_  | |  | | ___| |_ ___
//  | |    / _ \| '_ \/ __| __| | |  | |/ _ \  _/ __|
//  | |___| (_) | | | \__ \ |_  | |__| |  __/ | \__ \
//   \_____\___/|_| |_|___/\__| |_____/ \___|_| |___/
// --------------------------------------------------


// Wifi login info
const char* ssid {"networkName"};
const char* password {"password"};

// Timing variables
unsigned long high_time{0};
unsigned long low_time{0};
unsigned long total_time{0};
// int test_val{0};

// Pins
const size_t sensor_pin{3}; // use RX pin as GPIO3

// Buffers
String req;

// Object declarations
WebSocketsServer webSocket = WebSocketsServer(81);
IPAddress staticIP{192, 168, 1, 50}; //ESP8266 static ip
IPAddress gateway{192, 168, 1, 254}; //IP Address of your WiFi Router
IPAddress subnet{255, 255, 255, 0}; //Subnet mask

// -------------------------------------------------------------------
//   ______ _    _ _   _      _   _               _____        __
//  |  ____| |  | | \ | |    | | (_)             |  __ \      / _|
//  | |__  | |  | |  \| | ___| |_ _  ___  _ __   | |  | | ___| |_ ___
//  |  __| | |  | | . ` |/ __| __| |/ _ \| '_ \  | |  | |/ _ \  _/ __|
//  | |    | |__| | |\  | (__| |_| | (_) | | | | | |__| |  __/ | \__ \
//  |_|     \____/|_| \_|\___|\__|_|\___/|_| |_| |_____/ \___|_| |___/
// -------------------------------------------------------------------

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:{
            break;
        }
        case WStype_TEXT:{
              String _payload = String((char *) &payload[0]);
              // Serial.println(_payload);
              // send data back to server
              webSocket.sendBIN(num, (uint8_t *) &total_time, sizeof(total_time));
              // webSocket.sendBIN(num, (uint8_t *) &test_val, sizeof(test_val));
              break;
        }
        case WStype_BIN:{
            hexdump(payload, length);
            // echo data back to browser
            webSocket.sendBIN(num, payload, length);
            break;
        }
    }
}

// ------------------------------
//    _____      _
//   / ____|    | |
//  | (___   ___| |_ _   _ _ __
//   \___ \ / _ \ __| | | | '_ \
//   ____) |  __/ |_| |_| | |_) |
//  |_____/ \___|\__|\__,_| .__/
//                        | |
//                        |_|
// ------------------------------

void setup(void) {
  // pinmodes
  pinMode(sensor_pin, INPUT);

  delay(1000);

  // connect to WiFi
  WiFi.hostname("esp8266");
  WiFi.begin(ssid, password);

  // create static ip address
  WiFi.config(staticIP, gateway, subnet);
  WiFi.mode(WIFI_STA);

  // wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.println(WiFi.localIP());

  // start websocket
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
}

// --------------------------
//   _
//  | |
//  | |     ___   ___  _ __
//  | |    / _ \ / _ \| '_ \
//  | |___| (_) | (_) | |_) |
//  |______\___/ \___/| .__/
//                    | |
//                    |_|
// --------------------------

void loop(void) {
  // process the websocket loop
  webSocket.loop();
  // collect an rpm data point
  high_time = pulseIn(sensor_pin, HIGH);
  low_time = pulseIn(sensor_pin, LOW);
  total_time = high_time + low_time;
  // test_val = digitalRead(sensor_pin);
}
