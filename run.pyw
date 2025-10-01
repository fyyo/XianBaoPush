# run.pyw - Windows launcher to run the application without a console window.
import sys
import subprocess

def main():
    """
    Executes the precheck script using pythonw.exe to ensure no console window appears.
    """
    try:
        # We use pythonw.exe to ensure that even the precheck script itself doesn't flash a console window.
        subprocess.Popen([sys.executable.replace("python.exe", "pythonw.exe"), "precheck.py"])
    except Exception as e:
        # This is a fallback for critical errors, will show a simple tkinter error.
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw() # Hide the main window
        messagebox.showerror("Fatal Error", f"Failed to launch the application prechecker:\n\n{e}")
        root.destroy()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())