import struct
import threading
import time
from collections.abc import Sequence
from typing import Callable
from serial import Serial
from serial.threaded import ReaderThread, Protocol
import serial.tools.list_ports

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
    GET_MAC = 14
#------------------------------------------------------------------------------
class MAC(Sequence):
    """MAC Address representation class.
    This class provides a versatile way to handle MAC (Media Access Control) addresses in various formats.
    It supports initialization from strings (XX:XX:XX:XX:XX:XX format), bytes, bytearray, or list of integers.
    The class implements sequence protocol and provides common comparison operations.
    Args:
        addr (Union[str, bytes, bytearray, list[int]]): MAC address in one of the supported formats:
            - str: Colon-separated hexadecimal string (e.g., "00:11:22:33:44:55")
            - bytes: Raw bytes object containing MAC address
            - bytearray: Byte array containing MAC address
            - list[int]: List of integers representing MAC address bytes
    Raises:
        ValueError: If the input format is not supported or invalid
    Properties:
        addr (bytes): Internal storage of MAC address as bytes
    """
    def __init__(self, addr: str|bytes|bytearray|list[int]):
        if(isinstance(addr, str)):
            self.addr = bytes([int(x, 16) for x in addr.split(':')])
        elif(isinstance(addr, bytes)):
            self.addr = addr
        elif(isinstance(addr, bytearray)):
            self.addr = bytes(addr)
        elif(isinstance(addr, list)):
            self.addr = bytes(addr)
        else:
            raise ValueError("Invalid MAC Address: ", type(addr))
        super().__init__()
    
    def __str__(self):
        return ':'.join([f"{x:02X}" for x in self.addr])

    def __bytes__(self):
        return self.addr
    
    def __eq__(self, other):
        return self.addr == other.addr
    
    def __ne__(self, other):
        return self.addr != other.addr
    
    def __len__(self):
        return len(self.addr)
    
    def __getitem__(self, key):
        return self.addr[key]
    
    def __repr__(self):
         return f"MAC({self.__str__()})"

# Slip constants
SLIP_END = 0xC0
SLIP_ESC = 0xDB
SLIP_ESC_END = 0xDC
SLIP_ESC_ESC = 0xDD

