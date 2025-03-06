// Creator: Halid Y. 
// Github: SMDHuman
// Created: 06/03/2025
// Last modified: 06/03/2025
/* Description: ---------------------------------------------------------------
  * USB-Now is an ESP32-based solution consisting of a firmware and a Python 
  * module that enables ESP-NOW communication through USB. It requires an ESP32 
  * device to act as a USB adapter, allowing your computer to communicate with 
  * other ESP-NOW enabled devices.
  * -------------------------------------------------------------------------*/

#include <Arduino.h>
#include "serial_com.h"

void setup() {
  serial_init();
}

void loop() {
  serial_task();
}