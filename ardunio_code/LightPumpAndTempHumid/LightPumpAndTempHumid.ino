// Watchdog timer for system reliability
#include <avr/wdt.h>
// Heater timing enforcement
unsigned long heaterOnStartTime = 0;
bool heaterCooldownActive = false;
unsigned long heaterCooldownStartTime = 0;
const unsigned long heaterMaxOnDuration = 10 * 60 * 1000;  // 10 minutes
const unsigned long heaterCooldownDuration = 10 * 60 * 1000;  // 10 minutes

// Heater fail-safe for missing temp readings
unsigned long lastValidIndoorTempTime = 0;
const unsigned long heaterFailSafeTimeout = 30000;  // 30 seconds
// Pin Definitions

#define RELAY_LIGHTS_TOP 7
#define RELAY_LIGHTS_BOTTOM 8
#define RELAY_PUMP_TOP 9
#define RELAY_PUMP_BOTTOM 10
#define RELAY_VENT_FAN 11
#define RELAY_CIRCULATION_FAN 12
#define RELAY_HEATER 13

#define FLOAT_SENSOR_TOP 4
#define FLOAT_SENSOR_BOTTOM 5

#define DHTPIN A0  // Indoor air temp and humidity sensor
#define DHTPIN2 A1  // Outdoor air temp and humidity sensor
// Separate OneWire buses for each DS18B20 sensor
#define ONE_WIRE_BUS_1 2
#define ONE_WIRE_BUS_2 3


// Include DHT Sensor Library
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>
#include <OneWire.h>
#include <DallasTemperature.h>

OneWire oneWire1(ONE_WIRE_BUS_1);
DallasTemperature sensor1(&oneWire1);
OneWire oneWire2(ONE_WIRE_BUS_2);
DallasTemperature sensor2(&oneWire2);

// Define DHT Sensor Pin & Type
#define DHTTYPE DHT11
DHT dhtIndoor(DHTPIN, DHTTYPE);
DHT dhtOutdoor(DHTPIN2, DHTTYPE);

// Time tracking variables
int hours = 0, minutes = 0, seconds = 0;
unsigned long lastMillis = 0;
unsigned long lastStateUpdate = 0;
unsigned long lastSensorUpdate = 0;

// Function to send the current time status
void sendTimeStatus() {
    Serial.print("TIME:");
    if (hours < 10) Serial.print("0");
    Serial.print(hours);
    Serial.print(":");
    if (minutes < 10) Serial.print("0");
    Serial.print(minutes);
    Serial.print(":");
    if (seconds < 10) Serial.print("0");
    Serial.println(seconds);
}

// Manual override tracking
bool overrideActive = false;
unsigned long overrideEndTime = 0;  // Overrides expire after 10 minutes

// Override duration set to 5 minutes
const unsigned long overrideDuration = 300000; // 5-minute override

// Vent fan timeout
bool ventFanRecentlyOn = false;
unsigned long ventFanOffDelayStart = 0;
const unsigned long ventFanDelayDuration = 5 * 60 * 1000; // 5 minutes

// Vent fan cooldown
bool ventFanInCooldown = false;
unsigned long ventFanCooldownStart = 0;
const unsigned long ventFanCooldownDuration = 10 * 60 * 1000; // 10 minutes

void activateOverride() {
    overrideActive = true;
    overrideEndTime = millis() + overrideDuration;
}

void setup() {
    // Set relay pins as outputs
    pinMode(RELAY_LIGHTS_TOP, OUTPUT);
    pinMode(RELAY_LIGHTS_BOTTOM, OUTPUT);
    pinMode(RELAY_PUMP_TOP, OUTPUT);
    pinMode(RELAY_PUMP_BOTTOM, OUTPUT);
    pinMode(RELAY_VENT_FAN, OUTPUT);
    pinMode(RELAY_CIRCULATION_FAN, OUTPUT);
    pinMode(RELAY_HEATER, OUTPUT);

    digitalWrite(RELAY_LIGHTS_TOP, HIGH);
    digitalWrite(RELAY_LIGHTS_BOTTOM, HIGH);
    digitalWrite(RELAY_PUMP_TOP, HIGH);
    digitalWrite(RELAY_PUMP_BOTTOM, HIGH);
    digitalWrite(RELAY_VENT_FAN, HIGH);
    digitalWrite(RELAY_CIRCULATION_FAN, HIGH);
    digitalWrite(RELAY_HEATER, HIGH);

    pinMode(FLOAT_SENSOR_TOP, INPUT_PULLUP);
    pinMode(FLOAT_SENSOR_BOTTOM, INPUT_PULLUP);

    // Initialize serial communication
    Serial.begin(9600);
    delay(2000);  // Allow serial connection to stabilize

    // Initialize DHT Sensor
    dhtIndoor.begin();
    dhtOutdoor.begin();

    sensor1.begin();
    delay(1000);
    sensor2.begin();

    Serial.println("Arduino is ready. Default time: 00:00. Running schedule.");

    wdt_enable(WDTO_8S);  // Enable watchdog timer with 8-second timeout
}

