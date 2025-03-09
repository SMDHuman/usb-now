import serial
import sys, os
import threading
import serial.tools.list_ports
import time

# USBNow Response Codes
RESP_OK = 0
RESP_ERROR = 1
RESP_VERSION = 2
RESP_PEER = 3
RESP_PEER_ADDR = 4
RESP_PEER_EXIST = 5
RESP_PEER_NUM = 6
RESP_RECV_CB = 7
RESP_SEND_CB = 8
RESP_ERROR_LEN = 9
RESP_ERROR_UNKNOWN = 10

# USBNow Commands
CMD_INIT = 0
CMD_DEINIT = 1
CMD_GET_VERSION = 2
CMD_SEND = 3
CMD_ADD_PEER = 4
CMD_DEL_PEER = 5
CMD_MOD_PEER = 6
CMD_CONFIG_ESPNOW_RATE = 7
CMD_GET_PEER = 8
CMD_FETCH_PEER = 9
CMD_IS_PEER_EXIST = 10
CMD_GET_PEER_NUM = 11
CMD_SET_PMK = 12
CMD_SET_WAKE_WINDOW = 13
CMD_GET_DEVICE_MAC = 14

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
        self.serial: serial.Serial = serial.Serial()
        self.serial.timeout = self.timeout
        self.serial.baudrate = self.baudrate
        self.serial.port = self.port
        self.slip_decoder = SLIP()
        self.receive_thread = threading.Thread(target=self.rx_loop)
        self.receive_thread_running = True
        self.receive_thread.start()
        self.receive_buffer: list[bytearray] = []
        self.can_close = False
        self.open()
    
    def open(self) -> bool:
        try:
            self.serial.open()
        except serial.SerialException as e:
            return False
        return True
    
    def close(self) -> bool:
        try:
            while(not self.can_close): time.sleep(0.01)
            self.serial.close()
        except serial.SerialException as e:
            return False
        return True

    def quit(self) -> None:
        self.receive_thread_running = False
        self.receive_thread.join() 

    def init(self) -> bool:
        if(not self.serial.is_open):
             self.open()
        self.send_slip_bytes(bytes([CMD_INIT]))
        return self.recv_slip_bytes() == bytes([RESP_OK])

    def send_slip_bytes(self, data: bytes):
        for byte in data:
            if byte == SLIP_END:
                self.serial.write(bytes([SLIP_ESC, SLIP_ESC_END]))
            elif byte == SLIP_ESC:
                self.serial.write(bytes([SLIP_ESC, SLIP_ESC_ESC]))
            else:
                self.serial.write(bytes([byte]))
        self.serial.write(bytes([SLIP_END]))

    def recv_slip_bytes(self, timeout: int = None) -> bytes:
        if(timeout == None):
            timeout = self.timeout
        now = time.time()
        while(time.time() - now < timeout):
            if(self.receive_buffer):
                return self.receive_buffer.pop(0)
        return bytes()
    
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
                self.receive_buffer.append(self.slip_decoder.get())
            time.sleep(0.001)

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