class USBNow(Protocol):
    def _self_(self):
        return(self)
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: int = 1, print_error: bool = False, wait_resp: bool = True): 
        self.port: str = port
        self.baudrate: int = baudrate
        self.timeout: int = timeout
        self.print_error = print_error
        self.wait_resp: bool = wait_resp
        self.receive_buffer: list[bytearray] = []
        self.receive_cb: Callable[[bytes, bytes], None] = None
        self.send_cb: Callable[[bytes, str], None] = None
        self.error_resp: str = None
        #...
        self.serial: serial.Serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self.serial_thread = ReaderThread(self.serial, self._self_)
        self.serial_thread.start()
        self.slip_decoder = SLIP()
        #...
        #self.receive_thread = threading.Thread(target=self.rx_loop, daemon=True)
        self.can_close_lock = threading.Lock()
        self.OK_resp_lock = threading.Condition()
        self.serial_com_lock = threading.Lock()
        self.receive_thread_running = threading.Event()
        #self.receive_thread.start()
        #...
        self.send_count: int = 0
        self.resp_ok_count: int = 0
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

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
    def close(self) -> None:
        self.can_close_lock.acquire()
        self.serial.close()
        self.receive_thread_running.set()

    # Send a command to the USBNow device
    def send_slip_bytes(self, data: bytes):
        self.serial_com_lock.acquire()
        self.send_count += 1
        checksum = 0
        for byte in data:
            self.send_slip_byte(byte)
            checksum += byte + 1
        checksum = struct.pack("I", checksum)
        #print("Checksum:", checksum)
        #print(data)
        for byte in checksum:
            self.send_slip_byte(byte)
        self.serial.write(bytes([SLIP_END]))
        self.serial_com_lock.release()
    
    def send_slip_byte(self, data: int):
        if data == SLIP_END:
            self.serial.write(bytes([SLIP_ESC, SLIP_ESC_END]))
        elif data == SLIP_ESC:
            self.serial.write(bytes([SLIP_ESC, SLIP_ESC_ESC]))
        else:
            self.serial.write(bytes([data]))

    # Wait for a response from the USBNow device until timeout
    def wait_ok(self) -> str|None:
        #res = self.OK_resp_lock.acquire(timeout=self.timeout)
        #print("waiting for OK")
        with self.OK_resp_lock:
            res = self.OK_resp_lock.wait(self.timeout)
            if(res == False):
                return("timeout")
        if(self.print_error and self.error_resp):
            print("Error:", self.error_resp)
        #print("OK Release")
        #self.OK_resp_lock.release()
        return(self.error_resp)
    
    # Called when data is received By Serial.ReaderThread
    def data_received(self, data: bytes):
        for byte in data:
            self.slip_decoder.push(byte)
            #...
            if(self.slip_decoder.in_wait() > 0):
                data = self.slip_decoder.get()
                #print("Data: ", data)
                self.parse_receive_package(data)
    
    # Parse received package
    def parse_receive_package(self, data: bytes) -> None:
        #print("Data: ", data)
        
        if(data[0] == RESP.RECV_CB):
            if(self.receive_cb):
                mac = data[1:7]
                data = data[7:]
                self.receive_cb(mac, data)
        elif(data[0] == RESP.SEND_CB):
            if(self.send_cb):
                self.send_cb(data[1:7], ["OK", "ERROR"][data[7]])
        elif(data[0] == RESP.ERROR):
            with self.OK_resp_lock:
                self.error_resp = data[1:].decode()
                self.OK_resp_lock.notify()
                #self.OK_resp_lock.release()
        elif(data[0] == RESP.ERROR_LEN):
            raise Exception("USBNow Error: Invalid Length")
        elif(data[0] == RESP.ERROR_UNKNOWN):
            raise Exception("USBNow Error: Unknown Command")
        elif(data[0] == RESP.OK):
            with self.OK_resp_lock:
                self.error_resp = None
                self.OK_resp_lock.notify()
                #self.OK_resp_lock.release()
        else:
            self.receive_buffer.append(data)
            if(len(self.receive_buffer) > 10):
                self.receive_buffer.pop(0)

    #------------------------------------------------------------------------------
    # USBNow API
    #------------------------------------------------------------------------------
    def init(self) -> str|None:
        """Initialize ESP-NOW function.
        
        Returns:
            str|None: None if successful, error message string if failed
        """
        self.send_slip_bytes(bytes([CMD.INIT]))
        return(self.wait_ok())
    
    def deinit(self) -> str|None:
        """Deinitialize ESP-NOW function.
        
        Returns:
            str|None: None if successful, error message string if failed
        """
        self.send_slip_bytes(bytes([CMD.DEINIT]))
        if(self.wait_resp): return(self.wait_ok())

    def register_recv_cb(self, cb: Callable[[bytes, bytes], None]) -> None:
        """Register callback function for receiving data.
        
        Args:
            cb: Callback function taking MAC address (bytes) and data (bytes) as parameters
        """
        self.receive_cb = cb

    def register_send_cb(self, cb: Callable[[bytes, str], None]) -> None:
        """Register callback function for sending data.
        
        Args:
            cb: Callback function taking MAC address (bytes) and status (str) as parameters
        """
        self.send_cb = cb
        
    def get_version(self) -> int|str:
        """Get ESP-NOW version number.
        
        Returns:
            int|str: Version number if successful, error message string if failed
        """
        self.send_slip_bytes(bytes([CMD.GET_VERSION]))
        if(self.wait_resp): 
            res = self.wait_ok()
        else:
            res = None
        #...
        if(res): return res
        if(len(self.receive_buffer) == 0): return "No Response"
        if(self.receive_buffer[-1][0] == RESP.VERSION):
            return struct.unpack("I", self.receive_buffer[-1][1:])[0]
    
    def send(self, peer_addr: MAC, data: bytes) -> str|None:
        """Send data to a peer device.
        
        Args:
            peer_addr: MAC address of target device
            data: Data bytes to send
            
        Returns:
            str|None: None if successful, error message string if failed
        """
        self.send_slip_bytes(bytes([CMD.SEND]) + bytes(peer_addr) + data)
        if(self.wait_resp): return self.wait_ok()
    
    def add_peer(self, peer_addr: MAC, channel: int = 0, encrypt: bool = False) -> str|None:
        """Add peer device to peer list.
        
        Args:
            peer_addr: MAC address of peer device
            channel: WiFi channel (0-14)
            encrypt: Enable encryption
            
        Returns:
            str|None: None if successful, error message string if failed
        """
        self.send_slip_bytes(bytes([CMD.ADD_PEER]) + bytes(peer_addr) + bytes([channel, encrypt]))
        if(self.wait_resp): return self.wait_ok()
    
    def mod_peer(self, peer_addr: MAC, channel: int = 0, encrypt: bool = False) -> str|None:
        """Modify existing peer device parameters.
        
        Args:
            peer_addr: MAC address of peer device
            channel: WiFi channel (0-14)
            encrypt: Enable encryption
            
        Returns:
            str|None: None if successful, error message string if failed
        """
        self.send_slip_bytes(bytes([CMD.MOD_PEER]) + bytes(peer_addr) + bytes([channel, encrypt]))
        if(self.wait_resp): return self.wait_ok()
    
    def del_peer(self, peer_addr: MAC) -> str|None:
        """Delete peer from peer list.
        
        Args:
            peer_addr: MAC address of peer device to remove
            
        Returns:
            str|None: None if successful, error message string if failed
        """
        self.send_slip_bytes(bytes([CMD.DEL_PEER]) + bytes(peer_addr))
        if(self.wait_resp): return self.wait_ok()

    def config_espnow_rate(self, ifx: int, rate: int) -> str|None:
        """Configure ESP-NOW data rate.
        
        Args:
            ifx: Interface index
            rate: Data rate value
            
        Returns:
            str|None: None if successful, error message string if failed
        """
        self.send_slip_bytes(bytes([CMD.CONFIG_ESPNOW_RATE, ifx, rate]))
        if(self.wait_resp): return self.wait_ok()
    
    def get_peer(self, peer_addr: MAC) -> tuple[bytes, int, bool]:
        """Get peer device information.
        
        Args:
            peer_addr: MAC address of peer device
            
        Returns:
            tuple: (MAC address, channel, encryption status)
            
        Raises:
            Exception: If no peer response received
        """
        self.send_slip_bytes(bytes([CMD.GET_PEER]) + bytes(peer_addr))
        if(self.wait_resp): self.wait_ok()
        if(len(self.receive_buffer) == 0): return "No Response"
        if(self.receive_buffer[-1][0] == RESP.PEER):
            return (self.receive_buffer[-1][1:7], self.receive_buffer[-1][7], self.receive_buffer[-1][8])
        else:
            raise Exception("USBNow Error: No Peer Response")
    
    def fetch_peer(self, from_head: bool) -> tuple[bytes, int, bool]:
        """Fetch next peer from peer list.
        
        Args:
            from_head: Start searching from beginning of list if True
            
        Returns:
            tuple: (MAC address, channel, encryption status)
            
        Raises:
            Exception: If no peer response received
        """
        self.send_slip_bytes(bytes([CMD.FETCH_PEER, from_head]))
        if(self.wait_resp): self.wait_ok()
        if(len(self.receive_buffer) == 0): return "No Response"
        if(self.receive_buffer[-1][0] == RESP.PEER):
            return (self.receive_buffer[-1][1:7], self.receive_buffer[-1][7], self.receive_buffer[-1][8])
        else:
            raise Exception("USBNow Error: No Peer Response")
    
    def is_peer_exist(self, peer_addr: MAC) -> bool:
        """Check if peer exists in peer list.
        
        Args:
            peer_addr: MAC address to check
            
        Returns:
            bool: True if peer exists
            
        Raises:
            Exception: If no response received
        """
        self.send_slip_bytes(bytes([CMD.IS_PEER_EXIST]) + bytes(peer_addr))
        if(self.wait_resp): self.wait_ok()
        if(len(self.receive_buffer) == 0): return "No Response"
        if(self.receive_buffer[-1][0] == RESP.PEER_EXIST):
            return self.receive_buffer[-1][1]
        else:
            raise Exception("USBNow Error: No Peer Exist Response")

    def get_peer_num(self) -> int:
        """Get number of peers in peer list.
        
        Returns:
            int: Number of peers
            
        Raises:
            Exception: If no response received
        """
        self.send_slip_bytes(bytes([CMD.GET_PEER_NUM]))
        if(self.wait_resp): self.wait_ok()
        if(len(self.receive_buffer) == 0): return "No Response"
        if(self.receive_buffer[-1][0] == RESP.PEER_NUM):
            return struct.unpack("i", self.receive_buffer[-1][1:])[0]
        else:
            raise Exception("USBNow Error: No Peer Number Response")
    
    def set_pmk(self, pmk: bytes) -> str|None:
        """Set Primary Master Key for ESP-NOW encryption.
        
        Args:
            pmk: Primary Master Key bytes
            
        Returns:
            str|None: None if successful, error message string if failed
        """
        self.send_slip_bytes(bytes([CMD.SET_PMK]) + pmk)
        if(self.wait_resp): return self.wait_ok()
    
    def set_wake_window(self, window: int) -> str|None:
        """Set wake window duration.
        
        Args:
            window: Wake window duration in milliseconds
            
        Returns:
            str|None: None if successful, error message string if failed
        """
        window = struct.pack("H", window)
        self.send_slip_bytes(bytes([CMD.SET_WAKE_WINDOW]) + window)
        if(self.wait_resp): return self.wait_ok()
    
    def get_mac(self) -> MAC:
        """Get MAC address of local device.
        
        Returns:
            MAC: MAC address object
            
        Raises:
            Exception: If no response received
        """
        self.send_slip_bytes(bytes([CMD.GET_MAC]))
        if(self.wait_resp): self.wait_ok()
        if(len(self.receive_buffer) == 0): return "No Response"
        if(self.receive_buffer[-1][0] == RESP.PEER_ADDR):
            return MAC(self.receive_buffer[-1][1:7])
        else:
            raise Exception("USBNow Error: No Device MAC Response")

