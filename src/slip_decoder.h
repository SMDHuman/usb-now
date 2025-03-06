//-----------------------------------------------------------------------------
// File: slip_decoder.h
// Last modified: 06/03/2025
//-----------------------------------------------------------------------------
#ifndef SLIP_DECODER_H
#define SLIP_DECODER_H

//-----------------------------------------------------------------------------
#include <Arduino.h>

#define S_END 0xC0
#define S_ESC 0xDB
#define S_ESC_END 0xDC
#define S_ESC_ESC 0xDD

//#define CHECKSUM_ENABLE

#define slip_buffer_size 2048

//-----------------------------------------------------------------------------
void slip_init();
void slip_task();
void slip_push(uint8_t data);
uint8_t slip_is_ready();
size_t slip_package_size();
uint8_t* slip_get_package();
void slip_reset();

    //-----------------------------------------------------------------------------
#endif