// Pin Definitions
#define RELAY_LIGHTS_TOP 2
#define RELAY_LIGHTS_BOTTOM 3
#define RELAY_PUMP_TOP 4
#define RELAY_PUMP_BOTTOM 5

// Time tracking variables
int hours = 0, minutes = 0, seconds = 0;
unsigned long lastMillis = 0;

// Manual override tracking
bool overrideActive = false;
unsigned long overrideEndTime = 0; // Overrides expire after 10 minutes

void setup() {
    // Set relay pins as outputs
    pinMode(RELAY_LIGHTS_TOP, OUTPUT);
    pinMode(RELAY_LIGHTS_BOTTOM, OUTPUT);
    pinMode(RELAY_PUMP_TOP, OUTPUT);
    pinMode(RELAY_PUMP_BOTTOM, OUTPUT);

    // Initialize serial communication
    Serial.begin(9600);
    delay(2000);  // Allow serial connection to stabilize

    Serial.println("Arduino is ready. Default time: 00:00. Running schedule.");
}

// Keeps track of the last time relay states were sent to the Pi
unsigned long lastStateUpdate = 0;

void loop() {
    unsigned long currentMillis = millis();

    // Increment time every second
    if (currentMillis - lastMillis >= 1000) {
        lastMillis = currentMillis;
        incrementTime();
        Serial.println("Running schedule update...");  // ✅ Debug print
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

// Function to send relay states to the Pi
void sendRelayState() {
    Serial.print("STATE:");
    Serial.print(digitalRead(RELAY_LIGHTS_TOP));
    Serial.print(",");
    Serial.print(digitalRead(RELAY_LIGHTS_BOTTOM));
    Serial.print(",");
    Serial.print(digitalRead(RELAY_PUMP_TOP));
    Serial.print(",");
    Serial.println(digitalRead(RELAY_PUMP_BOTTOM));
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
               command.startsWith("PT:") || command.startsWith("PB:")) {
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
    } else {
        Serial.println("Unknown command: " + command);
        return;
    }

    String state = command.substring(3);
    if (state == "ON") {
        digitalWrite(relayPin, HIGH);
        overrideActive = true;
        overrideEndTime = millis() + 600000; // ✅ 10-minute override
        Serial.println(deviceName + " overridden to ON.");
    } else if (state == "OFF") {
        digitalWrite(relayPin, LOW);
        overrideActive = true;
        overrideEndTime = millis() + 600000;
        Serial.println(deviceName + " overridden to OFF.");
    } else {
        Serial.println("Invalid state for " + deviceName + ": " + state);
    }

    sendRelayState();  // ✅ Send immediate relay update
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

    // **Lights Schedule (9 AM - 9 PM)**
    bool lightsState = (hours >= 9 && hours < 21);
    digitalWrite(RELAY_LIGHTS_TOP, lightsState ? HIGH : LOW);
    digitalWrite(RELAY_LIGHTS_BOTTOM, lightsState ? HIGH : LOW);

    // **Pumps Schedule (15 minutes every 4 hours)**
    bool pumpsState = (minutes < 15) && (hours % 4 == 0);
    
    // ✅ Force correction if actual state doesn't match schedule
    if (digitalRead(RELAY_PUMP_TOP) != pumpsState) {
        Serial.println("Pump state mismatch! Correcting...");
        digitalWrite(RELAY_PUMP_TOP, pumpsState ? HIGH : LOW);
        digitalWrite(RELAY_PUMP_BOTTOM, pumpsState ? HIGH : LOW);
    }

    // Debug output every minute
    if (seconds == 0) {
        Serial.print("Current Time: ");
        Serial.print(hours);
        Serial.print(":");
        if (minutes < 10) Serial.print("0");
        Serial.print(minutes);
        Serial.println();

        Serial.print("Lights: ");
        Serial.print(digitalRead(RELAY_LIGHTS_TOP) ? "ON " : "OFF ");
        Serial.println(digitalRead(RELAY_LIGHTS_BOTTOM) ? "ON" : "OFF");

        Serial.print("Pumps: ");
        Serial.print(digitalRead(RELAY_PUMP_TOP) ? "ON " : "OFF ");
        Serial.println(digitalRead(RELAY_PUMP_BOTTOM) ? "ON" : "OFF");

        Serial.println();
    }
}