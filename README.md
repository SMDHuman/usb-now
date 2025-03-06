# USB-Now

USB-Now is an ESP32-based solution consisting of a firmware and a Python module that enables ESP-NOW communication through USB. It requires an ESP32 device to act as a USB adapter, allowing your computer to communicate with other ESP-NOW enabled devices.

The project provides:
- A firmware for the ESP32 USB adapter
- A Python monitoring tool (`usbnow-monitor`)
- A Python module for device communication and configuration

This project is a redesigned implementation of [ESP-NOW_USB_Receiver](https://github.com/SMDHuman/ESP-NOW_USB_Receiver), focusing on providing comprehensive access to ESP-NOW functions and essential WiFi features for more efficient control and communication.

## Implemented ESP-Now Functions

- [ ] esp_now_init()
- [ ] esp_now_deinit()
- [ ] esp_now_get_version()
- [ ] esp_now_register_recv_cb()
- [ ] esp_now_unregister_recv_cb()
- [ ] esp_now_register_send_cb()
- [ ] esp_now_unregister_send_cb()
- [ ] esp_now_send()
- [ ] esp_now_add_peer()
- [ ] esp_now_del_peer()
- [ ] esp_now_mod_peer()
- [ ] esp_wifi_config_espnow_rate()
- [ ] esp_now_get_peer()
- [ ] esp_now_fetch_peer()
- [ ] esp_now_is_peer_exist()
- [ ] esp_now_get_peer_num()
- [ ] esp_now_set_pmk()
- [ ] esp_now_set_wake_window()