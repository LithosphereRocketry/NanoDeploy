#include <OneWire.h>

/*
Simplified OneWire to UART/CDC bridge.

-------------------------------------------------------------------------------

Command format:

All commands are formed from a mode tag (one byte), a length (one byte), a
command byte (one byte), and a string of data. The data string may be between 0
and 255 bytes, not including the command byte.

Tags are as follows:

Read tag: tag byte 0
Sends the command byte, then receives (length) bytes from the bus and sends
them back on the serial port.

Write tag: tag byte 1
Sends the command byte followed by the data string to the bus.

Scan tag: tag byte 2
Command byte and length ignored. Performs a scan of the bus. If a device is
present, returns a nonzero byte, followed by the 8-byte address of the device.
If no device is present, returns a zero byte.

Alarm scan tag: tag byte 3
Command byte and length ignored. Performs a scan of the bus with alarm flag
filter set. If a device is present, returns a nonzero byte, followed by the
8-byte address of the device. If no device is present, returns a zero byte.
*/

enum {
  TAG_READ = 0,
  TAG_WRITE = 1,
  TAG_SCAN = 2,
  TAG_ALARM = 3
};

OneWire owi(14);

uint8_t data_buf[256];

const uint8_t null_rom[8] = {0, 0, 0, 0, 0, 0, 0, 0};

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);

  while(1) {
    owi.reset_search();
    owi.search(data_buf);
    delay(100);
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }
}

void loop() {
  while(!Serial.available());
  digitalWrite(LED_BUILTIN, HIGH);
  uint8_t tag = Serial.read();
  while(!Serial.available());
  uint8_t len = Serial.read();
  while(!Serial.available());
  uint8_t cmd = Serial.read();

  switch(tag) {
    case TAG_READ:
      owi.write(cmd);
      owi.read_bytes(data_buf, len);
      Serial.write(data_buf, len);
      break;
    case TAG_WRITE:
      Serial.readBytes(data_buf, len);
      owi.write(cmd);
      owi.write_bytes(data_buf, len);
      break;
    case TAG_SCAN:
      if(owi.search(data_buf, true)) {
        Serial.write((uint8_t) 1);
        Serial.write(data_buf, 8);
      } else {
        Serial.write((uint8_t) 0);
      }
      break;
    case TAG_ALARM:
      if(owi.search(data_buf, false)) {
        Serial.write((uint8_t) 1);
        Serial.write(data_buf, 8);
      } else {
        Serial.write((uint8_t) 0);
      }
      break;
  }
  digitalWrite(LED_BUILTIN, LOW);
}
