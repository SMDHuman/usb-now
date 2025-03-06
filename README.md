# USB-Now

USB-Now is an ESP32-based solution consisting of a firmware and a Python module that enables ESP-NOW communication through USB. It requires an ESP32 device to act as a USB adapter, allowing your computer to communicate with other ESP-NOW enabled devices.

The project provides:
- A firmware for the ESP32 USB adapter
- A Python monitoring tool (`usbnow-monitor`)
- A Python module for device communication and configuration

This project is a redesigned implementation of [ESP-NOW_USB_Receiver](https://github.com/SMDHuman/ESP-NOW_USB_Receiver), focusing on providing comprehensive access to ESP-NOW functions and essential WiFi features for more efficient control and communication.

## Python Script
WIP...

## Implementation Development Table

| Function | Implemented | Tested | Works |
|----------|------------|---------|-------|
| esp_now_init() | ✔ | X | X |
| esp_now_deinit() | ✔ | X | X |
| esp_now_get_version() | ✔ | X | X |
| esp_now_register_recv_cb() | ✔ | X | X |
| esp_now_unregister_recv_cb() | ✔ | X | X |
| esp_now_register_send_cb() | ✔ | X | X |
| esp_now_unregister_send_cb() | ✔ | X | X |
| esp_now_send() | ✔ | X | X |
| esp_now_add_peer() | ✔ | X | X |
| esp_now_del_peer() | ✔ | X | X |
| esp_now_mod_peer() | ✔ | X | X |
| esp_wifi_config_espnow_rate() | ✔ | X | X |
| esp_now_get_peer() | ✔ | X | X |
| esp_now_fetch_peer() | ✔ | X | X |
| esp_now_is_peer_exist() | ✔ | X | X |
| esp_now_get_peer_num() | ✔ | X | X |
| esp_now_set_pmk() | ✔ | X | X |
| esp_now_set_wake_window() | ✔ | X | X |
| WiFi.macAddress() | ✔ | X | X |