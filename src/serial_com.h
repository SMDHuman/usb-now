//-----------------------------------------------------------------------------
// File: serial_com.h
// Last edit: 06/03/2025
//-----------------------------------------------------------------------------
#ifndef SERIAL_COM_H
#define SERIAL_COM_H
#include <Arduino.h>
#include "esp_camera.h"
#include "config.h"

//-----------------------------------------------------------------------------
#define BAUDRATE 115200
#define S_MAX_PACKAGE 1024

#define S_END 0xC0
#define S_ESC 0xDB
#define S_ESC_END 0xDC
#define S_ESC_ESC 0xDD

//-----------------------------------------------------------------------------
void serial_init();
void serial_task();
void serial_send_slip(uint8_t* buf, size_t len);
void serial_send_slip(uint8_t data);
void serial_send_slip(String data);
void serial_end_slip();
uint32_t serial_get_checksum();

//-----------------------------------------------------------------------------
#endif