#------------------------------------------------------------------------------
class SLIP:
    END = 0xC0
    ESC = 0xDB
    ESC_END = 0xDC
    ESC_ESC = 0xDD
    def __init__(self, checksum_enable = True):
        self.buffer: list[int] = []
        self.packages: list[bytearray] = []
        self.esc_flag: bool= False
        self.wait_ack: bool = False
        self.checksum_enable: bool = checksum_enable
        self.checksum = 0
    #...
    def push(self, value: int):
        #...
        if(self.esc_flag):
            if(value == self.ESC_END):
                self.buffer.append(self.END)
                self.checksum += self.END + 1
            elif(value == self.ESC_ESC):
                self.buffer.append(self.ESC)
                self.checksum += self.ESC + 1
            elif(value == self.END):
                self.wait_ack = True
            self.esc_flag = False
        #...
        elif(value == self.ESC):
            self.esc_flag = True
        #...
        elif(value == self.END):
            if(self.checksum_enable):
                #...
                if(len(self.buffer) < 4):
                    self.reset_buffer()
                    return
                #...
                for byte in self.buffer[-4:]:
                    self.checksum -= byte+1
                checksum = struct.unpack("I", bytes(self.buffer[-4:]))[0]
                #...
                if(self.checksum != checksum): 
                    self.reset_buffer()
                    return
                self.buffer = self.buffer[:-4]
            self.packages.append(bytearray(self.buffer))
            self.reset_buffer()
        #...
        else:
            self.buffer.append(value)
            self.checksum += value + 1
        self.checksum %= 2**32
    #...
    def get(self) -> bytearray:
        if(len(self.packages) > 0):
            return(self.packages.pop(0))
        return(bytearray())
    #...
    def in_wait(self) -> int:
        return(len(self.packages))
    #...
    def reset_buffer(self):
        self.buffer.clear()
        self.esc_flag = False
        self.wait_ack = False
        self.checksum = 0


# Ping tester
if(__name__ == "__main__"):
    import time, sys
    def recv_cb(mac: bytes, data: bytes):
        print(f"Received {data} from {MAC(mac)}")
    def send_cb(mac: bytes, status: str):
        print(f"Send to {MAC(mac)}: {status}")
    usbnow = USBNow("COM11")
    usbnow.register_recv_cb(recv_cb)
    #usbnow.register_send_cb(send_cb)
    err = usbnow.init()
    if(err):
        print("USBNow has error: ", err)
        sys.exit(1)
    print("USBNow initialized")
    res = usbnow.add_peer(MAC("FF:FF:FF:FF:FF:FF"))
    try:
        while True:
            start_send = time.time()
            res = usbnow.send(MAC("FF:FF:FF:FF:FF:FF"), bytes(100))
            end_send = time.time()
            print("Send Per Second", 1/(end_send-start_send))
    except KeyboardInterrupt:
        print("Exiting...")
        usbnow.close()
        print("Closed")
