//-----------------------------------------------------------------------------
// File: command_handler.h
// Last edit: 06/03/2025
//-----------------------------------------------------------------------------
#ifndef COMMAND_HANDLER_H
#define COMMAND_HANDLER_H
#include <Arduino.h>

//-----------------------------------------------------------------------------
// esp-now command list
enum CMD_TYPE_E{
    CMD_INIT,
    CMD_DEINIT,
    CMD_GET_VERSION,
    CMD_SEND,
    CMD_ADD_PEER,
    CMD_DEL_PEER,
    CMD_MOD_PEER,
    CMD_CONFIG_ESPNOW_RATE,
    CMD_GET_PEER,
    CMD_FETCH_PEER,
    CMD_IS_PEER_EXIST,
    CMD_GET_PEER_NUM,
    CMD_SET_PMK,
    CMD_SET_WAKE_WINDOW,
    CMD_GET_DEVICE_MAC,
};

// esp-now response list
enum RESP_TYPE_E{
    RESP_OK,
    RESP_ERROR,
    RESP_VERSION,
    RESP_PEER,
    RESP_PEER_ADDR,
    RESP_PEER_EXIST,
    RESP_PEER_NUM,
    RESP_RECV_CB,
    RESP_SEND_CB,
    RESP_ERROR_LEN,
    RESP_ERROR_UNKNOWN,
};

//-----------------------------------------------------------------------------
void CMD_init();
void CMD_task();
void CMD_parse(uint8_t *msg_data, uint32_t package_size);

#endif