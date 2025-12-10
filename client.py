#! /usr/bin/env python
import socket, threading, time, sys
from socket import *
import datetime

# ====== WARNA ======
RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"

def timestamp():
    return datetime.datetime.now().strftime('%H:%M:%S')

class TCPClient:
    def __init__(self):
        if len(sys.argv) != 3:
            print(RED + 'Penggunaan: ' + sys.argv[0] + ' [ip_server] [port]' + RESET)
            sys.exit(1)
        else:
            self.HOST = sys.argv[1]
            self.PORT = int(sys.argv[2])
            self.client_name = ""  # Menyimpan nama client
            self.running = True
            self.sockTCP = None
            self.reconnect_timeout = 120  # 2 menit dalam detik
            self.is_connected = False

    def safe_print(self, msg):
        sys.stdout.write("\033[2K\r")
        print(msg)
        if self.is_connected:
            sys.stdout.write(CYAN +"YOU >> " + RESET)
        sys.stdout.flush()

    def connect_to_server(self):
        """Mencoba koneksi ke server"""
        try:
            self.sockTCP = socket(AF_INET, SOCK_STREAM)
            self.sockTCP.settimeout(5)  # Timeout untuk koneksi
            self.sockTCP.connect((self.HOST, self.PORT))
            self.sockTCP.settimeout(None)  # Remove timeout setelah terkoneksi
            
            # Kirim nama ke server sebagai pesan pertama
            self.sockTCP.send(self.client_name.encode())
            self.is_connected = True
            return True
        except Exception as e:
            if self.sockTCP:
                self.sockTCP.close()
            self.is_connected = False
            return False

    def attempt_reconnection(self):
        """Mencoba reconnect selama 2 menit"""
        print(YELLOW + f"\n[{timestamp()}] Mencoba menghubungkan kembali ke server..." + RESET)
        print(YELLOW + f"[{timestamp()}] Timeout reconnection: {self.reconnect_timeout} detik" + RESET)
        
        start_time = time.time()
        attempt = 1
        
        while time.time() - start_time < self.reconnect_timeout and self.running:
            try:
                elapsed = int(time.time() - start_time)
                remaining = self.reconnect_timeout - elapsed
                print(YELLOW + f"[{timestamp()}] Attempt {attempt}: Mencoba koneksi ({elapsed}s/{self.reconnect_timeout}s)..." + RESET)
                
                if self.connect_to_server():
                    print(GREEN + f"╔══════════════════════════════════════════════════════════╗") 
                    print(f"║ [{timestamp()}] RECONNECTED AS {self.client_name} ({self.HOST}:{self.PORT}) ║") 
                    print(f"╚══════════════════════════════════════════════════════════╝" + RESET)
                    return True
                
                # Tunggu 5 detik sebelum mencoba lagi
                for i in range(5):
                    if not self.running:
                        return False
                    time.sleep(1)
                    
                attempt += 1
                    
            except KeyboardInterrupt:
                print(RED + f"\n[{timestamp()}] Reconnection dibatalkan oleh user" + RESET)
                return False
        
        if self.running:
            print(RED + f"\n[{timestamp()}] Gagal reconnect setelah {self.reconnect_timeout} detik" + RESET)
        return False

    def Create(self):
        # Input nama terlebih dahulu
        self.client_name = input(CYAN + "NAME : " + RESET)
        
        # Coba koneksi pertama kali
        print(YELLOW + f"[{timestamp()}] Connecting to {self.HOST}:{self.PORT}..." + RESET)
        
        if not self.connect_to_server():
            print(RED + f"[{timestamp()}] Gagal koneksi ke server {self.HOST}:{self.PORT}" + RESET)
            
            # Coba reconnect
            if not self.attempt_reconnection():
                sys.exit(1)
        
        print(GREEN + f"╔══════════════════════════════════════════════════════════╗") 
        print(f"║ [{timestamp()}] CONNECTED AS {self.client_name} ({self.HOST}:{self.PORT}) ║") 
        print(f"╚══════════════════════════════════════════════════════════╝" + RESET)

    def handle_receive(self):
        while self.running:
            try:
                if not self.sockTCP or not self.is_connected:
                    time.sleep(1)
                    continue
                    
                data = self.sockTCP.recv(1024)
                if not data:
                    self.safe_print(RED + f"[{timestamp()}] Disconnected from server" + RESET)
                    self.is_connected = False
                    
                    # Coba reconnect
                    if self.attempt_reconnection():
                        continue
                    else:
                        self.running = False
                        break
                        
                message = data.decode()
                
                # Periksa jika pesan adalah perintah khusus dari server
                if "SERVER:" in message and "shutting down" in message:
                    self.safe_print(RED + f"[{timestamp()}] Server is shutting down..." + RESET)
                    self.is_connected = False
                    
                    # Tunggu 2 detik lalu coba reconnect
                    time.sleep(2)
                    if self.attempt_reconnection():
                        continue
                    else:
                        self.running = False
                        break
                
                # Periksa jika kita dikick
                if "You have been kicked by server" in message:
                    self.safe_print(RED + f"[{timestamp()}] {message}" + RESET)
                    self.safe_print(RED + f"[{timestamp()}] Press Enter to exit..." + RESET)
                    self.running = False
                    if self.sockTCP:
                        self.sockTCP.close()
                    break
                    
                    
                self.safe_print(message)
                
            except socket.timeout:
                continue
            except ConnectionResetError:
                if self.running:
                    self.safe_print(RED + f"[{timestamp()}] Connection reset by server" + RESET)
                    self.is_connected = False
                    if self.attempt_reconnection():
                        continue
                    else:
                        self.running = False
                        break
            except (ConnectionAbortedError, BrokenPipeError):
                self.safe_print(RED + f"[{timestamp()}] Connection aborted" + RESET)
                self.is_connected = False
                if self.attempt_reconnection():
                    continue
                else:
                    self.running = False
                    break
            except Exception as e:
                self.safe_print(RED + f"[{timestamp()}] Connection error: {str(e)}" + RESET)
                self.is_connected = False
                if self.attempt_reconnection():
                    continue
                else:
                    self.running = False
                    break

    def handle_send(self):
        while self.running:
            try:
                # Jika tidak terkoneksi, tampilkan prompt khusus
                if not self.is_connected:
                    # Tampilkan prompt sederhana selama reconnection
                    try:
                        input_str = RED + "DISCONNECTED >> " + RESET
                        pesan = input(input_str)
                        
                        if not self.running:
                            break
                            
                        if pesan.strip() == "":
                            continue
                            
                        if pesan.lower() == ":quit":
                            print(YELLOW + f"[{timestamp()}] Closing connection..." + RESET)
                            self.running = False
                            if self.sockTCP:
                                self.sockTCP.close()
                            break
                            
                        print(RED + f"[{timestamp()}] Not connected to server. Reconnecting..." + RESET)
                        continue
                    except EOFError:
                        print(YELLOW + f"\n[{timestamp()}] Closing connection..." + RESET)
                        self.running = False
                        break
                
                # Jika terkoneksi, tampilkan prompt normal
                pesan = input(CYAN + "YOU >> " + RESET)
                
                if not self.running:
                    break
                    
                if pesan.strip() == "":
                    continue
                    
                if pesan.lower() == ":quit":
                    print(YELLOW + f"[{timestamp()}] Closing connection..." + RESET)
                    self.running = False
                    if self.sockTCP:
                        self.sockTCP.close()
                    sys.exit(0)
                
                # Cek jika socket masih valid
                if not self.sockTCP or not self.is_connected or self.sockTCP._closed:
                    print(RED + f"[{timestamp()}] Not connected to server. Attempting to reconnect..." + RESET)
                    self.is_connected = False
                    if self.attempt_reconnection():
                        # Coba kirim ulang pesan
                        try:
                            self.sockTCP.send(pesan.encode())
                        except:
                            continue
                    else:
                        break
                else:
                    self.sockTCP.send(pesan.encode())
                    
            except EOFError:
                # Ctrl+D pressed
                print(YELLOW + f"\n[{timestamp()}] Closing connection..." + RESET)
                self.running = False
                if self.sockTCP:
                    self.sockTCP.close()
                sys.exit(0)
            except Exception as e:
                if not self.running:
                    break
                print(RED + f"[{timestamp()}] Failed to send message: {str(e)}" + RESET)

    def Process(self):
        # Thread untuk menerima pesan
        receive_thread = threading.Thread(target=self.handle_receive)
        receive_thread.daemon = True
        receive_thread.start()
        
        # Thread utama untuk mengirim pesan
        self.handle_send()

        self.running = False
        print(YELLOW + f"[{timestamp()}] Client Terminated..." + RESET)

    def Run(self):
        self.Create()
        self.Process()


if __name__ == "__main__":
    TCPClient().Run()