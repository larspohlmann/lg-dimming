import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
import threading
import logging
from datetime import datetime
from bscpylgtv import WebOsClient, PyLGTVCmdException, StorageSqliteDict
from disable_autodimming import discover_tvs

CONFIG_FILE = "lg_config.json"
LOG_FILE = "lg_dimming.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class LGDimmingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LG OLED Auto-Dimming Control")
        self.root.geometry("550x450")

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, daemon=True)
        self.thread.start()

        self.create_widgets()
        self.load_config()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_async(self, coro):
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def create_widgets(self):
        # Connection Frame
        conn_frame = ttk.LabelFrame(self.root, text="Connection")
        conn_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(conn_frame, text="TV IP Address:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # IP Entry + Scan
        ip_frame = ttk.Frame(conn_frame)
        ip_frame.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self.ip_entry = ttk.Combobox(ip_frame, width=18)
        self.ip_entry.pack(side="left")
        
        self.scan_btn = ttk.Button(ip_frame, text="Scan", width=6, command=self.on_scan)
        self.scan_btn.pack(side="left", padx=5)

        ttk.Label(conn_frame, text="Client Key (Optional):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.key_entry = ttk.Entry(conn_frame, width=30)
        self.key_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.on_connect)
        self.connect_btn.grid(row=2, column=0, columnspan=2, pady=10)

        # Actions Frame
        action_frame = ttk.LabelFrame(self.root, text="Actions")
        action_frame.pack(padx=10, pady=5, fill="x")

        self.disable_btn = ttk.Button(action_frame, text="Disable Auto-Dimming (Recommended)", command=lambda: self.on_action(False), state="disabled")
        self.disable_btn.pack(fill="x", padx=10, pady=5)

        self.enable_btn = ttk.Button(action_frame, text="Enable Auto-Dimming (Default)", command=lambda: self.on_action(True), state="disabled")
        self.enable_btn.pack(fill="x", padx=10, pady=5)

        # Log Area
        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.log_area = scrolledtext.ScrolledText(log_frame, height=10, state="disabled")
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, message):
        logging.info(message)
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.ip_entry.set(config.get("ip", ""))
                    self.key_entry.insert(0, config.get("key", ""))
            except Exception:
                pass

    def save_config(self):
        config = {
            "ip": self.ip_entry.get().strip(),
            "key": self.key_entry.get().strip()
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
        except Exception as e:
            self.log(f"Failed to save config: {e}")

    def on_scan(self):
        self.scan_btn.config(state="disabled")
        logging.info("Starting device scan")
        self.log("Scanning for devices...")
        threading.Thread(target=self.scan_task, daemon=True).start()

    def scan_task(self):
        try:
            tvs = discover_tvs(timeout=3)
            ips = [tv['ip'] for tv in tvs]
            
            def update_ui():
                if ips:
                    self.ip_entry['values'] = ips
                    self.ip_entry.set(ips[0])
                    self.log(f"Found {len(ips)} device(s): {', '.join(ips)}")
                else:
                    self.log("No devices found.")
                self.scan_btn.config(state="normal")
            
            self.root.after(0, update_ui)
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Scan failed: {e}"))
            self.root.after(0, lambda: self.scan_btn.config(state="normal"))

    def on_connect(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showerror("Error", "Please enter an IP address.")
            return
        
        self.save_config()
        self.connect_btn.config(state="disabled")
        self.log(f"Connecting to {ip}...")
        self.run_async(self.connect_task(ip))

    async def connect_task(self, ip):
        storage = await StorageSqliteDict.create(db_path="lgtv_keys.db")
        self.client = WebOsClient(ip, storage=storage, states=[])
        
        try:
            await self.client.connect()
            self.root.after(0, lambda: self.log("Connected and paired."))
            self.root.after(0, self.enable_controls)

        except Exception as e:
            logging.error(f"Connection failed: {e}", exc_info=True)
            self.root.after(0, lambda: self.log(f"Connection failed: {e}"))
            self.root.after(0, lambda: self.connect_btn.config(state="normal"))

    def enable_controls(self):
        self.connect_btn.config(state="normal")
        self.disable_btn.config(state="normal")
        self.enable_btn.config(state="normal")

    def on_action(self, enable):
        action_str = "Enabling" if enable else "Disabling"
        self.log(f"{action_str} features...")
        self.disable_btn.config(state="disabled")
        self.enable_btn.config(state="disabled")
        self.run_async(self.action_task(enable))

    async def action_task(self, enable):
        try:
            await self.client.enable_tpc_or_gsr("tpc", enable)
            await self.client.enable_tpc_or_gsr("gsr", enable)
            
            msg = f"Done. Sent command to {'Enable' if enable else 'Disable'} TPC and GSR."
            self.root.after(0, lambda: self.log(msg))
            
        except Exception as e:
            logging.error(f"Operation failed: {e}", exc_info=True)
            self.root.after(0, lambda: self.log(f"Operation failed: {e}"))
        finally:
            self.root.after(0, self.enable_controls)

if __name__ == "__main__":
    root = tk.Tk()
    app = LGDimmingGUI(root)
    root.mainloop()
