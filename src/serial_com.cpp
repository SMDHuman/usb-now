//-----------------------------------------------------------------------------
// File: serial_com.cpp
// Last modified: 27/03/2025
//-----------------------------------------------------------------------------
#include <Arduino.h>
#include "serial_com.h"
#include "command_handler.h"

#define SLIP_IMPLEMENTATION
#include "p_slip.h"

static uint32_t checksum = 0;
static uint8_t rx_slip_buffer[2028];

//-----------------------------------------------------------------------------
// Initialize the serial communication with the specified baud rate
void serial_init(){
  Serial.begin(BAUDRATE);
  slip_init(rx_slip_buffer, sizeof(rx_slip_buffer));
}

//-----------------------------------------------------------------------------
// Handle serial communication tasks, including reading and processing commands
void serial_task(){
  if(Serial.available()){
    slip_push(rx_slip_buffer, Serial.read()); 
  }
  if(slip_is_ready(rx_slip_buffer)){
    size_t package_len = slip_get_size(rx_slip_buffer);
    uint8_t *package = slip_get_buffer(rx_slip_buffer);
    CMD_parse(package, package_len);
    slip_reset(rx_slip_buffer);
  }
}
//-----------------------------------------------------------------------------
// Send a byte using the SLIP protocol
void serial_send_slip(uint8_t data){
  checksum += data + 1;
  if(data == S_END){
    Serial.write(S_ESC);
    Serial.write(S_ESC_END);
  }
  else if(data == S_ESC){
    Serial.write(S_ESC);
    Serial.write(S_ESC_ESC);
  }
  else{
    Serial.write(data);
  }
}
//-----------------------------------------------------------------------------
// Send a buffer using the SLIP protocol
void serial_send_slip(uint8_t* buf, size_t len){
  for(size_t i = 0; i < len; i++){
    serial_send_slip(buf[i]);
  }
}
//-----------------------------------------------------------------------------
// Send an unsigned integer using the SLIP protocol
void serial_send_slip(uint data){
  serial_send_slip((uint8_t*)&data, sizeof(data));
}
//-----------------------------------------------------------------------------
// Send an integer using the SLIP protocol
void serial_send_slip(int data){
  serial_send_slip((uint8_t*)&data, sizeof(data));
}
//-----------------------------------------------------------------------------
// Send a char using the SLIP protocol
void serial_send_slip(char data){
  serial_send_slip((uint8_t)data);
}
//-----------------------------------------------------------------------------
// Send a string using the SLIP protocol
void serial_send_slip(String data){
  for(size_t i = 0; i < data.length(); i++){
    serial_send_slip(data[i]);
  }
}
//-----------------------------------------------------------------------------
// Send the end of the slip package
void serial_end_slip(){
  uint32_t final_checksum = checksum;
  serial_send_slip(final_checksum);
  Serial.write(S_END);
  checksum = 0;
}
