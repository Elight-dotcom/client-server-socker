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
BOLD = "\033[1m"
DIM = "\033[2m"

def timestamp():
    return datetime.datetime.now().strftime('%H:%M:%S')

class TCPServer:
    def __init__(self):
        if len(sys.argv) != 3:
            print(f'{RED}Penggunaan: {sys.argv[0]} [ip address] [port]{RESET}')
            sys.exit(1)
        else:
            self.HOST = sys.argv[1]
            self.PORT = int(sys.argv[2])

        self.running = True
        self.connections = []
        self.client_names = {}
        self.groups = {}

    def Create(self):
        try:
            self.sockTCP = socket(AF_INET, SOCK_STREAM)
            self.sockTCP.bind((self.HOST, self.PORT))
            self.sockTCP.listen(5)
        except Exception as e:
            print(f'{RED}╔═══════════════════════════════════════════╗')
            print(f'║  ✖ Gagal membuat socket TCP               ║')
            print(f'║  Error: {str(e):<32}║')
            print(f'╚═══════════════════════════════════════════╝{RESET}')
            sys.exit(1)
        else:
            print(f"\n{GREEN}{BOLD}╔═══════════════════════════════════════════╗")
            print(f"║                                           ║")
            print(f"║          🌐 TCP CHAT SERVER 🌐            ║")
            print(f"║                                           ║")
            print(f"║  ✓ Address: {self.HOST:<28}  ║")
            print(f"║  ✓ Port   : {self.PORT:<28}  ║")
            print(f"║                                           ║")
            print(f"╚═══════════════════════════════════════════╝{RESET}\n")

    # ========== SAFE PRINT ===========
    @staticmethod
    def safe_print(msg):
        sys.stdout.write("\033[2K\r")
        print(msg)
        sys.stdout.write(f"{CYAN}{BOLD}SERVER » {RESET}")
        sys.stdout.flush()

    # =========== BROADCAST ===========
    def broadcast(self, message, sender=None):
        for conn in self.connections:
            if conn != sender:
                try:
                    conn.send(message.encode())
                except:
                    conn.close()
                    self.connections.remove(conn)

    # =========== PRIVATE MESSAGE ===========
    def private_message(self, sender, target, message):
        for conn in self.connections:
            if conn != sender and self.client_names[conn] == target:
                try:
                    formatted = f"{MAGENTA}[{timestamp()}] {DIM}PM{RESET} {MAGENTA}{self.client_names[sender]} → You:{RESET} {message}"
                    conn.send(formatted.encode())
                    self.safe_print(f"{MAGENTA}[{timestamp()}] {DIM}PM{RESET} {MAGENTA}{self.client_names[sender]} → {target}:{RESET} {message}")
                except:
                    conn.close()
                    self.connections.remove(conn)
                return True
        return False
    
    # =========== GROUP ===========
    def create_group(self, sender, group_name):
        if group_name in self.groups:
            sender.send(f"{RED}✖ Group '{group_name}' already exists{RESET}".encode())
            return
        self.groups[group_name] = [sender]
        sender.send(f"{GREEN}✓ Group '{group_name}' created successfully{RESET}".encode())
        self.safe_print(f"{GREEN}[{timestamp()}] {DIM}GROUP{RESET} {GREEN}'{group_name}' created by {self.client_names[sender]}{RESET}")
    
    def join_group(self, sender, group_name):
        if group_name not in self.groups:
            sender.send(f"{RED}✖ Group '{group_name}' not found{RESET}".encode())
            return
        if sender in self.groups[group_name]:
            sender.send(f"{RED}✖ You are already in group '{group_name}'{RESET}".encode())
            return
        self.groups[group_name].append(sender)
        sender.send(f"{GREEN}✓ Joined group '{group_name}'{RESET}".encode())
        self.safe_print(f"{GREEN}[{timestamp()}] {DIM}GROUP{RESET} {GREEN}{self.client_names[sender]} joined '{group_name}'{RESET}")
        
    def leave_group(self, sender, group_name):
        if group_name not in self.groups:
            sender.send(f"{RED}✖ Group '{group_name}' not found{RESET}".encode())
            return
        if sender not in self.groups[group_name]:
            sender.send(f"{RED}✖ You are not in group '{group_name}'{RESET}".encode())
            return
        self.groups[group_name].remove(sender)
        sender.send(f"{GREEN}✓ Left group '{group_name}'{RESET}".encode())
        self.safe_print(f"{YELLOW}[{timestamp()}] {DIM}GROUP{RESET} {YELLOW}{self.client_names[sender]} left '{group_name}'{RESET}")
    
    def send_to_group(self, sender, group_name, message):
        if group_name not in self.groups:
            sender.send(f"{RED}✖ Group '{group_name}' not found{RESET}".encode())
            return
        if sender not in self.groups[group_name]:
            sender.send(f"{RED}✖ You are not in group '{group_name}'{RESET}".encode())
            return
        sender_name = self.client_names[sender]
        formatted = f"{BLUE}[{timestamp()}] {DIM}@{group_name}{RESET} {BLUE}{sender_name}:{RESET} {message}"

        for conn in self.groups[group_name]:
            if conn != sender:
                conn.send(formatted.encode())

        self.safe_print(formatted)
    
    def list_group_members(self, sender, group_name):
        if group_name not in self.groups:
            sender.send(f"{RED}✖ Group '{group_name}' not found{RESET}".encode())
            return
        
        sender.send(f"{GREEN}━━━ Members of '{group_name}' ━━━{RESET}\n".encode())
        for i, conn in enumerate(self.groups[group_name], 1):
            sender.send(f"{CYAN}  {i}. {self.client_names[conn]}{RESET}\n".encode())
        sender.send(f"{GREEN}━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n".encode())
    
    # =========== CHECK INPUT USER ==========
    def check_input_user(self, sender, message):
        if message.startswith(":pm "): 
            parts = message.split(" ", 2)
            if len(parts) < 3:
                sender.send(f"{RED}✖ Usage: :pm <target> <message>{RESET}".encode())
                return
            target = parts[1].strip()
            msg = " ".join(parts[2:]).strip()
            success = self.private_message(sender, target, msg)
            if not success:
                sender.send(f"{RED}✖ Client '{target}' not found{RESET}".encode())
            return
        
        if message.startswith(":group "): 
            parts = message.split(" ", 3)
            if len(parts) < 2:
                sender.send(f"{RED}✖ Usage: :group <command>{RESET}".encode())
                return
            
            cmd = parts[1]

            if cmd == "create":
                if len(parts) < 3:
                    sender.send(f"{RED}✖ Usage: :group create <group_name>{RESET}".encode())
                    return
                group_name = parts[2].strip()
                self.create_group(sender, group_name)
                return

            if cmd == "join":
                if len(parts) < 3:
                    sender.send(f"{RED}✖ Usage: :group join <group_name>{RESET}".encode())
                    return
                group_name = parts[2].strip()
                self.join_group(sender, group_name)
                return

            if cmd == "leave":
                if len(parts) < 3:
                    sender.send(f"{RED}✖ Usage: :group leave <group_name>{RESET}".encode())
                    return
                group_name = parts[2].strip()
                self.leave_group(sender, group_name)
                return

            if cmd == "send":
                if len(parts) < 4:
                    sender.send(f"{RED}✖ Usage: :group send <group_name> <message>{RESET}".encode())
                    return
                group_name = parts[2].strip()
                msg = parts[3].strip()
                self.send_to_group(sender, group_name, msg)
                return

            if cmd == "members":
                if len(parts) < 3:
                    sender.send(f"{RED}✖ Usage: :group members <group_name>{RESET}".encode())
                    return
                group_name = parts[2].strip()
                self.list_group_members(sender, group_name)
                return
        
        sender.send(f"{RED}✖ Invalid command{RESET}".encode())
        
    # =========== HANDLING CLIENT ===========
    def handle_client(self, koneksi, alamat):
        client_name = koneksi.recv(1024).decode()
        self.client_names[koneksi] = client_name
        msg = f"{GREEN}[{timestamp()}] {DIM}CONNECT{RESET} {GREEN}{client_name}{RESET} {DIM}({alamat[0]}:{alamat[1]}){RESET}"
        self.safe_print(msg)
        self.broadcast(f"{GREEN}[{timestamp()}] ➜ {client_name} joined the chat{RESET}", sender=koneksi)

        self.connections.append(koneksi)

        while True:
            try:
                data = koneksi.recv(1024)
                if not data:
                    break
            except:
                break

            msg = data.decode()

            if msg.startswith(":"): 
                self.check_input_user(koneksi, msg)
                continue

            formatted = f"{YELLOW}[{timestamp()}] {self.client_names[koneksi]}:{RESET} {msg}"
            self.safe_print(formatted)
            self.broadcast(formatted, sender=koneksi)

        disconnect = f"{RED}[{timestamp()}] {DIM}DISCONNECT{RESET} {RED}{self.client_names[koneksi]}{RESET} {DIM}({alamat[0]}:{alamat[1]}){RESET}"
        self.safe_print(disconnect)
        self.broadcast(f"{RED}[{timestamp()}] ➜ {self.client_names[koneksi]} left the chat{RESET}", sender=koneksi)

        if koneksi in self.connections:
            koneksi.close()
            self.connections.remove(koneksi)

    # =========== KICK CLIENT ==============
    def kick_client(self, target):
        for conn in self.connections:
            if self.client_names[conn] == target:
                conn.send(f"{RED}✖ You have been kicked by server{RESET}\n".encode())
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
    
    # =========== PRIVATE MESSAGE SERVER ===============
    def private_message_server(self, target, message):
        for conn in self.connections:
            if self.client_names[conn] == target:
                conn.send(f"{YELLOW}[{timestamp()}] {DIM}SERVER PM{RESET} {YELLOW}→ You:{RESET} {message}".encode())
                return True
        return False

    # =========== CHECKING FOR INPUT =============
    def check_input(self, message):
        if message.strip() == ":list":
            self.safe_print(f"\n{CYAN}━━━ Connected Clients ({len(self.connections)}) ━━━{RESET}")
            for i, conn in enumerate(self.connections, 1):
                try:
                    peer = conn.getpeername()
                    self.safe_print(f"{CYAN}  {i}. {BOLD}{self.client_names[conn]}{RESET} {DIM}({peer[0]}:{peer[1]}){RESET}")
                except:
                    pass
            self.safe_print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
            return

        if message.startswith(":kick "):
            target = message.split(" ", 1)[1].strip()
            if target == "":
                self.safe_print(f"{RED}✖ Usage: :kick <username>{RESET}")
                return
            
            success = self.kick_client(target)
            if not success:
                self.safe_print(f"{RED}✖ Client '{target}' not found{RESET}")
                return
            
            self.safe_print(f"{GREEN}✓ Client '{target}' has been kicked{RESET}")
            return
        
        if message.startswith(":pm "):
            parts = message.split(" ", 2)
            if len(parts) < 3:
                self.safe_print(f"{RED}✖ Usage: :pm <username> <message>{RESET}")
                return
            target = parts[1].strip()
            msg = parts[2].strip()

            success = self.private_message_server(target, msg)
            if not success:
                self.safe_print(f"{RED}✖ Client '{target}' not found{RESET}")
                return
            
            self.safe_print(f"{GREEN}✓ Private message sent to '{target}'{RESET}")
            return
        
        if message.startswith(":rename "):
            parts = message.split(" ", 2)
            if len(parts) < 3:
                self.safe_print(f"{RED}✖ Usage: :rename <old> <new>{RESET}")
                return
            old = parts[1]
            new = parts[2]

            success = self.rename_client(old, new)
            if not success:
                self.safe_print(f"{RED}✖ Client '{old}' not found{RESET}")
                return
            
            self.safe_print(f"{GREEN}✓ Client '{old}' renamed to '{new}'{RESET}")
            return

        if message.strip() == ":shutdown":
            shut_down = f"\n{RED}{BOLD}╔═══════════════════════════════════════════╗\n║  🛑 SERVER SHUTTING DOWN...               ║\n╚═══════════════════════════════════════════╝{RESET}\n"
            print(shut_down)
            self.broadcast(f"{RED}[{timestamp()}] ⚠ Server is shutting down...{RESET}")

            self.running = False
            self.sockTCP.close()
            sys.exit(0)

        self.safe_print(f"{RED}✖ Invalid command{RESET}")

    # =========== INPUT SERVER ===========
    def server_input(self):
        while True:
            message = input(f"{CYAN}{BOLD}SERVER » {RESET}")

            if message.startswith(":"): 
                self.check_input(message)
                continue

            formatted = f"{GREEN}[{timestamp()}] {DIM}SERVER:{RESET} {GREEN}{message}{RESET}"
            print(formatted)
            self.broadcast(formatted)

    def Procesess(self):
        threading.Thread(target=self.server_input, daemon=True).start()
        print(f"{MAGENTA}[{timestamp()}] {DIM}STATUS{RESET} {MAGENTA}Waiting for clients...{RESET}\n")

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