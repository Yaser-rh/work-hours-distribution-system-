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
            text="Choose an option to launch the application interface",
            text_color="#718096",
            font=ctk.CTkFont(family="Segoe UI", size=13, slant="italic")
        )
        self.subtitle_label.pack(pady=(0, 30))
        
        # Button 1: Legacy Desktop UI
        self.btn_legacy = ctk.CTkButton(
            self.main_frame,
            text="1. Legacy Desktop UI",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            height=50,
            width=350,
            fg_color="#4a5568",
            hover_color="#2d3748",
            command=self.run_legacy_ui
        )
        self.btn_legacy.pack(pady=10)
        
        # Button 2: Simple One-Function UI
        self.btn_simple = ctk.CTkButton(
            self.main_frame,
            text="2. Simple One-Function UI (Future Update)",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            height=50,
            width=350,
            fg_color="#1a202c",
            hover_color="#2d3748",
            command=self.run_simple_ui
        )
        self.btn_simple.pack(pady=10)
        
        # Button 3: Flask Web UI (Recommended)
        self.btn_web = ctk.CTkButton(
            self.main_frame,
            text="3. Web UI (Flask Server)",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            height=50,
            width=350,
            fg_color="#1a365d",
            hover_color="#2b6cb0",
            command=self.run_web_ui
        )
        self.btn_web.pack(pady=10)
        
        # Footer
        self.footer_label = ctk.CTkLabel(
            self.main_frame,
            text="Unified Solver Launcher • Compiled EXE Ready",
            text_color="#a0aec0",
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.footer_label.pack(side="bottom", pady=15)

    def run_legacy_ui(self):
        self.withdraw()
        
        # Ensure 'legacy code' folder is in search path
        legacy_path = os.path.join(ROOT_DIR, "legacy code")
        if legacy_path not in sys.path:
            sys.path.append(legacy_path)
            
        try:
            from ui.main_gui import TimesheetAppGUI
            
            legacy_root = ctk.CTk()
            legacy_root.title("Timesheet Generator - Legacy Desktop UI")
            legacy_root.geometry("1150x800")
            legacy_root.minsize(1050, 700)
            
            app = TimesheetAppGUI(legacy_root)
            
            def on_close():
                legacy_root.destroy()
                self.deiconify()
                
            legacy_root.protocol("WM_DELETE_WINDOW", on_close)
            legacy_root.mainloop()
        except Exception as e:
            self.deiconify()
            from tkinter import messagebox
            messagebox.showerror("Legacy UI Error", f"Failed to launch Legacy Desktop UI:\n{e}")

    def run_simple_ui(self):
        self.withdraw()
        
        simple_window = ctk.CTk()
        simple_window.title("Simple One-Function UI")
        simple_window.geometry("500x320")
        
        # Center simple window
        sw = 500
        sh = 320
        sx = (self.winfo_screenwidth() // 2) - (sw // 2)
        sy = (self.winfo_screenheight() // 2) - (sh // 2)
        simple_window.geometry(f"{sw}x{sh}+{sx}+{sy}")
        simple_window.resizable(False, False)
        
        # Frame
        frame = ctk.CTkFrame(simple_window, corner_radius=15)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title = ctk.CTkLabel(
            frame,
            text="Simple One-Function UI",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        title.pack(pady=(35, 10))
        
        desc = ctk.CTkLabel(
            frame,
            text="This is a placeholder for the simplified layout.\nIt will be fully implemented in a future update.\n\nPlease select another option to use the application.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#a0aec0"
        )
        desc.pack(pady=20)
        
        btn_back = ctk.CTkButton(
            frame,
            text="Back to Launcher",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=180,
            height=40,
            command=lambda: [simple_window.destroy(), self.deiconify()]
        )
        btn_back.pack(pady=15)
        
        simple_window.protocol("WM_DELETE_WINDOW", lambda: [simple_window.destroy(), self.deiconify()])
        simple_window.mainloop()

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
