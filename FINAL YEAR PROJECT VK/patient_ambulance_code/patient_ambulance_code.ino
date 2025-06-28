#include <SoftwareSerial.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// DHT Sensor Setup
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// ECG & Pulse Sensor Pins
#define ECG_PIN A1
#define PULSE_PIN A2

// LCD Display (I2C Address: 0x27)
LiquidCrystal_I2C lcd(0x27, 16, 2);

unsigned long previousMillis = 0; 
int displayState = 0;  // 0 = Temp & Hum, 1 = ECG & Pulse

void setup() {
    Serial.begin(115200);   // For Serial Monitor
    dht.begin();
    lcd.init();
    lcd.backlight();

    Serial.println("System Initialized...");
}

void loop() {
    unsigned long currentMillis = millis();

    // Read sensor values
    float temp = dht.readTemperature();
    float humidity = dht.readHumidity();
    int ecg = analogRead(ECG_PIN);
    int pulseValue = analogRead(PULSE_PIN);
    int pulseRate = map(pulseValue, 0, 1023, 40, 180);  // Convert to BPM

    // Toggle LCD Display every 3 seconds
    if (currentMillis - previousMillis >= 3000) {
        previousMillis = currentMillis;
        lcd.clear();
        if (displayState == 0) {
            lcd.setCursor(0, 0);
            lcd.print("Temp: " + String(temp) + "C");
            lcd.setCursor(0, 1);
            lcd.print("Hum: " + String(humidity) + "%");
            displayState = 1;
        } else {
            lcd.setCursor(0, 0);
            lcd.print("ECG: " + String(ecg));
            lcd.setCursor(0, 1);
            lcd.print("Pulse: " + String(pulseRate) + " BPM");
            displayState = 0;
        }
    }

    // Send Data to Python Script (For ThingSpeak)
    Serial.print(temp); Serial.print(",");
    Serial.print(humidity); Serial.print(",");
    Serial.print(ecg); Serial.print(",");
    Serial.println(pulseRate);

    delay(500);  // Small delay to avoid rapid looping
}
