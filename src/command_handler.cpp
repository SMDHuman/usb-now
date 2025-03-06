//-----------------------------------------------------------------------------
// File: command_handler.cpp
// Last modified: 06/03/2025
//-----------------------------------------------------------------------------
#include "command_handler.h"
#include <Arduino.h>
#include <esp_now.h>
#include <WiFi.h>
#include "serial_com.h"

//-----------------------------------------------------------------------------
static esp_now_peer_info_t peer_info;
static void esp_now_recv_cb(const uint8_t *mac_addr, const uint8_t *data, int data_len);
static void esp_now_send_cb(const uint8_t *mac_addr, esp_now_send_status_t status);  

//-----------------------------------------------------------------------------
void CMD_init(){
}
//-----------------------------------------------------------------------------
void CMD_task(){
}
//-----------------------------------------------------------------------------
void CMD_parse(uint8_t *msg_data, uint32_t len){
  static uint8_t *peer_addr;
  static esp_err_t res = ESP_OK;
  CMD_TYPE_E cmd = (CMD_TYPE_E)msg_data[0];
  // Reuse the global peer_info instead of creating a local one
  switch(cmd){
    case CMD_INIT: {
      WiFi.mode(WIFI_MODE_STA);
      res = esp_now_init();
      esp_now_register_recv_cb(esp_now_recv_cb);
      esp_now_register_send_cb(esp_now_send_cb);
      break;
    }
    case CMD_DEINIT: {
      esp_now_unregister_recv_cb();
      esp_now_unregister_send_cb();
      res = esp_now_deinit();
      WiFi.mode(WIFI_MODE_NULL);
      break;
    }
    case CMD_GET_VERSION: {
      serial_send_slip(RESP_VERSION);
      uint32_t ESP_NOW_VERSION;
      res = esp_now_get_version(&ESP_NOW_VERSION);
      serial_send_slip(ESP_NOW_VERSION);
      serial_end_slip();
      break;
    }
    case CMD_SEND: {
      if(len < 8){
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      if((len - 7) > ESP_NOW_MAX_DATA_LEN) {
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      peer_addr = msg_data + 1;
      uint8_t *data = msg_data + 7;
      uint8_t data_len = len - 7;
      res = esp_now_send(peer_addr, data, data_len);
      break;
    }
    case CMD_ADD_PEER:
    case CMD_MOD_PEER: {
      if(len < 9){
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      memcpy(peer_info.peer_addr, msg_data+1, 6);
      peer_info.channel = msg_data[7];
      peer_info.encrypt = msg_data[8];
      peer_info.ifidx = WIFI_IF_STA;  // Set default interface
      peer_info.priv = NULL;          // Initialize private data as NULL
      memset(peer_info.lmk, 0, ESP_NOW_KEY_LEN); // Initialize LMK
      res = (cmd == CMD_ADD_PEER) ? esp_now_add_peer(&peer_info) : esp_now_mod_peer(&peer_info);
      break;
    }
    case CMD_DEL_PEER: {
      if(len < 7){
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      peer_addr = msg_data+1;
      res = esp_now_del_peer(peer_addr);
      break;
    }
    case CMD_CONFIG_ESPNOW_RATE: {
      if(len < 3){
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      res = esp_wifi_config_espnow_rate((wifi_interface_t)msg_data[1], (wifi_phy_rate_t)msg_data[2]);
      break;
    }
    case CMD_GET_PEER: {
      if(len < 7){
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      res = esp_now_get_peer(msg_data+1, &peer_info);
      if(res == ESP_OK) {
        serial_send_slip(RESP_PEER);
        serial_send_slip(peer_info.peer_addr, 6);
        serial_send_slip(peer_info.channel);
        serial_send_slip(peer_info.encrypt);
        serial_end_slip();
      }
      break;
    }
    case CMD_FETCH_PEER: {
      if(len < 2){
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      res = esp_now_fetch_peer(msg_data[1], &peer_info);
      if(res == ESP_OK){
        serial_send_slip(RESP_PEER);
        serial_send_slip(peer_info.peer_addr, 6);
        serial_send_slip(peer_info.channel);
        serial_send_slip(peer_info.encrypt);
        serial_end_slip();
      }
      break;
    }
    case CMD_IS_PEER_EXIST: {
      if(len < 7){
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      serial_send_slip(RESP_PEER_EXIST);
      peer_addr = msg_data+1;
      serial_send_slip(esp_now_is_peer_exist(peer_addr));
      serial_end_slip();
      break;
    }
    case CMD_GET_PEER_NUM: {
      esp_now_peer_num_t peer_num;
      res = esp_now_get_peer_num(&peer_num);
      if(res == ESP_OK){
        serial_send_slip(RESP_PEER_NUM);
        serial_send_slip(peer_num.total_num);
        serial_send_slip(peer_num.encrypt_num);
        serial_end_slip();
      }
      break;
    }
    case CMD_SET_PMK: {
      if(len != (ESP_NOW_KEY_LEN + 1)){  // PMK length + command byte
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      res = esp_now_set_pmk(msg_data+1);
      break;
    }
    case CMD_SET_WAKE_WINDOW: {
      if(len < 3){
        serial_send_slip(RESP_ERROR_LEN);
        serial_end_slip();
        return;
      }
      uint16_t window = (msg_data[1] << 8) | msg_data[2];
      res = esp_now_set_wake_window(window);
      break;
    }
    case CMD_GET_DEVICE_MAC: {
      serial_send_slip(RESP_PEER_ADDR);
      uint8_t mac[6];
      WiFi.macAddress(mac);
      serial_send_slip(mac, 6);
      serial_end_slip();
      break;
    }
    default:{
      serial_send_slip(RESP_ERROR_UNKNOWN);
      serial_end_slip();
      break;
    }
  }
  // Send response
  if(res == ESP_OK){
    serial_send_slip(RESP_OK);
  }
  else{
    serial_send_slip(RESP_ERROR);
    serial_send_slip(res);
  }
  serial_end_slip();
}

//-----------------------------------------------------------------------------
static void esp_now_recv_cb(const uint8_t *mac_addr, const uint8_t *data, int data_len){
  serial_send_slip(RESP_RECV_CB);
  serial_send_slip((uint8_t*)mac_addr, 6);
  serial_send_slip((uint8_t*)data, data_len);
  serial_end_slip();
}
//-----------------------------------------------------------------------------
static void esp_now_send_cb(const uint8_t *mac_addr, esp_now_send_status_t status){
  serial_send_slip(RESP_SEND_CB);
  serial_send_slip((uint8_t*)mac_addr, 6);
  serial_send_slip(status);
  serial_end_slip();
}
