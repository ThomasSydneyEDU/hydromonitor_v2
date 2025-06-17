// Pin Definitions

#define RELAY_SENSOR_PUMP_TOP 7
#define RELAY_SENSOR_PUMP_BOTTOM 8
#define RELAY_DRAIN_ACTUATOR 9
#define RELAY_LIGHTS_TOP 10
#define RELAY_LIGHTS_BOTTOM 11
#define RELAY_PUMP_TOP 12
#define RELAY_PUMP_BOTTOM 13

#define RELAY_VENT_FAN 3
#define RELAY_CIRCULATION_FAN 4

#define FLOAT_SENSOR_TOP 5
#define FLOAT_SENSOR_BOTTOM 6

#define DHTPIN 2  // Air temp and humidity sensor
#define ONE_WIRE_BUS A2  // Water temperature probes

// Include DHT Sensor Library
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Define DHT Sensor Pin & Type
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
DeviceAddress sensor1, sensor2;

// Time tracking variables
int hours = 0, minutes = 0, seconds = 0;
unsigned long lastMillis = 0;
unsigned long lastStateUpdate = 0;
unsigned long lastSensorUpdate = 0;

// Manual override tracking
bool overrideActive = false;
unsigned long overrideEndTime = 0;  // Overrides expire after 10 minutes

// Vent fan timeout
bool ventFanRecentlyOn = false;
unsigned long ventFanOffDelayStart = 0;
const unsigned long ventFanDelayDuration = 5 * 60 * 1000; // 5 minutes

// Vent fan cooldown
bool ventFanInCooldown = false;
unsigned long ventFanCooldownStart = 0;
const unsigned long ventFanCooldownDuration = 10 * 60 * 1000; // 10 minutes

void setup() {
    // Set relay pins as outputs
    pinMode(RELAY_LIGHTS_TOP, OUTPUT);
    pinMode(RELAY_LIGHTS_BOTTOM, OUTPUT);
    pinMode(RELAY_PUMP_TOP, OUTPUT);
    pinMode(RELAY_PUMP_BOTTOM, OUTPUT);

    digitalWrite(RELAY_LIGHTS_TOP, HIGH);
    digitalWrite(RELAY_LIGHTS_BOTTOM, HIGH);
    digitalWrite(RELAY_PUMP_TOP, HIGH);
    digitalWrite(RELAY_PUMP_BOTTOM, HIGH);

    pinMode(RELAY_VENT_FAN, OUTPUT);
    pinMode(RELAY_CIRCULATION_FAN, OUTPUT);

    digitalWrite(RELAY_VENT_FAN, HIGH);
    digitalWrite(RELAY_CIRCULATION_FAN, HIGH);

    pinMode(RELAY_SENSOR_PUMP_TOP, OUTPUT);
    pinMode(RELAY_SENSOR_PUMP_BOTTOM, OUTPUT);
    pinMode(RELAY_DRAIN_ACTUATOR, OUTPUT);

    digitalWrite(RELAY_SENSOR_PUMP_TOP, HIGH);
    digitalWrite(RELAY_SENSOR_PUMP_BOTTOM, HIGH);
    digitalWrite(RELAY_DRAIN_ACTUATOR, HIGH);

    pinMode(FLOAT_SENSOR_TOP, INPUT_PULLUP);
    pinMode(FLOAT_SENSOR_BOTTOM, INPUT_PULLUP);

    // Initialize serial communication
    Serial.begin(9600);
    delay(2000);  // Allow serial connection to stabilize

    // Initialize DHT Sensor
    dht.begin();

    sensors.begin();
    if (!sensors.getAddress(sensor1, 0)) {
        Serial.println("Could not find sensor 0");
    }
    if (!sensors.getAddress(sensor2, 1)) {
        Serial.println("Could not find sensor 1");
    }

    Serial.println("Arduino is ready. Default time: 00:00. Running schedule.");
}

void loop() {
    unsigned long currentMillis = millis();

    // Increment time every second
    if (currentMillis - lastMillis >= 1000) {
        lastMillis = currentMillis;
        incrementTime();
        if (!overrideActive) {
            runSchedule();
        }
    }

    // Send relay state every 10 seconds
    if (currentMillis - lastStateUpdate >= 10000) {
        lastStateUpdate = currentMillis;
        sendRelayState();
    }

    // If override has expired, return to schedule
    if (overrideActive && millis() >= overrideEndTime) {
        overrideActive = false;
        Serial.println("Override expired. Resuming schedule.");
        runSchedule();
    }

    // Listen for Pi commands
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        handleCommand(command);
        sendRelayState();  // Send updated state immediately after a change
    }
}

