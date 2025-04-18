from usbnow import USBNow
import argparse
import sys, os, re, json

def number2base(n: int, b: int) -> str:
    base_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if n == 0:
        return "0"
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    return "".join([base_chars[x] for x in digits[::-1]])

def type_mac_address(value: str):
    if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', value):
        raise argparse.ArgumentTypeError(f'{value} is not a valid MAC address')
    value = value.split(':')
    value = bytes([int(x, 16) for x in value])
    return value

def type_json_path(value: str):
    if not os.path.exists(value):
        raise argparse.ArgumentTypeError(f'{value} does not exist')
    if not os.path.isfile(value):
        raise argparse.ArgumentTypeError(f'{value} is not a file')
    if not value.endswith('.json'):
        raise argparse.ArgumentTypeError(f'{value} is not a json file')
    with open(value, 'r') as f:
        value = json.load(f)
    return value

def main():
    parser = argparse.ArgumentParser(description='Monitor USB devices')
    parser.add_argument("port", type=str, help="Serial port", nargs="?")
    parser.add_argument("-l", "--list", help="List available devices", nargs="?", const=True)
    parser.add_argument("-b", "--baudrate", help="Set baudrate, Default: 115200", type=int, default=115200)
    parser.add_argument("-t", "--timeout", help="Set timeout, Defauld: 1", type=int, default=1)
    parser.add_argument("-d", "--display_base", help="Set received message display base", type=int, default=16)
    args = parser.parse_args()

    if(not args.port):
        parser.print_help()
        sys.exit(0)

    if(args.list):
        devices = USBNow.list_devices()
        if(len(devices) == 0):
            print("No devices found")
        else:
            print("Available devices:")
            for device in devices:
                print(" ", device)
        sys.exit(0)

    usbnow = USBNow(args.port, args.baudrate, args.timeout)
    usbnow.init()
    print("USBNow device initialized")

    print("Version:", usbnow.get_version())
    print("MAC:", usbnow.get_mac())
        
    def receive_cb(_from, data):
        mac_str = ':'.join([f"{x:02X}" for x in _from])
        data = [number2base(x, args.display_base) for x in data]
        print(f"[{mac_str}] {",".join(data)}")
    
    usbnow.receive_cb = receive_cb

    x = input("Press Enter to exit\n")
    print("Exiting...")
    usbnow.deinit()
    usbnow.close()


main()
    