void loop() {
    unsigned long currentMillis = millis();

    // Increment time every second
    while (currentMillis - lastMillis >= 1000) {
        lastMillis += 1000;
        incrementTime();
        if (!overrideActive) {
            runSchedule();
        }
    }

    // Send relay state and time status every 10 seconds
    if (currentMillis - lastStateUpdate >= 10000) {
        lastStateUpdate = currentMillis;
        sendRelayState();
        sendTimeStatus();
    }

    // If override has expired, return to schedule
    if (overrideActive && millis() >= overrideEndTime) {
        overrideActive = false;
        Serial.println("Override expired. Resuming schedule.");
        runSchedule();
    }

    // Listen for Pi commands (non-blocking serial read)
    static String serialBuffer = "";
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
            serialBuffer.trim();
            if (serialBuffer.length() > 0) {
                handleCommand(serialBuffer);
                sendRelayState();  // Send updated state immediately after a change
            }
            serialBuffer = "";
        } else {
            serialBuffer += c;
        }
    }
}

void sendRelayState() {
    sendRelayStatus();
    sendSensorStatus();
}

void sendRelayStatus() {
    Serial.print("RSTATE:");
    Serial.print("LT="); Serial.print(digitalRead(RELAY_LIGHTS_TOP) == LOW ? 1 : 0); Serial.print(",");
    Serial.print("LB="); Serial.print(digitalRead(RELAY_LIGHTS_BOTTOM) == LOW ? 1 : 0); Serial.print(",");
    Serial.print("PT="); Serial.print(digitalRead(RELAY_PUMP_TOP) == LOW ? 1 : 0); Serial.print(",");
    Serial.print("PB="); Serial.print(digitalRead(RELAY_PUMP_BOTTOM) == LOW ? 1 : 0); Serial.print(",");
    Serial.print("FV="); Serial.print(digitalRead(RELAY_VENT_FAN) == LOW ? 1 : 0); Serial.print(",");
    Serial.print("FC="); Serial.print(digitalRead(RELAY_CIRCULATION_FAN) == LOW ? 1 : 0); Serial.print(",");
    Serial.print("HE="); Serial.print(digitalRead(RELAY_HEATER) == LOW ? 1 : 0);
    Serial.println();
}

void sendSensorStatus() {
    sensor1.requestTemperatures();
    float waterTemp1 = sensor1.getTempCByIndex(0);
    sensor2.requestTemperatures();
    float waterTemp2 = sensor2.getTempCByIndex(0);

    if (isnan(waterTemp1)) waterTemp1 = -1;
    if (isnan(waterTemp2)) waterTemp2 = -1;

    int temp1 = (int)dhtIndoor.readTemperature();
    int humid1 = (int)dhtIndoor.readHumidity();
    int temp2 = (int)dhtOutdoor.readTemperature();
    int humid2 = (int)dhtOutdoor.readHumidity();

    if (isnan(temp1)) temp1 = -1;
    if (isnan(humid1)) humid1 = -1;
    if (isnan(temp2)) temp2 = -1;
    if (isnan(humid2)) humid2 = -1;

    int floatTop = digitalRead(FLOAT_SENSOR_TOP) == LOW ? 1 : 0;
    int floatBottom = digitalRead(FLOAT_SENSOR_BOTTOM) == LOW ? 1 : 0;

    Serial.print("SSTATE:");
    Serial.print(temp1); Serial.print(",");
    Serial.print(humid1); Serial.print(",");
    Serial.print(temp2); Serial.print(",");
    Serial.print(humid2); Serial.print(",");
    Serial.print(waterTemp1, 1); Serial.print(",");
    Serial.print(waterTemp2, 1); Serial.print(",");
    Serial.print(floatTop); Serial.print(",");
    Serial.println(floatBottom);
}

// Function to process commands from the Raspberry Pi
void handleCommand(String command) {
    if (command == "PING") {
        Serial.println("PING_OK");
    } else if (command.startsWith("SET_TIME:")) {
        setTimeFromPi(command.substring(9));
        Serial.println("SET_TIME OK");
        Serial.println("Received time update command: " + command);
        sendRelayState();
    } else if (command == "RESET_SCHEDULE") {  
        Serial.println("Schedule reset. Resuming automatic control.");
        activateOverride();
        runSchedule();
        sendRelayState();  
    } else if (command.startsWith("LT:") || command.startsWith("LB:") || 
               command.startsWith("PT:") || command.startsWith("PB:") ||
               command.startsWith("FV:") || command.startsWith("FC:") ||
               command.startsWith("HE:")) {
        overrideDevice(command);
    } else {
        Serial.println("Unknown command: " + command);
    }
}