// Function to send relay states and sensor data to the Pi
void sendRelayState() {
    sensors.requestTemperatures();
    float waterTemp1 = sensors.getTempC(sensor1);
    float waterTemp2 = sensors.getTempC(sensor2);

    if (isnan(waterTemp1)) waterTemp1 = -1;
    if (isnan(waterTemp2)) waterTemp2 = -1;

    // Read sensor values
    int temp = (int)dht.readTemperature(); // Convert float to int
    int humid = (int)dht.readHumidity();   // Convert float to int

    // If sensor readings fail, send default values (-1)
    if (isnan(temp) || isnan(humid)) {
        temp = -1;
        humid = -1;
    }

    int floatTop = digitalRead(FLOAT_SENSOR_TOP) == LOW ? 1 : 0;
    int floatBottom = digitalRead(FLOAT_SENSOR_BOTTOM) == LOW ? 1 : 0;

    // Send relay states and sensor values in a single integer-based string
    Serial.print("STATE:");
    Serial.print(digitalRead(RELAY_LIGHTS_TOP) == LOW ? 1 : 0);
    Serial.print(",");
    Serial.print(digitalRead(RELAY_LIGHTS_BOTTOM) == LOW ? 1 : 0);
    Serial.print(",");
    Serial.print(digitalRead(RELAY_PUMP_TOP) == LOW ? 1 : 0);
    Serial.print(",");
    Serial.print(digitalRead(RELAY_PUMP_BOTTOM) == LOW ? 1 : 0);
    Serial.print(",");
    Serial.print(digitalRead(RELAY_VENT_FAN) == LOW ? 1 : 0);
    Serial.print(",");
    Serial.print(digitalRead(RELAY_CIRCULATION_FAN) == LOW ? 1 : 0);
    Serial.print(",");
    Serial.print(temp);
    Serial.print(",");
    Serial.print(humid);
    Serial.print(",");
    Serial.print(waterTemp1, 1);
    Serial.print(",");
    Serial.print(waterTemp2, 1);
    Serial.print(",");
    Serial.print(floatTop);
    Serial.print(",");
    Serial.print(floatBottom);
    Serial.print(",");
    Serial.print(digitalRead(RELAY_SENSOR_PUMP_TOP) == LOW ? 1 : 0);
    Serial.print(",");
    Serial.print(digitalRead(RELAY_SENSOR_PUMP_BOTTOM) == LOW ? 1 : 0);
    Serial.print(",");
    Serial.println(digitalRead(RELAY_DRAIN_ACTUATOR) == LOW ? 1 : 0);
}

// Function to read and send temperature & humidity
void sendSensorData() {
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();  // Celsius

    if (isnan(humidity) || isnan(temperature)) {
        Serial.println("TEMP:ERROR | HUM:ERROR");
        return;
    }

    Serial.print("TEMP:");
    Serial.print(temperature);
    Serial.print(" | HUM:");
    Serial.println(humidity);
}

// Function to process commands from the Raspberry Pi
void handleCommand(String command) {
    if (command == "PING") {
        Serial.println("PING_OK");
    } else if (command.startsWith("SET_TIME:")) {
        setTimeFromPi(command.substring(9));
        Serial.println("SET_TIME OK");
        sendRelayState();
    } else if (command == "RESET_SCHEDULE") {  
        Serial.println("Schedule reset. Resuming automatic control.");
        overrideActive = false;  
        runSchedule();  
        sendRelayState();  
    } else if (command.startsWith("LT:") || command.startsWith("LB:") || 
               command.startsWith("PT:") || command.startsWith("PB:") ||
               command.startsWith("FV:") || command.startsWith("FC:") ||
               command.startsWith("SPT:") || command.startsWith("SPB:") ||
               command.startsWith("DA:")) {
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
    } else if (command.startsWith("SPT:")) {
        relayPin = RELAY_SENSOR_PUMP_TOP;
        deviceName = "Sensor Pump Top";
    } else if (command.startsWith("SPB:")) {
        relayPin = RELAY_SENSOR_PUMP_BOTTOM;
        deviceName = "Sensor Pump Bottom";
    } else if (command.startsWith("DA:")) {
        relayPin = RELAY_DRAIN_ACTUATOR;
        deviceName = "Drain Actuator";
    } else {
        Serial.println("Unknown command: " + command);
        return;
    }

    String state = command.substring(command.indexOf(':') + 1);
    if (state == "ON") {
        digitalWrite(relayPin, LOW);
        overrideActive = true;
        overrideEndTime = millis() + 600000; // 10-minute override
        Serial.println(deviceName + " overridden to ON.");
    } else if (state == "OFF") {
        digitalWrite(relayPin, HIGH);
        overrideActive = true;
        overrideEndTime = millis() + 600000;
        Serial.println(deviceName + " overridden to OFF.");
    } else {
        Serial.println("Invalid state for " + deviceName + ": " + state);
    }

    sendRelayState();
}

// Function to set time from the Raspberry Pi
void setTimeFromPi(String timeString) {
    int firstColon = timeString.indexOf(':');
    int secondColon = timeString.lastIndexOf(':');

    if (firstColon > 0 && secondColon > firstColon) {
        hours = timeString.substring(0, firstColon).toInt();
        minutes = timeString.substring(firstColon + 1, secondColon).toInt();
        seconds = timeString.substring(secondColon + 1).toInt();
        Serial.print("Time set to: ");
        Serial.print(hours);
        Serial.print(":");
        Serial.print(minutes);
        Serial.print(":");
        Serial.println(seconds);

        // Resume schedule after time update
        overrideActive = false;
        runSchedule();
    } else {
        Serial.println("Invalid time format!");
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

    // **Pumps Schedule: ON for 5 minutes every 30 minutes during daylight hours**
    bool daylightHours = (hours >= 7 && hours < 19);
    bool halfHourCycle = (minutes % 30 < 5);  // ON for 5 minutes every 30
    bool pumpsState = daylightHours && halfHourCycle;
    digitalWrite(RELAY_PUMP_TOP, pumpsState ? LOW : HIGH);
    digitalWrite(RELAY_PUMP_BOTTOM, pumpsState ? LOW : HIGH);

    // Circulation fan schedule: ON for 10 minutes every hour
    bool circulationFanOn = (minutes % 60 < 10);
    digitalWrite(RELAY_CIRCULATION_FAN, circulationFanOn ? LOW : HIGH);

    // Vent fan trigger with timeout and cooldown logic
    int currentTemp = dht.readTemperature();
    int currentHumid = dht.readHumidity();

    bool sensorTrigger = (currentTemp > 28 || currentHumid > 80);

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
}