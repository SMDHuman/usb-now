from ..scripts.usbnow import MAC, USBNow
import time

def send_cb(addr: bytes, status: str):
    mac = ':'.join([f"{x:02X}" for x in addr])
    print(f"[{mac}] {status}")

def recv_cb(addr: bytes, data: bytes):
    mac = ':'.join([f"{x:02X}" for x in addr])
    print(f"[{mac}] {data}")

esp = USBNow("COM11", print_error=True)
esp.init()

#esp.register_send_cb(send_cb)
esp.register_recv_cb(recv_cb)

mac = esp.get_mac()
print("devices mac address: ", mac )

# Send a test message
addr = MAC("70:04:1D:A8:82:58")
esp.add_peer(addr)
esp.send(addr, b"Hello, World!")
for i in range(10):
    esp.send(addr, str(i).encode())
    time.sleep(0.5)
esp.deinit()
