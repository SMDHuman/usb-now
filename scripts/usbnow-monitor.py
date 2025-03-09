from usbnow import USBNow
import argparse
import sys, os, re, json

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
    parser.add_argument("-r", "--peer", help="Peer MAC address", type=type_mac_address)
    parser.add_argument("-R", "--peers_list", help="Peers MAC address in a json file", type=type_json_path)
    parser.add_argument("-s", "--self", help="Get Device's MAC address")
    parser.add_argument("-v", "--version", help="Get Device's version")
    parser.add_argument("-l", "--list", help="List available devices", nargs="?", const=True)
    parser.add_argument("-b", "--baudrate", help="Set baudrate, Default: 115200", type=int, default=115200)
    parser.add_argument("-t", "--timeout", help="Set timeout, Defauld: 1", type=int, default=1)
    args = parser.parse_args()
    print(args)

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

        
    def receive_cb(_from, data):
        print(f"Received from {_from}: {data}")
    
    usbnow.receive_cb = receive_cb

    x = input("Press Enter to exit")
    print("Exiting")
    usbnow.quit()


main()
    