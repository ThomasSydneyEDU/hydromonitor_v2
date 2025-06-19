#include <OneWire.h>
#include <DallasTemperature.h>

// Sensor 1 on pin D2
#define ONE_WIRE_BUS_1 2
OneWire oneWire1(ONE_WIRE_BUS_1);
DallasTemperature sensor1(&oneWire1);

// Sensor 2 on pin D3
#define ONE_WIRE_BUS_2 3
OneWire oneWire2(ONE_WIRE_BUS_2);
DallasTemperature sensor2(&oneWire2);

void setup() {
  Serial.begin(9600);
  delay(1000);

  sensor1.begin();
  sensor2.begin();
}

void loop() {
  sensor1.requestTemperatures();
  float temp1 = sensor1.getTempCByIndex(0);

  sensor2.requestTemperatures();
  float temp2 = sensor2.getTempCByIndex(0);

  Serial.print("Sensor on D2: ");
  if (temp1 == DEVICE_DISCONNECTED_C) {
    Serial.println("Not detected");
  } else {
    Serial.print(temp1);
    Serial.println(" °C");
  }

  Serial.print("Sensor on D3: ");
  if (temp2 == DEVICE_DISCONNECTED_C) {
    Serial.println("Not detected");
  } else {
    Serial.print(temp2);
    Serial.println(" °C");
  }

  delay(2000);  // Wait 2 seconds before next read
}