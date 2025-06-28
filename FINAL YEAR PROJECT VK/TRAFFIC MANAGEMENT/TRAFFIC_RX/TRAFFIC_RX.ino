#define RF_SIGNAL_1 2  
#define RF_SIGNAL_2 3  
#define RF_SIGNAL_3 4  
#define RF_SIGNAL_4 5  

#define GREEN1 8
#define YELLOW1 7
#define RED1 6

#define GREEN2 11
#define YELLOW2 10
#define RED2 9

#define GREEN3 A0
#define YELLOW3 13
#define RED3 12

#define GREEN4 A3
#define YELLOW4 A2
#define RED4 A1

#define BUZZER A4  

bool isEmergencyActive = false;

void setup() {
    pinMode(RF_SIGNAL_1, INPUT_PULLUP);
    pinMode(RF_SIGNAL_2, INPUT_PULLUP);
    pinMode(RF_SIGNAL_3, INPUT_PULLUP);
    pinMode(RF_SIGNAL_4, INPUT_PULLUP);

    pinMode(GREEN1, OUTPUT);
    pinMode(YELLOW1, OUTPUT);
    pinMode(RED1, OUTPUT);
    pinMode(GREEN2, OUTPUT);
    pinMode(YELLOW2, OUTPUT);
    pinMode(RED2, OUTPUT);
    pinMode(GREEN3, OUTPUT);
    pinMode(YELLOW3, OUTPUT);
    pinMode(RED3, OUTPUT);
    pinMode(GREEN4, OUTPUT);
    pinMode(YELLOW4, OUTPUT);
    pinMode(RED4, OUTPUT);
    pinMode(BUZZER, OUTPUT);

    resetSignals();
}

void loop() {
    // Check emergency buttons
    if (digitalRead(RF_SIGNAL_1) == LOW) { handleEmergency(GREEN1, RED1, YELLOW1); }
    else if (digitalRead(RF_SIGNAL_2) == LOW) { handleEmergency(GREEN2, RED2, YELLOW2); }
    else if (digitalRead(RF_SIGNAL_3) == LOW) { handleEmergency(GREEN3, RED3, YELLOW3); }
    else if (digitalRead(RF_SIGNAL_4) == LOW) { handleEmergency(GREEN4, RED4, YELLOW4); }
    else {
        isEmergencyActive = false; // Reset flag when no button is pressed
        runNormalTraffic();
    }
}

void handleEmergency(int green, int red, int yellow) {
    if (isEmergencyActive) return; // Prevent multiple triggers
    isEmergencyActive = true;

    resetSignals();  
    digitalWrite(red, LOW);  
    digitalWrite(yellow, LOW);
    digitalWrite(green, HIGH);  
    ambulanceSound();  
    delay(60000);  // 1-minute green
    digitalWrite(green, LOW);
    digitalWrite(yellow, HIGH);  
    delay(2000);
    digitalWrite(yellow, LOW);
    digitalWrite(red, HIGH);
}

void runNormalTraffic() {
    int signals[4][3] = {{GREEN1, YELLOW1, RED1}, {GREEN2, YELLOW2, RED2}, {GREEN3, YELLOW3, RED3}, {GREEN4, YELLOW4, RED4}};

    for (int i = 0; i < 4; i++) {
        if (isEmergencyActive || digitalRead(RF_SIGNAL_1) == LOW || digitalRead(RF_SIGNAL_2) == LOW ||
            digitalRead(RF_SIGNAL_3) == LOW || digitalRead(RF_SIGNAL_4) == LOW) {
            return;  // Stop normal cycle if a button is pressed
        }
        
        digitalWrite(signals[i][2], LOW);
        digitalWrite(signals[i][0], HIGH);
        delay(6000);
        digitalWrite(signals[i][0], LOW);
        digitalWrite(signals[i][1], HIGH);
        delay(2000);
        digitalWrite(signals[i][1], LOW);
        digitalWrite(signals[i][2], HIGH);
    }
}

void resetSignals() {
    digitalWrite(GREEN1, LOW);
    digitalWrite(YELLOW1, LOW);
    digitalWrite(RED1, HIGH);
    digitalWrite(GREEN2, LOW);
    digitalWrite(YELLOW2, LOW);
    digitalWrite(RED2, HIGH);
    digitalWrite(GREEN3, LOW);
    digitalWrite(YELLOW3, LOW);
    digitalWrite(RED3, HIGH);
    digitalWrite(GREEN4, LOW);
    digitalWrite(YELLOW4, LOW);
    digitalWrite(RED4, HIGH);
    noTone(BUZZER);
}

void ambulanceSound() {
    for (int i = 0; i < 10; i++) {
        tone(BUZZER, 1000);
        delay(500);
        tone(BUZZER, 500);
        delay(500);
    }
    noTone(BUZZER);
}
