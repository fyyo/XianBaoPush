# precheck.py - A lightweight pre-checker for essential dependencies.
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import importlib.util
import threading

# 模块名 -> 包名 的映射
ESSENTIAL_MODULES = {
    "PyQt6": "PyQt6",
    "PyQt6.QtWebEngineWidgets": "PyQt6-WebEngine",
    "requests": "requests",
    "flask": "Flask"
}

def check_dependencies():
    """检查核心依赖是否存在"""
    missing = []
    for module_name, package_name in ESSENTIAL_MODULES.items():
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            missing.append(package_name)
    return missing

def install_dependencies(on_finish_callback):
    """在一个新线程中安装所有依赖"""
    def do_install():
        try:
            command = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.run(command, check=True, startupinfo=startupinfo)
            on_finish_callback(True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            on_finish_callback(False, str(e))

    thread = threading.Thread(target=do_install)
    thread.daemon = True
    thread.start()

def launch_main_app():
    """启动主应用程序"""
    try:
        pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe") if "python.exe" in sys.executable else sys.executable
        subprocess.Popen([pythonw_exe, "main.py"])
    except Exception as e:
        messagebox.showerror("启动失败", f"无法启动主程序: {e}")

class PrecheckApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw() # 初始隐藏窗口
        self.check_and_proceed()

    def check_and_proceed(self):
        missing = check_dependencies()
        if not missing:
            # 环境正常，直接启动主应用并退出预检
            self.root.destroy()
            launch_main_app()
        else:
            # 缺少依赖，显示安装引导窗口
            self.show_installer_window(missing)

    def show_installer_window(self, missing_packages):
        installer_window = tk.Toplevel(self.root)
        installer_window.title("环境预检")
        installer_window.geometry("400x200")
        installer_window.resizable(False, False)
        self.center_window(installer_window)

        label = tk.Label(installer_window, text=f"检测到缺失的核心依赖：\n\n{', '.join(missing_packages)}\n\n请点击下方按钮进行安装。", wraplength=380)
        label.pack(pady=20)

        self.install_button = ttk.Button(installer_window, text="一键安装依赖", command=lambda: self.start_installation(installer_window))
        self.install_button.pack(pady=10)
        
        self.progress = ttk.Progressbar(installer_window, orient="horizontal", length=300, mode="indeterminate")

    def start_installation(self, window):
        self.install_button.config(state="disabled", text="正在安装...")
        self.progress.pack(pady=10)
        self.progress.start()
        
        install_dependencies(lambda success, error=None: self.on_installation_finished(success, error, window))

    def on_installation_finished(self, success, error, window):
        self.progress.stop()
        self.progress.pack_forget()
        
        if success:
            messagebox.showinfo("安装成功", "所有依赖已成功安装！应用即将启动。")
            window.destroy()
            self.root.destroy()
            launch_main_app()
        else:
            messagebox.showerror("安装失败", f"依赖安装失败，请手动安装。\n\n错误: {error}")
            self.install_button.config(state="normal", text="重试安装")

    def center_window(self, win):
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
    root = tk.Tk()
    app = PrecheckApp(root)
    root.mainloop()