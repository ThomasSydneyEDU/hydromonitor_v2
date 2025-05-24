// Arduino Hydroponics Control Code

#include <OneWire.h>
#include <DallasTemperature.h>

// Data wire is plugged into digital pin 7 on the Arduino
#define ONE_WIRE_BUS 7

// Setup a oneWire instance to communicate with any OneWire device
OneWire oneWire(ONE_WIRE_BUS);

// Pass oneWire reference to DallasTemperature library
DallasTemperature sensors(&oneWire);

// Define pins for the components
#define LIGHTS_TOP_PIN 2
#define LIGHTS_BOTTOM_PIN 3
#define PUMP_TOP_PIN 4
#define PUMP_BOTTOM_PIN 5

void setup() {
  // Initialize serial communication
  Serial.begin(9600);

  // Start up the temperature sensors library
  sensors.begin();

  // Set pins as output
  pinMode(LIGHTS_TOP_PIN, OUTPUT);
  pinMode(LIGHTS_BOTTOM_PIN, OUTPUT);
  pinMode(PUMP_TOP_PIN, OUTPUT);
  pinMode(PUMP_BOTTOM_PIN, OUTPUT);

  // Ensure all components are off at startup
  digitalWrite(LIGHTS_TOP_PIN, LOW);
  digitalWrite(LIGHTS_BOTTOM_PIN, LOW);
  digitalWrite(PUMP_TOP_PIN, LOW);
  digitalWrite(PUMP_BOTTOM_PIN, LOW);

  Serial.println("Arduino ready.");
}

void loop() {
  // Check if data is available on the serial port
  if (Serial.available() > 0) {
    // Read the incoming command
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove any extra whitespace or newline characters

    // Process the command
    if (command.startsWith("LT:ON")) {
      digitalWrite(LIGHTS_TOP_PIN, HIGH);
      Serial.println("Lights Top ON");
    } else if (command.startsWith("LT:OFF")) {
      digitalWrite(LIGHTS_TOP_PIN, LOW);
      Serial.println("Lights Top OFF");
    } else if (command.startsWith("LB:ON")) {
      digitalWrite(LIGHTS_BOTTOM_PIN, HIGH);
      Serial.println("Lights Bottom ON");
    } else if (command.startsWith("LB:OFF")) {
      digitalWrite(LIGHTS_BOTTOM_PIN, LOW);
      Serial.println("Lights Bottom OFF");
    } else if (command.startsWith("PT:ON")) {
      digitalWrite(PUMP_TOP_PIN, HIGH);
      Serial.println("Pump Top ON");
    } else if (command.startsWith("PT:OFF")) {
      digitalWrite(PUMP_TOP_PIN, LOW);
      Serial.println("Pump Top OFF");
    } else if (command.startsWith("PB:ON")) {
      digitalWrite(PUMP_BOTTOM_PIN, HIGH);
      Serial.println("Pump Bottom ON");
    } else if (command.startsWith("PB:OFF")) {
      digitalWrite(PUMP_BOTTOM_PIN, LOW);
      Serial.println("Pump Bottom OFF");
    } else if (command == "GET_TEMP") {
      float tempC = getTemperatureC();
      float tempF = (tempC * 9.0) / 5.0 + 32.0;
      Serial.print("Temperature: ");
      Serial.print(tempC);
      Serial.print((char)176); // degrees character
      Serial.print("C | ");
      Serial.print(tempF);
      Serial.print((char)176); // degrees character
      Serial.println("F");
    } else {
      // Invalid command
      Serial.println("Invalid command received.");
    }
  }

  // Print temperature to the serial monitor every 5 seconds for debugging
  static unsigned long lastDebugTime = 0;
  if (millis() - lastDebugTime >= 5000) {
    float tempC = getTemperatureC();
    float tempF = (tempC * 9.0) / 5.0 + 32.0;
    Serial.print("[Debug] Current Temperature: ");
    Serial.print(tempC);
    Serial.print((char)176); // degrees character
    Serial.print("C | ");
    Serial.print(tempF);
    Serial.print((char)176); // degrees character
    Serial.println("F");
    lastDebugTime = millis();
  }
}

float getTemperatureC() {
  // Request temperatures from sensors
  sensors.requestTemperatures();
  // Get temperature in Celsius from the first sensor
  return sensors.getTempCByIndex(0);
}
