//------------------------------------------------------------------------------
// File: display_handler.h
// Created: 12/3/2025
// Last modified: 12/3/2025
//------------------------------------------------------------------------------
#ifndef DISPLAY_HANDLER_H
#define DISPLAY_HANDLER_H
#include <Arduino.h>

//-----------------------------------------------------------------------------
void display_init();
void display_task();
void display_led_blink(uint32_t _close_delay);

#endif