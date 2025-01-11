#include <OneWire.h>

OneWire owi(14);

uint8_t addr[8];

void setup() {
  Serial.begin(9600);

  while(!owi.search(addr)) {
    Serial.println("No devices found");
    delay(1000);
  }

  for(int i = 0 ; i < 8; i++) {
    Serial.printf("%hx ", addr[i]);
    Serial.println();
  }
}

void loop() {
  // put your main code here, to run repeatedly:

}
