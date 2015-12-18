int SPEAKER = 10;    // Ouout pins
int LEFT =8;   
int RIGHT=9;   


String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete


void setup()
{   // initialize serial:
    Serial.begin(9600);     //Port for commands/confirmation
    //Serial2.begin(9600);    //Port for data logging
    // reserve 200 bytes for the inputString:
    inputString.reserve(200);
    
    digitalWrite(LEFT, HIGH);
    digitalWrite(RIGHT, HIGH);
    
    pinMode(SPEAKER, OUTPUT);
    pinMode(LEFT, OUTPUT);
    pinMode(RIGHT, OUTPUT);
}

//Activates left feeder
void feed_left() {    
       
      digitalWrite(LEFT, LOW);
      delay(1000);
      digitalWrite(LEFT, HIGH);
     
     
    }


//Activates right feeder
void feed_right() { //activates right feeder
  
      digitalWrite(RIGHT, LOW);
      delay(1000);
      digitalWrite(RIGHT, HIGH);
    }

  
//Intiates countdown with related frequency  
void countdown(int time)

 {    
  
  int freq = time*50;
   
   while( freq > 0) 
      {
          tone(SPEAKER, freq);
          delay(1000);
          freq -= 50;
      }
    }
        noTone(SPEAKER);
}

void loop()

{  
   if (stringComplete) {
        Serial.println(inputString);
        run(inputString);
        // clear the string:
        inputString = "";
        stringComplete = false;
    }
  
}

void serialEvent() {
    while (Serial.available()) {
        // get the new byte:
        char inChar = (char)Serial.read(); 
        // add it to the inputString:
        inputString += inChar;
        // if the incoming character is a newline, set a flag
        // so the main loop can do something about it:
        if (inChar == '\n') {
            stringComplete = true;
        }
    }
}

String getValue(String data, char separator, int index) {
    int found = 0;
    int strIndex[] = {0, -1};
    int maxIndex = data.length()-1;

    for(int i=0; i<=maxIndex && found<=index; i++) {
        if(data.charAt(i)==separator || i==maxIndex) {
            found++;
            strIndex[0] = strIndex[1]+1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
    }
    return found>index ? data.substring(strIndex[0], strIndex[1]) : "";
}



void run(String command) {

    // isolate function
    String f = getValue(command, ' ', 0);
  
    // isolate paramater
    int param = getValue(command, ' ', 1).toInt();
    //Serial.println("Function: " + f);
    //Serial.println("Paramater: " + String(param));
  
    if (f == "feed_right") {
        Serial.println("feed right");
        feed_right();
        // send dose to smoke box
        // SmokeDelivery.send_dose(param);
    } 
    
       if (f == "feed_left") {
        Serial.println("feed left");
        feed_left();
        // send dose to smoke box
        // SmokeDelivery.send_dose(param);
    }
    
    if (f == "countdown") {
      Serial.println("countdown " + String(param) + " seconds");
      countdown(param);
    }
       
} 
   