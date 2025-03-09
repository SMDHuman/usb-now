import serial
import sys, os
import threading
import serial.tools.list_ports
import time

# USBNow Response Codes
class RESP:
    OK = 0
    ERROR = 1
    VERSION = 2
    PEER = 3
    PEER_ADDR = 4
    PEER_EXIST = 5
    PEER_NUM = 6
    RECV_CB = 7
    SEND_CB = 8
    ERROR_LEN = 9
    ERROR_UNKNOWN = 10

# USBNow Commands
class CMD:
    INIT = 0
    DEINIT = 1
    GET_VERSION = 2
    SEND = 3
    ADD_PEER = 4
    DEL_PEER = 5
    MOD_PEER = 6
    CONFIG_ESPNOW_RATE = 7
    GET_PEER = 8
    FETCH_PEER = 9
    IS_PEER_EXIST = 10
    GET_PEER_NUM = 11
    SET_PMK = 12
    SET_WAKE_WINDOW = 13
    GET_DEVICE_MAC = 14

# Slip constants
SLIP_END = 0xC0
SLIP_ESC = 0xDB
SLIP_ESC_END = 0xDC
SLIP_ESC_ESC = 0xDD

class USBNow:
    def __init__(self, port: str, baudrate: int = 115200, timeout: int = 1):
        self.port: str = port
        self.baudrate: int = baudrate
        self.timeout: int = timeout
        self.receive_buffer: list[bytearray] = []
        self.receive_cb: callable = None
        self.send_cb: callable = None
        self.can_close = False
        self.waiting_response: RESP = None
        #...
        self.serial: serial.Serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self.slip_decoder = SLIP()
        self.receive_thread = threading.Thread(target=self.rx_loop)
        self.receive_thread_running = True
        self.receive_thread.start()

    def list_devices(self = None) -> list[str]:
        ports = serial.tools.list_ports.comports()
        devices = []
        for port in ports:
            devices.append(port.device)
        return devices
    
    # Open the serial port
    def open(self) -> bool:
        try:
            self.serial.open()
        except serial.SerialException as e:
            return False
        return True
    
    # Close the serial port
    def close(self) -> bool:
        try:
            while(not self.can_close): time.sleep(0.01)
            self.serial.close()
        except serial.SerialException as e:
            return False
        return True

    # Close the serial port and join the receive thread
    def quit(self) -> None:
        self.close()
        self.receive_thread_running = False
        self.receive_thread.join() 

    # Initialize the USBNow device
    def init(self) -> bool:
        if(not self.serial.is_open):
             self.open()
        self.send_slip_bytes(bytes([CMD.INIT]))
        if(self.wait_response(RESP.OK)):
            return True
        else:
             raise Exception("USBNow Initialization Failed")

    # Send a command to the USBNow device
    def send_slip_bytes(self, data: bytes):
        for byte in data:
            if byte == SLIP_END:
                self.serial.write(bytes([SLIP_ESC, SLIP_ESC_END]))
            elif byte == SLIP_ESC:
                self.serial.write(bytes([SLIP_ESC, SLIP_ESC_ESC]))
            else:
                self.serial.write(bytes([byte]))
        self.serial.write(bytes([SLIP_END]))

    # Wait for a response from the USBNow device until timeout
    def wait_response(self, type: CMD, timeout: int = None) -> bytes:
        self.waiting_response = type
        if(timeout == None):
            timeout = self.timeout
        now = time.time()
        while(time.time() - now < timeout):
            if(self.waiting_response == None):
                return self.receive_buffer[-1]
        return bytes()
    
    # Receive loop
    def rx_loop(self):
        while self.receive_thread_running:
            if(not self.serial.is_open): continue
            self.can_close = False
            timeout = time.time() + 0.5
            while(self.serial.in_waiting and time.time() < timeout):
                byte = self.serial.read(1)
                self.slip_decoder.push(byte[0])
            self.can_close = True
            if(self.slip_decoder.ready):
                self.parse_receive_package(self.slip_decoder.get())
            time.sleep(0.001)
    
    # Parse received package
    def parse_receive_package(self, data: bytes):
        if(data[0] == self.waiting_response):
            self.waiting_response = None
        
        if(data[0] == RESP.RECV_CB):
            if(self.receive_cb):
                mac = data[1:7]
                data = data[7:]
                self.receive_cb(mac, data)
        elif(data[0] == RESP.SEND_CB):
            if(self.send_cb):
                self.send_cb(data[1:])
        
        self.receive_buffer.append(data)

         

#------------------------------------------------------------------------------
class SLIP:
	END = 0xC0
	ESC = 0xDB
	ESC_END = 0xDC
	ESC_ESC = 0xDD
	def __init__(self):
		self.buffer: list[int] = []
		self.packages: list[bytearray] = []
		self.esc_flag: bool= False
		self.ready: int= 0
		self.wait_ack: bool = False
	#...
	def push(self, value: int):
		if(self.esc_flag):
			if(value == self.ESC_END):
				self.buffer.append(self.END)
			elif(value == self.ESC_ESC):
				self.buffer.append(self.ESC)
			elif(value == self.END):
				self.wait_ack = True
			self.esc_flag = False
		elif(value == self.ESC):
			self.esc_flag = True
		elif(value == self.END):
			self.ready += 1
			self.packages.append(bytearray(self.buffer))
			self.buffer.clear()
		else:
			self.buffer.append(value)
	#...
	def get(self) -> bytearray:
		if(self.ready):
			self.ready -= 1
			return(self.packages.pop(0))
		return(bytearray())

if(__name__ == "__main__"):
    usbnow = USBNow("COM4")
    usbnow.open()
    if(usbnow.init()):
        print("USBNow Initialized")
    else:
        print("USBNow Initialization Failed")
    usbnow.close()
    usbnow.quit()