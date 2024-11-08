#!/usr/bin/env python3

import socket
import threading
import queue
import sys
import time
from colorama import init, Fore
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter.messagebox import showerror
from ttkthemes import ThemedTk
import subprocess
import re
import os
import json

class PortScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SpyEye (Demo)")
        self.root.geometry("600x500")
        self.root.configure(bg='black')
        
        # Configure style
        style = ttk.Style()
        style.configure('Custom.TFrame', background='black')
        style.configure('Custom.TLabel', background='black', foreground='#FFD700')
        style.configure('Custom.TButton', background='black', foreground='#FFD700')
        
        # Initialize scan counter
        self.scan_count = 0
        self.max_scans = 3
        
        # Main frame
        self.main_frame = ttk.Frame(root, style='Custom.TFrame')
        self.main_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Demo Version Label
        demo_label = ttk.Label(
            self.main_frame,
            text="DEMO VERSION - Limited to 3 scans",
            style='Custom.TLabel',
            font=('Helvetica', 12, 'bold')
        )
        demo_label.pack(pady=5)
        
        # Input fields
        ttk.Label(self.main_frame, text="Target Host:", style='Custom.TLabel').pack(pady=5)
        self.target_entry = ttk.Entry(self.main_frame, width=40)
        self.target_entry.pack(pady=5)
        
        ttk.Label(self.main_frame, text="Port Range (e.g., 1-1024):", style='Custom.TLabel').pack(pady=5)
        self.ports_entry = ttk.Entry(self.main_frame, width=40)
        self.ports_entry.insert(0, "1-1024")
        self.ports_entry.pack(pady=5)
        
        ttk.Label(self.main_frame, text="Number of Threads:", style='Custom.TLabel').pack(pady=5)
        self.threads_entry = ttk.Entry(self.main_frame, width=40)
        self.threads_entry.insert(0, "100")
        self.threads_entry.pack(pady=5)
        
        # Exploit search
        ttk.Label(self.main_frame, text="Search Exploit:", style='Custom.TLabel').pack(pady=5)
        self.exploit_entry = ttk.Entry(self.main_frame, width=40)
        self.exploit_entry.pack(pady=5)
        
        self.exploit_button = ttk.Button(
            self.main_frame,
            text="Search Exploit",
            command=self.search_exploit,
            style='Custom.TButton'
        )
        self.exploit_button.pack(pady=10)
        
        # Scan button
        self.scan_button = ttk.Button(
            self.main_frame,
            text="Start Scan",
            command=self.start_scan,
            style='Custom.TButton'
        )
        self.scan_button.pack(pady=20)
        
        # Results area
        self.results_area = scrolledtext.ScrolledText(
            self.main_frame,
            height=15,
            bg='black',
            fg='#FFD700',
            font=('Courier', 10)
        )
        self.results_area.pack(pady=10, fill='both', expand=True)
        
        # Scan counter label
        self.scan_counter_label = ttk.Label(
            self.main_frame,
            text=f"Remaining scans: {self.max_scans - self.scan_count}",
            style='Custom.TLabel'
        )
        self.scan_counter_label.pack(pady=5)
        
        # Add this near the start of __init__
        self.scan_data_file = os.path.join(os.path.expanduser('~'), '.spyeye_demo.json')
        self.load_scan_count()

    def log_message(self, message, color='#FFD700'):
        self.results_area.insert(tk.END, message + '\n')
        self.results_area.see(tk.END)
        self.root.update()

    def start_scan(self):
        if self.scan_count >= self.max_scans:
            showerror("Demo Limit Reached",
                     "You have reached the demo version limit (3 scans).\n\n"
                     "Please contact the owner for the full version:\n"
                     "WhatsApp: +963960955844\n"
                     "Telegram: @h00x7r")
            return
            
        self.scan_count += 1
        self.save_scan_count()
        self.scan_counter_label.config(
            text=f"Remaining scans: {self.max_scans - self.scan_count}"
        )
        
        # Clear previous results
        self.results_area.delete(1.0, tk.END)
        
        target = self.target_entry.get()
        ports = self.ports_entry.get()
        threads = self.threads_entry.get()
        
        try:
            start_port, end_port = map(int, ports.split('-'))
            threads = int(threads)
        except ValueError:
            showerror("Error", "Invalid port range or thread count")
            return
        
        scan_thread = threading.Thread(
            target=self.run_scan,
            args=(target, start_port, end_port, threads)
        )
        scan_thread.daemon = True
        scan_thread.start()

    def run_scan(self, target, start_port, end_port, threads):
        results = queue.Queue()
        
        self.log_message(f"Starting scan on host: {target}")
        try:
            target_ip = socket.gethostbyname(target)
            self.log_message(f"Target IP: {target_ip}\n")
        except socket.gaierror:
            self.log_message("Could not resolve hostname", '#FF0000')
            return

        thread_list = []
        for port in range(start_port, end_port + 1):
            thread = threading.Thread(
                target=scan_port,
                args=(target, port, 1, results)
            )
            thread.daemon = True
            thread_list.append(thread)

        for thread in thread_list:
            thread.start()
            while threading.active_count() > threads:
                time.sleep(0.1)

        for thread in thread_list:
            thread.join()

        self.log_message("\nOpen ports:")
        while not results.empty():
            port, status, service = results.get()
            self.log_message(f"Port {port}: {service}")
        
        self.log_message("\nScan completed!")

    def search_exploit(self):
        search_term = self.exploit_entry.get()
        if not search_term:
            self.log_message("Please enter a search term", '#FF0000')
            return
            
        try:
            if sys.platform == 'win32':
                try:
                    cmd = f'wsl searchsploit {search_term} --colour --exclude="/dos/"'
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    output, error = process.communicate()
                    
                    if error:
                        if "wsl: command not found" in error:
                            self.log_message("\nError: WSL not installed. if you're using windows - Please install WSL and Kali Linux:", '#FF0000')
                            self.log_message("1. Enable WSL feature in Windows")
                            self.log_message("2. Install Kali Linux from Microsoft Store")
                            self.log_message("3. Run: wsl sudo apt install exploitdb")
                            return
                        elif "searchsploit: command not found" in error:
                            self.log_message("Error: searchsploit not installed in WSL. Run:", '#FF0000')
                            self.log_message("wsl sudo apt install exploitdb")
                            return
                        self.log_message(f"Error: {error}", '#FF0000')
                        return
                    
                    if not output.strip():
                        self.log_message(f"No exploits found for '{search_term}'")
                        return
                    
                    self.log_message("\n=== Exploit Search Results ===")
                    clean_results = re.sub(r'\x1b\[[0-9;]*m', '', output)
                    self.log_message(clean_results)
                except Exception as e:
                    url = f"https://exploit-db.com/search?q={search_term}"
                    self.log_message("\nFallback to web search:", '#FF0000')
                    self.log_message(f"Please visit: {url}")
            else:
                # Linux/Unix handling
                cmd = f"searchsploit {search_term} --colour --exclude='/dos/'"
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True  # Use text mode for easier string handling
                )
                output, error = process.communicate()
                
                if error:
                    if "searchsploit: command not found" in error:
                        self.log_message("Error: searchsploit not installed. Please install exploitdb package.", '#FF0000')
                        return
                    self.log_message(f"Error: {error}", '#FF0000')
                    return
                    
                if not output.strip():
                    self.log_message(f"No exploits found for '{search_term}'")
                    return
                    
                self.log_message("\n=== Exploit Search Results ===")
                # Clean ANSI color codes and format output
                clean_results = re.sub(r'\x1b\[[0-9;]*m', '', output)
                self.log_message(clean_results)
                
        except Exception as e:
            self.log_message(f"Search failed: {str(e)}", '#FF0000')

    def load_scan_count(self):
        try:
            if os.path.exists(self.scan_data_file):
                with open(self.scan_data_file, 'r') as f:
                    data = json.load(f)
                    self.scan_count = data.get('scan_count', 0)
            else:
                self.scan_count = 0
        except:
            self.scan_count = 0

    def save_scan_count(self):
        try:
            with open(self.scan_data_file, 'w') as f:
                json.dump({'scan_count': self.scan_count}, f)
        except:
            pass

def scan_port(target, port, timeout, results):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target, port))
        if result == 0:
            try:
                service = socket.getservbyport(port)
            except:
                service = "unknown"
            results.put((port, "open", service))
        sock.close()
    except:
        pass

def main():
    root = ThemedTk(theme="black")
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    app = PortScannerGUI(root)
    root.mainloop()

def on_closing(root):
    root.destroy()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Scan interrupted by user{Fore.RESET}")
        sys.exit(0) 