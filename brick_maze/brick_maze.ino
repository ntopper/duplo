int SPEAKER = 10;
int LEFT = 8;
int RIGHT = 9;

int mode = 0;

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete


void setup()
{ // initialize serial:
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
  delay(500);
}


//Activates right feeder
void feed_right() { //activates right feeder

  digitalWrite(RIGHT, LOW);
  delay(1000);
  digitalWrite(RIGHT, HIGH);
  delay(500);
}


//Intiates countdown with related frequency
boolean countdown(unsigned int sec)

{
  long finish = millis() + sec * 1000;
  unsigned int freq = 0;

  while (millis() < finish)
  {
    switch(mode) {
      
      case 0:
        freq = sweep50(finish-millis(), sec);
        break;
      case 1:
        freq = sweep250(finish-millis(), sec);
        break;
      case 2:
        freq = step250(finish-millis(), sec);
        break;
    }

    if (Serial.available()) {
      noTone(SPEAKER);
      return false;
    }

    tone(SPEAKER, freq);
  }
  noTone(SPEAKER);
  return true;
}

unsigned int sweep250(unsigned int t, unsigned int n) {
 return (t / 1000.0) * 250 + 1000;
}

unsigned int step250 (unsigned int t, unsigned int n){
 return (t / 1000) * 250 + 1000;
}

unsigned int sweep50(unsigned int t, unsigned int n) {
 return map(t,  0, n * 1000, 50, n * 50);
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
  int maxIndex = data.length() - 1;

  for (int i = 0; i <= maxIndex && found <= index; i++) {
    if (data.charAt(i) == separator || i == maxIndex) {
      found++;
      strIndex[0] = strIndex[1] + 1;
      strIndex[1] = (i == maxIndex) ? i + 1 : i;
    }
  }
  return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

void run(String command) {

  // isolate function
  String f = getValue(command, ' ', 0);

  // isolate paramater
  int param = getValue(command, ' ', 1).toInt();
  int param2 = getValue(command, ' ', 2).toInt();

  if (f == "feed_right") {
    Serial.println("BEEEeeeeewwww");
    if (countdown(param)) {
      while (param2) {
        Serial.println("feeding: right");
        feed_right();
        param2 -= 1;
      }
    }
    else {
      Serial.println("interupted");
    }
  }

  if (f == "feed_left") {
    Serial.println("BEEEeeeeewwww");

    if (countdown(param)) {
      while (param2) {
        Serial.println("feeding: left");
        feed_left();
        param2 -= 1;
      }
    }
    else {
      Serial.println("interupted");
    }
  }
  
  if (f == "set_mode") {
   mode = param; 
  }
}