// Function to override a specific device
void overrideDevice(String command) {
    int relayPin;
    String deviceName;

    if (command.startsWith("LT:")) {
        relayPin = RELAY_LIGHTS_TOP;
        deviceName = "Lights Top";
    } else if (command.startsWith("LB:")) {
        relayPin = RELAY_LIGHTS_BOTTOM;
        deviceName = "Lights Bottom";
    } else if (command.startsWith("PT:")) {
        relayPin = RELAY_PUMP_TOP;
        deviceName = "Pump Top";
    } else if (command.startsWith("PB:")) {
        relayPin = RELAY_PUMP_BOTTOM;
        deviceName = "Pump Bottom";
    } else if (command.startsWith("FV:")) {
        relayPin = RELAY_VENT_FAN;
        deviceName = "Vent Fan";
    } else if (command.startsWith("FC:")) {
        relayPin = RELAY_CIRCULATION_FAN;
        deviceName = "Circulation Fan";
    } else if (command.startsWith("HE:")) {
        relayPin = RELAY_HEATER;
        deviceName = "Heater";
    } else {
        Serial.println("Unknown command: " + command);
        return;
    }

    String state = command.substring(command.indexOf(':') + 1);

    // Heater override temperature check
    float indoorTemp = dhtIndoor.readTemperature();
    if (command.startsWith("HE:") && state == "ON") {
        bool isDaytime = (hours >= 7 && hours < 19);
        float offThreshold = isDaytime ? 22.0 : 18.0;
        if (!isnan(indoorTemp) && indoorTemp >= offThreshold) {
            Serial.println("Heater override denied: temperature already above threshold.");
            return;
        }
    }

    if (state == "ON") {
        digitalWrite(relayPin, LOW);
        if (command.startsWith("HE:")) {
            digitalWrite(RELAY_CIRCULATION_FAN, LOW);  // Ensure fan is also ON
        }
        activateOverride();
        Serial.println(deviceName + " overridden to ON.");
    } else if (state == "OFF") {
        digitalWrite(relayPin, HIGH);
        if (command.startsWith("HE:")) {
            digitalWrite(RELAY_CIRCULATION_FAN, HIGH);  // Turn fan OFF with heater
        }
        activateOverride();
        Serial.println(deviceName + " overridden to OFF.");
    } else {
        Serial.println("Invalid state for " + deviceName + ": " + state);
    }

    sendRelayState();
}

void setTimeFromPi(String timeString) {
    timeString.trim();  // <- this removes trailing \r and spaces

    Serial.println("⚠ Raw SET_TIME string: [" + timeString + "]");

    int firstColon = timeString.indexOf(':');
    int secondColon = timeString.lastIndexOf(':');

    if (firstColon > 0 && secondColon > firstColon) {
        hours = timeString.substring(0, firstColon).toInt();
        minutes = timeString.substring(firstColon + 1, secondColon).toInt();
        seconds = timeString.substring(secondColon + 1).toInt();

        Serial.print("⏰ Time set to: ");
        Serial.print(hours); Serial.print(":");
        Serial.print(minutes); Serial.print(":");
        Serial.println(seconds);

        // Resume schedule after time update
        overrideActive = false;
        runSchedule();
    } else {
        Serial.println("❌ Invalid time format!");
    }
}

// Function to increment time every second
void incrementTime() {
    seconds++;
    if (seconds >= 60) {
        seconds = 0;
        minutes++;
        if (minutes >= 60) {
            minutes = 0;
            hours++;
            if (hours >= 24) {
                hours = 0;
            }
        }
    }
}

