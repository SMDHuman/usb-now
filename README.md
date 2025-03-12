# USB-Now

USB-Now is an ESP32-based solution consisting of a firmware and a Python module that enables ESP-NOW communication through USB. It requires an ESP32 device to act as a USB adapter, allowing your computer to communicate with other ESP-NOW enabled devices.

The project provides:
- A firmware for the ESP32 USB adapter
- A Python monitoring tool (`usbnow-monitor.py`)
- A Python module for device communication and configuration (`usbnow.py`)

> Note: All Python tools are located in the `/scripts` folder.

This project is a redesigned implementation of [ESP-NOW_USB_Receiver](https://github.com/SMDHuman/ESP-NOW_USB_Receiver), focusing on providing comprehensive access to ESP-NOW functions and essential WiFi features for more efficient control and communication.

## ESP32 Setup

### PlatformIO Configuration

1. Install PlatformIO in VSCode
2. Create a new project or clone this repository
3. Configure your `platformio.ini` like in the example: 
    ```ini
    [env:esp32]
    platform = espressif32
    board = esp32dev
    framework = arduino
    monitor_speed = 115200
    build_flags = 
        -DCORE_DEBUG_LEVEL=0
        -DCONFIG_ESP_NOW_ENABLE
    ```

### Supported ESP32 Boards

The firmware has been tested on:
- nodemcu-32s
- esp32-s3 

Note: Any ESP32 board with USB-UART bridge should work.

### Hardware Setup

1. Connect your ESP32 to your computer via USB
2. Identify the correct COM port:
    - Windows: Check Device Manager under "Ports (COM & LPT)"
    - Linux: Run `ls /dev/tty*` (usually appears as `/dev/ttyUSB0` or `/dev/ttyACM0`)
    - macOS: Run `ls /dev/tty.*` (usually appears as `/dev/tty.usbserial-*` or `/dev/tty.SLAB_USBtoUART`)
3. Upload the project:
    - Connect your ESP32 board to your computer
    - Open VS Code with PlatformIO extension installed
    - Click on the PlatformIO icon in the sidebar
    - Under "Project Tasks", expand your project
    - Click on "Upload" to compile and flash the code to your ESP32
    - Wait for the upload process to complete (you can monitor progress in the terminal)

    Note: Make sure you have selected the correct COM port in platformio.ini and your board is in bootloader mode (most boards enter this mode automatically, but some might require pressing the BOOT button while connecting)

### Troubleshooting

- If upload fails, try holding the BOOT button while initiating the upload
- Ensure proper USB drivers are installed for your ESP32 board
- For permission issues on Linux, add your user to the `dialout` group:
  ```bash
  sudo usermod -a -G dialout $USER
  ```

## Python Module Usage

The `usbnow` module provides a simple interface to communicate with ESP-NOW devices through USB.

### Example: Receiving Data

```python
from usbnow import USBNow

def recv_cb(addr: bytes, data: bytes):
    print("From:", addr)
    print(data)

# Initialize with your COM port
usbnow = USBNow('COM3')
usbnow.init()
usbnow.register_recv_cb(recv_cb)

input("Press Enter to Exit...")
usbnow.deinit()
```

### Example: Sending Data

```python
from usbnow import USBNow, MAC

# Initialize with your COM port
usbnow = USBNow('COM3')
usbnow.init()

# Add peer device
peer_mac = MAC("AA:BB:CC:DD:EE:FF")
usbnow.add_peer(peer_mac)

# Send message
message = b"Hello ESP-NOW!"
usbnow.send(peer_mac, message)
usbnow.deinit()
```

## Error Handling

The module return `None` if it has no error. But otherwise errors usualy returns as `str`, if it does not effect the usage. 

```python
res = usbnow.send(peer_mac, data)
if(res):
    print("Error While Sending:", res)
```

## References

- [ESP-NOW Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_now.html)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

