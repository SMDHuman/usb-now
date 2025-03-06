//-----------------------------------------------------------------------------
// File: serial_com.cpp
// Last modified: 06/03/2025
//-----------------------------------------------------------------------------
#include <Arduino.h>
#include "serial_com.h"
#include "slip_decoder.h"
#include "command_handler.h"

static uint32_t checksum = 0;

//-----------------------------------------------------------------------------
// Initialize the serial communication with the specified baud rate
void serial_init(){
  Serial.begin(BAUDRATE);
}

//-----------------------------------------------------------------------------
// Handle serial communication tasks, including reading and processing commands
void serial_task(){
  if(Serial.available()){
    slip_push(Serial.read()); 
  }
  if(slip_is_ready()){
    size_t package_len = slip_package_size();
    uint8_t *package = slip_get_package();
    CMD_parse(package, package_len);
    slip_reset();
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
// Send a byte using the SLIP protocol
void serial_send_slip(uint8_t data){
  checksum += data;
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
// Send a string using the SLIP protocol
void serial_send_slip(String data){
  for(size_t i = 0; i < data.length(); i++){
    serial_send_slip(data[i]);
  }
}
//-----------------------------------------------------------------------------
// Send the end of the slip package
void serial_end_slip(){
  checksum = 0;
  Serial.write(S_END);
}
//-----------------------------------------------------------------------------
// Get total checksum
uint32_t serial_get_checksum(){
  return checksum;
}