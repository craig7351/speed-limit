import sys
import ctypes
import tkinter as tk
from tkinter import messagebox
from traffic_shaper import BandwidthLimiter

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_admin():
    """Relaunch as admin if not already."""
    if not is_admin():
        # Re-run the program with admin rights
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to elevate privileges: {e}")
        sys.exit()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 11 Global Bandwidth Limiter")
        self.root.geometry("400x250")
        
        self.limiter = BandwidthLimiter()
        self.is_running = False

        # UI Elements
        tk.Label(root, text="Global Download Limit (Mbps):").pack(pady=5)
        self.entry_dl = tk.Entry(root)
        self.entry_dl.insert(0, "0")
        self.entry_dl.pack(pady=5)
        tk.Label(root, text="(0 = Unlimited)").pack()

        tk.Label(root, text="Global Upload Limit (Mbps):").pack(pady=5)
        self.entry_ul = tk.Entry(root)
        self.entry_ul.insert(0, "0")
        self.entry_ul.pack(pady=5)
        tk.Label(root, text="(0 = Unlimited)").pack()

        self.btn_state = tk.Button(root, text="START Limiting", command=self.toggle_limiting, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.btn_state.pack(pady=20)

        self.lbl_status = tk.Label(root, text="Status: Stopped", fg="red")
        self.lbl_status.pack(side=tk.BOTTOM, pady=10)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def toggle_limiting(self):
        if not self.is_running:
            # Start
            try:
                dl = float(self.entry_dl.get())
                ul = float(self.entry_ul.get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for limits.")
                return

            if dl < 0 or ul < 0:
                messagebox.showerror("Invalid Input", "Limits cannot be negative.")
                return

            self.limiter.set_limits(dl, ul)
            
            try:
                self.limiter.start()
                self.is_running = True
                self.btn_state.config(text="STOP Limiting", bg="#f44336")
                self.lbl_status.config(text=f"Status: Running (DL: {dl} Mbps, UL: {ul} Mbps)", fg="green")
                
                # Disable inputs
                self.entry_dl.config(state='disabled')
                self.entry_ul.config(state='disabled')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start limiter: {e}\n\nMake sure WinDivert driver is supported.")
        else:
            # Stop
            self.limiter.stop()
            self.is_running = False
            self.btn_state.config(text="START Limiting", bg="#4CAF50")
            self.lbl_status.config(text="Status: Stopped", fg="red")
            
            # Enable inputs
            self.entry_dl.config(state='normal')
            self.entry_ul.config(state='normal')

    def on_closing(self):
        if self.is_running:
            self.limiter.stop()
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    check_admin()
    root = tk.Tk()
    app = App(root)
    root.mainloop()