// Function to run the schedule
void runSchedule() {
    if (overrideActive) return; // Skip schedule if overridden

    // **Lights Schedule (7 AM - 7 PM)**
    bool lightsState = (hours >= 7 && hours < 19);
    digitalWrite(RELAY_LIGHTS_TOP, lightsState ? LOW : HIGH);
    digitalWrite(RELAY_LIGHTS_BOTTOM, lightsState ? LOW : HIGH);

    // **Pumps Schedule: ON for 5 minutes at a variable interval based on air temperature**
    bool daylightHours = (hours >= 7 && hours < 19);
    int airTemp = (int)dhtIndoor.readTemperature();  // Read air temperature directly
    if (isnan(airTemp)) airTemp = 20;  // fallback if invalid
    int wateringInterval;

    if (airTemp < 15) {
      wateringInterval = 90; // less frequent in cold weather
    } else if (airTemp < 25) {
      wateringInterval = 60; // moderate interval
    } else {
      wateringInterval = 30; // more frequent in warm weather
    }

    bool dynamicCycle = (minutes % wateringInterval < 5);  // ON for 5 minutes
    bool pumpsState = daylightHours && dynamicCycle;
    digitalWrite(RELAY_PUMP_TOP, pumpsState ? LOW : HIGH);
    digitalWrite(RELAY_PUMP_BOTTOM, pumpsState ? LOW : HIGH);

    // Circulation fan schedule: ON for 10 minutes every hour — only if heater is OFF
    if (digitalRead(RELAY_HEATER) == HIGH) {
        bool circulationFanOn = (minutes % 60 < 10);
        digitalWrite(RELAY_CIRCULATION_FAN, circulationFanOn ? LOW : HIGH);
    }

    // Vent fan trigger with timeout and cooldown logic (guard against NaN)
    int currentTemp = dhtIndoor.readTemperature();
    int currentHumid = dhtIndoor.readHumidity();

    if (!isnan(currentTemp) && !isnan(currentHumid)) {
        // Only allow humidity to trigger the fan if temp > 22°C
        bool sensorTrigger = (currentTemp > 28 || (currentTemp > 22 && currentHumid > 80));

        if (sensorTrigger && !ventFanInCooldown) {
            ventFanRecentlyOn = true;
            ventFanOffDelayStart = millis();
            digitalWrite(RELAY_VENT_FAN, LOW);
        } else if (ventFanRecentlyOn) {
            if (millis() - ventFanOffDelayStart < ventFanDelayDuration) {
                digitalWrite(RELAY_VENT_FAN, LOW);
            } else {
                ventFanRecentlyOn = false;
                ventFanInCooldown = true;
                ventFanCooldownStart = millis();
                digitalWrite(RELAY_VENT_FAN, HIGH);
            }
        } else if (ventFanInCooldown) {
            if (millis() - ventFanCooldownStart >= ventFanCooldownDuration) {
                ventFanInCooldown = false;
            }
            digitalWrite(RELAY_VENT_FAN, HIGH);
        } else {
            digitalWrite(RELAY_VENT_FAN, HIGH);
        }
    } else {
        digitalWrite(RELAY_VENT_FAN, HIGH);  // turn off if readings invalid
    }

    // Heater control logic with day-night temperature simulation
    float indoorTemp = dhtIndoor.readTemperature();
    if (!isnan(indoorTemp)) {
        lastValidIndoorTempTime = millis();  // Update on valid reading

        bool isDaytime = (hours >= 7 && hours < 19);
        float onThreshold = isDaytime ? 20.0 : 16.0;
        float offThreshold = isDaytime ? 22.0 : 18.0;

        static bool lastHeaterState = HIGH;
        int newHeaterState = digitalRead(RELAY_HEATER);

        // Heater timing enforcement logic
        if (heaterCooldownActive && millis() - heaterCooldownStartTime < heaterCooldownDuration) {
            digitalWrite(RELAY_HEATER, HIGH);  // Enforce cooldown
            digitalWrite(RELAY_CIRCULATION_FAN, HIGH);
        } else {
            heaterCooldownActive = false;  // Cooldown expired

            if (indoorTemp < onThreshold) {
                if (digitalRead(RELAY_HEATER) == HIGH) {
                    heaterOnStartTime = millis();  // Mark heater start time
                }
                digitalWrite(RELAY_HEATER, LOW);
                digitalWrite(RELAY_CIRCULATION_FAN, LOW);
            } else if (indoorTemp >= offThreshold || (digitalRead(RELAY_HEATER) == LOW && millis() - heaterOnStartTime >= heaterMaxOnDuration)) {
                digitalWrite(RELAY_HEATER, HIGH);
                digitalWrite(RELAY_CIRCULATION_FAN, HIGH);
                if (digitalRead(RELAY_HEATER) == LOW) {
                    heaterCooldownActive = true;
                    heaterCooldownStartTime = millis();
                }
            }
        }

        newHeaterState = digitalRead(RELAY_HEATER);
        if (newHeaterState != lastHeaterState) {
            sendRelayState();
            lastHeaterState = newHeaterState;
        }
    } else {
        // Fail-safe: shut off heater if no valid reading for 30 seconds
        if (millis() - lastValidIndoorTempTime > heaterFailSafeTimeout) {
            digitalWrite(RELAY_HEATER, HIGH);
            digitalWrite(RELAY_CIRCULATION_FAN, HIGH);
            Serial.println("⚠ Heater shut off: no valid indoor temp reading for 30s.");
        }
    }
    // Reset watchdog timer at the end of loop
    wdt_reset();  // Reset watchdog timer
}