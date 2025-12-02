import asyncio
import argparse
import sys
import socket
import re
from bscpylgtv import WebOsClient, PyLGTVCmdException, StorageSqliteDict

def discover_tvs(timeout=3):
    """
    Discover LG WebOS TVs using SSDP.
    Returns a list of dictionaries containing 'ip' and 'model' (if available).
    """
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    SSDP_MX = 2
    SSDP_ST = "urn:schemas-upnp-org:device:Basic:1"

    ssdp_request = (
        f"M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
        f"MAN: \"ssdp:discover\"\r\n"
        f"MX: {SSDP_MX}\r\n"
        f"ST: {SSDP_ST}\r\n"
        f"\r\n"
    ).encode()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    
    tvs = []
    seen_ips = set()

    try:
        sock.sendto(ssdp_request, (SSDP_ADDR, SSDP_PORT))
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                response = data.decode()
                
                # Check if it's an LG TV (usually contains "LG" or "WebOS" in headers or server field)
                # This is a heuristic. A more robust way is to check the SERVER header.
                if "LG Electronics" in response or "WebOS" in response:
                    ip = addr[0]
                    if ip not in seen_ips:
                        seen_ips.add(ip)
                        # Try to extract model name if possible, otherwise just use IP
                        model = "Unknown Model"
                        # Simple regex to find something looking like a model name if present in headers
                        # Often in SERVER: ... WebOS/x.x ...
                        
                        tvs.append({"ip": ip, "model": model, "raw": response})
            except socket.timeout:
                break
    except Exception as e:
        print(f"Discovery error: {e}")
    finally:
        sock.close()
        
    return tvs

async def main():
    parser = argparse.ArgumentParser(description="Manage Auto Dimming (TPC/GSR) on LG OLED TV.")
    parser.add_argument("--ip", help="IP address of the LG WebOS TV")
    parser.add_argument("--key", help="Client key (optional, will be saved/loaded if not provided)")
    parser.add_argument("--enable", action="store_true", help="Enable TPC and GSR (default is to disable)")
    parser.add_argument("--discover", action="store_true", help="Discover LG TVs on the network")
    args = parser.parse_args()

    if args.discover:
        print("Scanning for LG TVs...")
        tvs = discover_tvs()
        if tvs:
            print(f"Found {len(tvs)} device(s):")
            for tv in tvs:
                print(f" - IP: {tv['ip']}")
        else:
            print("No LG TVs found.")
        return

    if not args.ip:
        print("Error: --ip is required unless --discover is used.")
        sys.exit(1)

    storage = await StorageSqliteDict.create(db_path="lgtv_keys.db")
    client = WebOsClient(args.ip, storage=storage, states=[])

    try:
        print(f"Connecting to {args.ip}...")
        await client.connect()
        print("Connected and paired.")

        # Determine target state
        target_state = args.enable
        action_str = "Enabling" if target_state else "Disabling"
        
        print(f"\n--- {action_str} Auto-Dimming Features ---")

        # TPC
        print(f"{action_str} TPC...")
        await client.enable_tpc_or_gsr("tpc", target_state)
        
        # GSR
        print(f"{action_str} GSR...")
        await client.enable_tpc_or_gsr("gsr", target_state)

        print("\nDone. (Note: Verification of status is not supported by this library version)")

    except PyLGTVCmdException as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
