import os
import sys
import threading
import webbrowser
import customtkinter as ctk

# Ensure workspace root is in path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Configure customtkinter appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Timesheet & Shift System Launcher")
        self.geometry("600x450")
        self.resizable(False, False)
        
        # Center window
        self.center_window(600, 450)
        
        # UI Elements
        self.setup_ui()
        
        # Flask tracking
        self.flask_started = False
        self.flask_thread = None

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        # Background/Frame styling
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header/Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Timesheet Distribution System",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
        )
        self.title_label.pack(pady=(30, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Launch the ShiftPlan Web System",
            text_color="#718096",
            font=ctk.CTkFont(family="Segoe UI", size=13, slant="italic")
        )
        self.subtitle_label.pack(pady=(0, 30))
        
        # Primary Launch Button: Web UI
        self.btn_web = ctk.CTkButton(
            self.main_frame,
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
            self.main_frame,
            text="Unified Solver Launcher • Compiled EXE Ready",
            text_color="#a0aec0",
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.footer_label.pack(side="bottom", pady=15)

    def run_web_ui(self):
        self.withdraw()
        
        web_window = ctk.CTk()
        web_window.title("Flask Web Server Console")
        web_window.geometry("550x380")
        
        ww = 550
        wh = 380
        wx = (self.winfo_screenwidth() // 2) - (ww // 2)
        wy = (self.winfo_screenheight() // 2) - (wh // 2)
        web_window.geometry(f"{ww}x{wh}+{wx}+{wy}")
        web_window.resizable(False, False)
        
        frame = ctk.CTkFrame(web_window, corner_radius=15)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title = ctk.CTkLabel(
            frame,
            text="Web UI Control Panel",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        title.pack(pady=(25, 10))
        
        status_var = ctk.StringVar(value="Starting Flask server...")
        status_label = ctk.CTkLabel(
            frame,
            textvariable=status_var,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#3182ce"
        )
        status_label.pack(pady=10)
        
        desc = ctk.CTkLabel(
            frame,
            text="The Flask server is hosting the timesheet app.\nClick 'Open Browser' if the window does not launch automatically.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a0aec0"
        )
        desc.pack(pady=15)
        
        btn_browser = ctk.CTkButton(
            frame,
            text="🔗 Open Browser",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            width=200,
            height=45,
            fg_color="#2f855a",
            hover_color="#22543d",
            command=lambda: webbrowser.open("http://localhost:5000")
        )
        btn_browser.pack(pady=10)
        
        btn_back = ctk.CTkButton(
            frame,
            text="🔙 Back to Launcher",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            width=180,
            height=35,
            fg_color="#4a5568",
            hover_color="#2d3748",
            command=lambda: [web_window.destroy(), self.deiconify()]
        )
        btn_back.pack(pady=15)
        
        # Start Flask if not already started
        if not self.flask_started:
            from app import app as flask_app, initialize_database
            
            def run_server():
                try:
                    initialize_database()
                    flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
                except Exception as e:
                    status_var.set("Server error: Address already in use or crashed.")
                    status_label.configure(text_color="#e53e3e")
                    
            self.flask_thread = threading.Thread(target=run_server, daemon=True)
            self.flask_thread.start()
            self.flask_started = True
            
        # Update status
        status_var.set("Flask Server running at http://localhost:5000")
        status_label.configure(text_color="#38a169")
        
        # Auto-open browser
        webbrowser.open("http://localhost:5000")
        
        web_window.protocol("WM_DELETE_WINDOW", lambda: [web_window.destroy(), self.deiconify()])
        web_window.mainloop()

def kill_port_owner(port):
    import subprocess
    try:
        # Query netstat to find listening process PIDs on port
        output = subprocess.check_output("netstat -ano", shell=True).decode()
        pids_to_kill = set()
        for line in output.strip().split('\n'):
            if "LISTENING" in line and f":{port}" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit() and pid != "0":
                        pids_to_kill.add(int(pid))
        
        # Force terminate identified processes
        for pid in pids_to_kill:
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

if __name__ == "__main__":
    # Self-heal on startup by freeing port 5000 if occupied
    kill_port_owner(5000)
    
    app = LauncherApp()
    # Force kill background daemon threads on window close
    app.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    app.mainloop()
