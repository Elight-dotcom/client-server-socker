
import sys, threading, datetime
from socket import *

# ====== WARNA ======
RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"

def timestamp():
    return datetime.datetime.now().strftime('%H:%M:%S')

class TCPServer:
    @staticmethod
    def safe_print(msg):
        sys.stdout.write("\033[2K\r")
        print(msg)
        sys.stdout.write(CYAN + "INPUT >> " + RESET)
        sys.stdout.flush()

    def __init__(self):
        if len(sys.argv) != 3:
            print('Penggunaan:' + sys.argv[0] + ' [ip address] [port]')
            sys.exit(1)
        else:
            self.HOST = sys.argv[1]
            self.PORT = int(sys.argv[2])

        self.running = True
        self.connections = []
        self.client_names = {}

    def Create(self):
        try:
            self.sockTCP = socket(AF_INET, SOCK_STREAM)
            self.sockTCP.bind((self.HOST, self.PORT))
            self.sockTCP.listen(5)
        except Exception as e:
            print(RED + 'Gagal membuat socket TCP: ' + str(e) + RESET)
            sys.exit(1)
        else:
            print(GREEN)
            print(f"╔═══════════════════════════════════════════╗")
            print(f"║   SERVER STARTED ({self.HOST}:{self.PORT})   ║")
            print(f"╚═══════════════════════════════════════════╝" + RESET)

    # =========== BROADCAST ===========
    def broadcast(self, message, sender=None):
        for conn in self.connections:
            if conn != sender:
                try:
                    conn.send(message.encode())
                except:
                    conn.close()
                    self.connections.remove(conn)

    # =========== HANDLING CLIENT ===========
    def handle_client(self, koneksi, alamat):
        client_name = koneksi.recv(1024).decode()
        self.client_names[koneksi] = client_name
        msg = CYAN + f"[{timestamp()}] Client {alamat[0]}:{alamat[1]} CONNECTED Name: {client_name}" + RESET
        self.safe_print(msg)
        self.broadcast(msg, sender=koneksi)

        self.connections.append(koneksi)

        while True:
            try:
                data = koneksi.recv(1024)
                if not data:
                    break
            except:
                break

            msg = data.decode()
            formatted = YELLOW + f"[{timestamp()}] {self.client_names[koneksi]} >> " + RESET + msg
            print(formatted)

            self.broadcast(formatted, sender=koneksi)

        disconnect = RED + f"[{timestamp()}] {self.client_names[koneksi]} DISCONNECTED" + RESET
        self.safe_print(disconnect + RED + f" ({alamat[0]}:{alamat[1]})" + RESET)
        self.broadcast(disconnect, sender=koneksi)

        if koneksi in self.connections:
            koneksi.close()
            self.connections.remove(koneksi)

    # =========== KICK CLIENT ==============
    def kick_client(self, target):
        for conn in self.connections:
            if self.client_names[conn] == target:
                conn.send((RED + "You have been kicked by server.\n" + RESET).encode())
                conn.close()
                self.connections.remove(conn)
                return True
            
        return False
            
    # ========== RENAME CLIENT ==============
    def rename_client(self, old_name, new_name):
        for conn in self.connections:
            if self.client_names[conn] == old_name:
                self.client_names[conn] = new_name
                return True
            
        return False

    # =========== CHECKING FOR INPUT =============
    def check_input(self, message):
        if message.strip() == ":list":
            self.safe_print(GREEN + f"[{timestamp()}] SERVER: {len(self.connections)} client(s) connected" + RESET)
            for conn in self.connections:
                try:
                    print("- " + CYAN + self.client_names[conn] + YELLOW + f" ({conn.getpeername()[0]}:{conn.getpeername()[1]})")
                except:
                    pass
            return

        if message.startswith(":kick "):
            target = message.split(" ", 1)[1].strip()
            if target == "":
                self.safe_print(RED + f"Usage: :kick <username>" + RESET)
                return
            
            success = self.kick_client(target)
            if not success:
                self.safe_print(RED + f"Client {target} not found" + RESET)
                return
            
            self.safe_print(GREEN + f"Client {target} has been kicked" + RESET)
            return
        
        if message.startswith(":rename "):
            parts = message.split(" ", 2)
            if len(parts) < 3:
                self.safe_print(RED + "Usage: :rename <old> <new>" + RESET)
                return
            old = parts[1]
            new = parts[2]

            success = self.rename_client(old, new)
            if not success:
                self.safe_print(RED + f"Client {old} not found" + RESET)
                return
            
            self.safe_print(GREEN + f"Client {old} has been renamed to {new}" + RESET)
            return

        if message.strip() == ":shutdown":
            shut_down = RED + f"[{timestamp()}] SERVER: Server shutting down..." + RESET
            print(shut_down)
            self.broadcast(shut_down)

            self.running = False
            self.sockTCP.close()
            sys.exit(0)

        print(RED + "Invalid command" + RESET)


    # =========== INPUT SERVER ===========
    def server_input(self):
        while True:
            message = input(CYAN + "INPUT >> " + RESET)

            if message.startswith(":"): 
                self.check_input(message)
                continue

            formatted = GREEN + f"[{timestamp()}] SERVER: {message}" + RESET
            print(formatted)

            self.broadcast(formatted)

    def Procesess(self):
        threading.Thread(target=self.server_input, daemon=True).start()

        print(MAGENTA + f"[{timestamp()}] Waiting for client..." + RESET)

        while self.running:
            try:
                koneksi, alamat = self.sockTCP.accept()

                if not self.running:
                    koneksi.close()
                    break

                threading.Thread(
                    target=self.handle_client, 
                    args=(koneksi, alamat),
                    daemon=True
                ).start()
            except OSError:
                pass

    def Run(self):
        self.Create()
        self.Procesess()


if __name__ == '__main__':
    TCPServer().Run()
