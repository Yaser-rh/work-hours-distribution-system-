import os
import sys
import threading
import webbrowser
import subprocess
import time
import socket
import customtkinter as ctk

# Safe stream redirection for PyInstaller --windowed (GUI) mode where sys.stdout/sys.stderr are None
class DummyWriter:
    def write(self, s):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

if sys.stdout is None:
    sys.stdout = DummyWriter()
if sys.stderr is None:
    sys.stderr = DummyWriter()

# Ensure workspace root is in path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Configure customtkinter appearance
ctk.set_appearance_mode("System")

def open_browser_url(url="http://127.0.0.1:5000"):
    try:
        opened = webbrowser.open(url)
        if not opened:
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            subprocess.Popen(f'start "" "{url}"', shell=True, creationflags=creationflags)
    except Exception:
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        subprocess.Popen(f'start "" "{url}"', shell=True, creationflags=creationflags)

def kill_port_owner(port=5000):
    try:
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        output = subprocess.check_output("netstat -ano", shell=True, creationflags=creationflags).decode()
        pids_to_kill = set()
        current_pid = str(os.getpid())
        for line in output.strip().split('\n'):
            if "LISTENING" in line and f":{port}" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit() and pid != "0" and pid != current_pid:
                        pids_to_kill.add(int(pid))
        
        for pid in pids_to_kill:
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)
    except Exception:
        pass

def wait_for_port(host="127.0.0.1", port=5000, timeout=12.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.4):
                return True
        except Exception:
            time.sleep(0.2)
    return False

class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Timesheet & Shift System Launcher")
        self.geometry("600x450")
        self.resizable(False, False)
        
        # Center window
        self.center_window(600, 450)
        
        # Tracking variables
        self.flask_started = False
        self.flask_thread = None
        self.server_error = None
        
        # UI Container
        self.container = ctk.CTkFrame(self, corner_radius=15)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Setup views
        self.setup_main_view()
        self.setup_web_console_view()
        
        # Start at main view
        self.show_main_view()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_main_view(self):
        self.main_view = ctk.CTkFrame(self.container, fg_color="transparent")
        
        # Header/Title
        self.title_label = ctk.CTkLabel(
            self.main_view,
            text="Timesheet Distribution System",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
        )
        self.title_label.pack(pady=(30, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self.main_view,
            text="Launch the ShiftPlan Web System",
            text_color="#718096",
            font=ctk.CTkFont(family="Segoe UI", size=13, slant="italic")
        )
        self.subtitle_label.pack(pady=(0, 30))
        
        # Primary Launch Button: Web UI
        self.btn_web = ctk.CTkButton(
            self.main_view,
            text="🚀 Launch ShiftPlan System (Web UI)",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=55,
            width=380,
            fg_color="#1a365d",
            hover_color="#2b6cb0",
            command=self.run_web_ui
        )
        self.btn_web.pack(pady=20)
        
        # Footer
        self.footer_label = ctk.CTkLabel(
            self.main_view,
            text="Unified Solver Launcher • Compiled EXE Ready",
            text_color="#a0aec0",
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.footer_label.pack(side="bottom", pady=15)

    def setup_web_console_view(self):
        self.web_view = ctk.CTkFrame(self.container, fg_color="transparent")
        
        title = ctk.CTkLabel(
            self.web_view,
            text="Web UI Control Panel",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
        )
        title.pack(pady=(25, 10))
        
        self.status_var = ctk.StringVar(value="Starting Flask server...")
        self.status_label = ctk.CTkLabel(
            self.web_view,
            textvariable=self.status_var,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#3182ce"
        )
        self.status_label.pack(pady=10)
        
        desc = ctk.CTkLabel(
            self.web_view,
            text="The Flask server is hosting the timesheet app.\nClick 'Open Browser' if the window does not launch automatically.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a0aec0"
        )
        desc.pack(pady=15)

        self.btn_browser = ctk.CTkButton(
            self.web_view,
            text="🔗 Open Browser",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            width=220,
            height=45,
            fg_color="#2f855a",
            hover_color="#22543d",
            command=lambda: open_browser_url("http://127.0.0.1:5000")
        )
        self.btn_browser.pack(pady=10)
        
        self.btn_back = ctk.CTkButton(
            self.web_view,
            text="🔙 Back to Launcher",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            width=180,
            height=35,
            fg_color="#4a5568",
            hover_color="#2d3748",
            command=self.show_main_view
        )
        self.btn_back.pack(pady=15)

    def show_main_view(self):
        self.web_view.pack_forget()
        self.main_view.pack(fill="both", expand=True)

    def show_web_console_view(self):
        self.main_view.pack_forget()
        self.web_view.pack(fill="both", expand=True)

    def set_status_safe(self, text, color):
        self.after(0, lambda: self._update_status(text, color))

    def _update_status(self, text, color):
        self.status_var.set(text)
        self.status_label.configure(text_color=color)

    def run_web_ui(self):
        self.show_web_console_view()
        
        if not self.flask_started:
            self.set_status_safe("Starting Flask server...", "#3182ce")
            
            def run_server():
                try:
                    from app import app as flask_app, initialize_database
                    initialize_database()
                    import logging
                    logging.getLogger('werkzeug').setLevel(logging.ERROR)
                    flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
                except Exception as e:
                    self.server_error = str(e)
                    self.set_status_safe(f"Server error: {e}", "#e53e3e")
                    
            self.flask_thread = threading.Thread(target=run_server, daemon=True)
            self.flask_thread.start()
            self.flask_started = True
            
        def check_ready_and_open():
            if wait_for_port(port=5000, timeout=12.0):
                self.set_status_safe("Flask Server running at http://127.0.0.1:5000", "#38a169")
                open_browser_url("http://127.0.0.1:5000")
            else:
                if not self.server_error:
                    self.set_status_safe("Server error: Timed out waiting for port 5000.", "#e53e3e")
                    
        threading.Thread(target=check_ready_and_open, daemon=True).start()

if __name__ == "__main__":
    kill_port_owner(5000)
    app = LauncherApp()
    app.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    app.mainloop()


