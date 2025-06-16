#!/usr/bin/env python3
"""
SpyEye.py: A simple port scanner and exploit search tool with a GUI.

This script provides a basic graphical user interface (GUI) for scanning
open ports on a target host and searching for known exploits related to
services running on those ports using the 'searchsploit' tool.
It is intended for educational purposes and network security auditing
where authorized.
"""

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
import webbrowser # Added for web search fallback enhancement


class PortScannerGUI:
    """
    Manages the GUI for the port scanner and exploit search tool.

    This class handles the creation of UI elements, user input,
    initiating port scans, triggering exploit searches, and displaying
    results.
    """
    def __init__(self, root_window):
        """
        Initializes the PortScannerGUI.

        Args:
            root_window: The main Tkinter window for the application.
        """
        self.root = root_window
        self.root.title("SpyEye (Demo)")
        self.root.minsize(500, 400)
        self.root.geometry("600x500")
        self.root.configure(bg='black')

        style = ttk.Style()
        style.configure('Custom.TFrame', background='black')
        style.configure('Custom.TLabel', background='black', foreground='#FFD700', font=('Helvetica', 10))
        style.configure('Custom.TButton', background='black', foreground='#FFD700', font=('Helvetica', 10, 'bold'))
        style.configure('Custom.TEntry', fieldbackground='gray20', foreground='#FFD700', insertbackground='#FFD700')

        self.scan_count = 0
        self.max_scans = 3

        self.main_frame = ttk.Frame(self.root, style='Custom.TFrame')
        self.main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        demo_label = ttk.Label(
            self.main_frame,
            text="DEMO VERSION - Limited to 3 scans",
            style='Custom.TLabel',
            font=('Helvetica', 11, 'bold')
        )
        demo_label.pack(pady=(5, 10))

        input_frame = ttk.Frame(self.main_frame, style='Custom.TFrame')
        input_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(input_frame, text="Target Host:", style='Custom.TLabel').pack(pady=(5, 0))
        self.target_entry = ttk.Entry(input_frame, width=45, style='Custom.TEntry')
        self.target_entry.pack(pady=(0, 5), ipady=2)

        ttk.Label(input_frame, text="Port Range (e.g., 1-1024):", style='Custom.TLabel').pack(pady=(5, 0))
        self.ports_entry = ttk.Entry(input_frame, width=45, style='Custom.TEntry')
        self.ports_entry.insert(0, "1-1024")
        self.ports_entry.pack(pady=(0, 5), ipady=2)

        ttk.Label(input_frame, text="Number of Threads (e.g., 100):", style='Custom.TLabel').pack(pady=(5, 0))
        self.threads_entry = ttk.Entry(input_frame, width=45, style='Custom.TEntry')
        self.threads_entry.insert(0, "100")
        self.threads_entry.pack(pady=(0, 10), ipady=2)

        exploit_frame = ttk.Frame(self.main_frame, style='Custom.TFrame')
        exploit_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(exploit_frame, text="Search Exploit (e.g., Apache 2.4):", style='Custom.TLabel').pack(pady=(5, 0))
        self.exploit_entry = ttk.Entry(exploit_frame, width=45, style='Custom.TEntry')
        self.exploit_entry.pack(pady=(0, 5), ipady=2)

        self.exploit_button = ttk.Button(
            exploit_frame,
            text="Search Exploit",
            command=self.search_exploit,
            style='Custom.TButton'
        )
        self.exploit_button.pack(pady=10)

        self.scan_button = ttk.Button(
            self.main_frame,
            text="Start Port Scan",
            command=self.start_scan,
            style='Custom.TButton'
        )
        self.scan_button.pack(pady=15)

        self.results_area = scrolledtext.ScrolledText(
            self.main_frame,
            height=10,
            bg='black',
            fg='#FFD700',
            font=('Courier', 9),
            relief=tk.SUNKEN,
            borderwidth=1
        )
        self.results_area.pack(pady=10, padx=5, fill='both', expand=True)

        self.scan_counter_label = ttk.Label(
            self.main_frame,
            text=f"Remaining scans: {self.max_scans - self.scan_count}",
            style='Custom.TLabel',
            font=('Helvetica', 9)
        )
        self.scan_counter_label.pack(pady=(5, 0))

        self.scan_data_file = os.path.join(os.path.expanduser('~'), '.spyeye_demo.json')
        self.load_scan_count()

    def log_message(self, message, color='#FFD700'):
        """Logs a message to the results area in the GUI."""
        self.results_area.insert(tk.END, message + '\n')
        self.results_area.see(tk.END)
        self.root.update_idletasks()

    @staticmethod
    def _parse_port_range(ports_str: str) -> tuple[int, int]:
        """
        Parses a port range string (e.g., "1-1024") into start and end ports.

        Args:
            ports_str: The string containing the port range.

        Returns:
            A tuple (start_port, end_port).

        Raises:
            ValueError: If the port range string is invalid, ports are out of
                        valid range (1-65535), or start_port > end_port.
        """
        if not isinstance(ports_str, str):
            raise ValueError("Port range must be a string.")

        parts = ports_str.split('-')
        if len(parts) != 2:
            raise ValueError("Port range must be in 'start-end' format (e.g., '1-1024').")

        try:
            start_port = int(parts[0])
            end_port = int(parts[1])
        except ValueError:
            raise ValueError("Start and end ports must be integers.")

        if not (1 <= start_port <= 65535 and 1 <= end_port <= 65535):
            raise ValueError("Ports must be between 1 and 65535.")

        if start_port > end_port:
            raise ValueError("Start port cannot be greater than end port.")

        return start_port, end_port

    def start_scan(self):
        """Initiates a port scan based on user input from the GUI."""
        if self.scan_count >= self.max_scans:
            showerror("Demo Limit Reached",
                      "You have reached the demo version limit (3 scans).\n\n"
                      "Contact owner for full version:\nWhatsApp: +963960955844\nTelegram: @h00x7r")
            return

        target_host = self.target_entry.get().strip()
        port_range_str = self.ports_entry.get().strip()
        num_threads_str = self.threads_entry.get().strip()

        if not target_host:
            showerror("Input Error", "Target Host cannot be empty.")
            return # No scan count change if basic validation fails before increment

        try:
            start_port, end_port = PortScannerGUI._parse_port_range(port_range_str)
            num_threads = int(num_threads_str)
            if not (1 <= num_threads <= 500):
                raise ValueError("Number of Threads must be between 1 and 500.")
        except ValueError as e:
            showerror("Input Error", f"Invalid input: {e}")
            return # No scan count change

        # Increment scan count only after all initial validations pass
        self.scan_count += 1
        self.save_scan_count()
        self.update_scan_counter_label()
        self.results_area.delete(1.0, tk.END)

        scan_thread = threading.Thread(
            target=self.run_scan,
            args=(target_host, start_port, end_port, num_threads)
        )
        scan_thread.daemon = True
        scan_thread.start()

    def _revert_scan_count(self):
        """Decrements scan count, saves, and updates label. Used if scan setup fails post-increment."""
        # This method is now less likely to be needed if scan_count is incremented
        # only after all client-side validations pass.
        # However, it's kept in case run_scan has an early exit that constitutes a "failed scan attempt".
        self.scan_count -= 1
        self.save_scan_count()
        self.update_scan_counter_label()

    def run_scan(self, target_host, start_port, end_port, num_threads):
        """Executes the port scanning logic."""
        results_queue = queue.Queue()
        self.log_message(f"[*] Starting scan on host: {target_host}")
        try:
            target_ip = socket.gethostbyname(target_host)
            self.log_message(f"[*] Target IP: {target_ip}\n")
        except socket.gaierror:
            self.log_message(f"[!] Could not resolve hostname: {target_host}. Check network and hostname.", '#FF0000')
            self._revert_scan_count() # Revert scan count as it was a failed attempt
            return
        except Exception as e:
            self.log_message(f"[!] Error resolving host: {e}", '#FF0000')
            self._revert_scan_count() # Revert scan count
            return

        thread_list = []
        for port_num in range(start_port, end_port + 1):
            try:
                thread = threading.Thread(
                    target=scan_port_worker,
                    args=(target_ip, port_num, 1, results_queue)
                )
                thread.daemon = True
                thread_list.append(thread)
                thread.start()
                while threading.active_count() > num_threads + 1:
                    time.sleep(0.01)
            except threading.ThreadError as e:
                self.log_message(f"[!] Error creating thread for port {port_num}: {e}", "#FF0000")
            except Exception as e:
                self.log_message(f"[!] Unexpected error for port {port_num}: {e}", "#FF0000")

        for thread in thread_list:
            thread.join()

        self.log_message("\n[+] Open ports found:")
        open_ports_found = False
        temp_results = []
        while not results_queue.empty():
            port, status, service_name = results_queue.get()
            temp_results.append(f"  Port {port}: {service_name}")
            open_ports_found = True

        if open_ports_found:
            self.log_message("\n".join(temp_results))
        else:
            self.log_message("  No open ports found in the specified range.")
        self.log_message("\n[*] Scan completed!")

    def _execute_searchsploit(self, search_term):
        """Helper method to execute 'searchsploit'."""
        if sys.platform == 'win32':
            cmd = f'wsl searchsploit "{search_term}" --colour --exclude="/dos/"'
        else:
            cmd = f'searchsploit "{search_term}" --colour --exclude="/dos/"'

        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            output, error = process.communicate(timeout=60)
            return output, error
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                killed_output, killed_error = process.communicate(timeout=5)
            except Exception:
                killed_output, killed_error = "", ""
            timeout_msg = "Searchsploit command timed out after 60 seconds."
            if killed_error.strip():
                timeout_msg += f"\nError stream after kill: {killed_error.strip()}"
            return None, timeout_msg
        except FileNotFoundError:
            missing_cmd = "'wsl'" if sys.platform == 'win32' else "'searchsploit'"
            return None, f"Command {missing_cmd} not found. Ensure it's installed and in PATH."
        except PermissionError as e:
            return None, f"Permission denied executing searchsploit: {e}"
        except OSError as e:
            return None, f"OS error executing searchsploit: {e}"
        except Exception as e:
            return None, f"Critical error executing searchsploit: {str(e)}"

    def _handle_searchsploit_error(self, error_message, search_term_url):
        """Handles common searchsploit errors and logs messages."""
        error_lower = error_message.lower()

        if "command not found" in error_lower:
            if "'wsl'" in error_lower and sys.platform == 'win32':
                self.log_message("\n[!] Error: WSL (Windows Subsystem for Linux) is not found or not installed.", '#FF0000')
                self.log_message("  SpyEye uses 'searchsploit' via WSL on Windows.")
                self.log_message("  1. Install WSL: In PowerShell (Admin), run `wsl --install` (reboot may be needed).")
                self.log_message("  2. Install a Linux distribution (e.g., Kali Linux) from the Microsoft Store.")
                self.log_message("  3. Inside your Linux distro, install exploitdb: `sudo apt update && sudo apt install exploitdb`.")
            elif "'searchsploit'" in error_lower and sys.platform == 'win32':
                self.log_message("\n[!] Error: 'searchsploit' not found within your WSL environment.", '#FF0000')
                self.log_message("  Please install 'exploitdb' in your WSL Linux distribution:")
                self.log_message("  `sudo apt update && sudo apt install exploitdb`")
            else:
                self.log_message("\n[!] Error: 'searchsploit' command not found.", '#FF0000')
                self.log_message("  Please ensure 'exploitdb' (which includes searchsploit) is installed and in your system's PATH.")
                self.log_message("  For Debian/Ubuntu-based systems: `sudo apt update && sudo apt install exploitdb`.")
                self.log_message("  For other systems, check Exploit-DB's GitHub page for installation instructions.")
        elif "timed out" in error_lower:
            self.log_message(f"\n[!] Error: Local exploit search timed out: {error_message.strip()}", '#FF9900')
        elif "permission denied" in error_lower:
            self.log_message(f"\n[!] Error: Permission denied running searchsploit: {error_message.strip()}", '#FF0000')
        else:
            self.log_message(f"\n[!] Local exploit search error: {error_message.strip()}", '#FF0000')

        self.log_message(f"[*] As an alternative, you can search online at Exploit-DB: {search_term_url}", '#FFA500')
        try:
            if webbrowser.open_new_tab(search_term_url):
                self.log_message(f"    Attempted to open the above URL in your web browser.", '#FFA500')
            else:
                self.log_message(f"    Please copy the URL above into your browser.", '#FFA500')
        except Exception as e_web:
            self.log_message(f"    Could not open URL in browser ({e_web}). Please copy it manually.", '#FFA500')

    def search_exploit(self):
        """Searches for exploits using 'searchsploit', with refined error handling and web fallback."""
        search_term = self.exploit_entry.get().strip()
        if not search_term:
            self.log_message("[!] Please enter a search term (e.g., 'Apache 2.4').", '#FF0000')
            return

        self.log_message(f"\n[*] Searching local exploits for: '{search_term}'...")
        output, error = self._execute_searchsploit(search_term)

        url_search_term = search_term.replace(' ', '%20')
        exploit_db_url = f"https://www.exploit-db.com/search?q={url_search_term}"

        if error:
            self._handle_searchsploit_error(error, exploit_db_url)
            return

        if output is None:
            self.log_message("[!] Exploit search failed (no output returned from command).", '#FF0000')
            self._handle_searchsploit_error("Unknown execution error.", exploit_db_url)
            return

        if not output.strip():
            self.log_message(f"[-] No local exploits found for '{search_term}'.", color='#FFFF00')
            self.log_message(f"[*] You can try searching online at Exploit-DB: {exploit_db_url}", '#FFA500')
            try:
                if webbrowser.open_new_tab(exploit_db_url):
                    self.log_message(f"    Attempted to open the above URL in your web browser.", '#FFA500')
                else:
                    self.log_message(f"    Please copy the URL above into your browser.", '#FFA500')
            except Exception as e_web:
                self.log_message(f"    Could not open URL in browser ({e_web}). Please copy it manually.", '#FFA500')
            return

        self.log_message("\n[+] === Local Exploit Search Results ===")
        clean_results = re.sub(r'\x1b(\[([0-9]{1,2}(;[0-9]{1,2})*)?[m|K]|][0-9]+;[^\a]*(?:\a|\x07))', '', output)
        self.log_message(clean_results.strip())

    def load_scan_count(self):
        """Loads the scan count from the JSON file."""
        try:
            if os.path.exists(self.scan_data_file):
                with open(self.scan_data_file, 'r') as f:
                    data = json.load(f)
                    loaded_count = data.get('scan_count', 0)
                    self.scan_count = int(loaded_count) if isinstance(loaded_count, (int, float)) and loaded_count >= 0 else 0
            else:
                self.scan_count = 0
        except (IOError, OSError, json.JSONDecodeError, ValueError) as e:
            print(f"SpyEye Info: Could not load scan count from {self.scan_data_file}: {e}. Resetting count to 0.")
            self.scan_count = 0
        except Exception as e:
            print(f"SpyEye Info: Unexpected error loading scan count: {e}. Resetting count to 0.")
            self.scan_count = 0
        self.update_scan_counter_label()

    def save_scan_count(self):
        """Saves the current scan count to the JSON file."""
        try:
            with open(self.scan_data_file, 'w') as f:
                json.dump({'scan_count': self.scan_count}, f)
        except (IOError, OSError) as e:
            print(f"SpyEye Info: Could not save scan count to {self.scan_data_file}: {e}")
        except Exception as e:
            print(f"SpyEye Info: Unexpected error saving scan count: {e}")

    def update_scan_counter_label(self):
        """Updates the scan counter label in the GUI."""
        remaining_scans = self.max_scans - self.scan_count
        self.scan_counter_label.config(
            text=f"Remaining scans: {remaining_scans if remaining_scans >= 0 else 0}"
        )

def scan_port_worker(target_ip, port_num, timeout, results_queue):
    """Scans a single port. Worker for threads."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        connection_result = sock.connect_ex((target_ip, port_num))
        if connection_result == 0:
            service_name = "unknown"
            try:
                service_name = socket.getservbyport(port_num)
            except (OSError, socket.error):
                pass
            results_queue.put((port_num, "open", service_name))
        sock.close()
    except socket.timeout:
        pass
    except socket.error:
        pass
    except Exception as e:
        print(f"SpyEye Debug: Unexpected error in scan_port_worker (IP: {target_ip}, Port: {port_num}): {e}")
        pass

def main():
    """Initializes and runs the SpyEye GUI application."""
    init(autoreset=True)
    root = ThemedTk(theme="black")
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    app = PortScannerGUI(root_window=root)
    root.mainloop()

def on_closing(root_window):
    """Handles window close event."""
    print("SpyEye application is closing.")
    root_window.destroy()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Application terminated by user (KeyboardInterrupt).{Fore.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}[X] A critical unexpected error occurred in main: {e}{Fore.RESET}")
        sys.exit(1)
