#include <OneWire.h>
#include <DallasTemperature.h>

// Data wire connected to A2
#define ONE_WIRE_BUS A2

// Setup a oneWire instance and DallasTemperature instance
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(9600);
  delay(1000); // Let serial settle

  sensors.begin();
  Serial.print("Devices found on bus: ");
  Serial.println(sensors.getDeviceCount());
}

void loop() {
  sensors.requestTemperatures(); // Send command to get temperatures

  int deviceCount = sensors.getDeviceCount();
  for (int i = 0; i < deviceCount; i++) {
    float tempC = sensors.getTempCByIndex(i);
    Serial.print("Sensor ");
    Serial.print(i);
    Serial.print(": ");
    if (tempC == DEVICE_DISCONNECTED_C) {
      Serial.println("Not detected.");
    } else {
      Serial.print(tempC);
      Serial.println(" °C");
    }
  }

  delay(2000); // Read every 2 seconds
}