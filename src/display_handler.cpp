//------------------------------------------------------------------------------
// File: display_handler.cpp
// Created: 12/3/2025
// Last modified: 12/3/2025
//------------------------------------------------------------------------------

#include "display_handler.h"

static uint32_t last_led_on = 0;
static uint32_t close_delay = 100;

// Initialize the LED pin
void display_init(){
  pinMode(LED_BUILTIN, OUTPUT);
}

// Turn off the LED after a delay
void display_task(){
  if(millis() - last_led_on > close_delay){
    digitalWrite(LED_BUILTIN, LOW);
  }
}

// Blink the LED for a short duration
void display_led_blink(uint32_t _close_delay){
  close_delay = _close_delay;
  digitalWrite(LED_BUILTIN, HIGH);
  last_led_on = millis();
}