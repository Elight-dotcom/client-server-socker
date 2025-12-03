#! /usr/bin/env python
import socket, threading
from socket import *
import sys

# ====== WARNA ======
RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"

class TCPClient:
    @staticmethod
    def safe_print(msg):
        sys.stdout.write("\033[2K\r")
        print(msg)
        sys.stdout.write(CYAN + "YOU >> " + RESET)
        sys.stdout.flush()

    def __init__(self):
        if len(sys.argv) != 3:
            print(RED + 'Penggunaan: ' + sys.argv[0] + ' [ip_server] [port] [nama]' + RESET)
            sys.exit(1)
        else:
            self.HOST = sys.argv[1]
            self.PORT = int(sys.argv[2])


    def Create(self):
        try:
            self.sockTCP = socket(AF_INET, SOCK_STREAM)
            self.sockTCP.connect((self.HOST, self.PORT))
            pesan = input(CYAN + "NAME : " + RESET)
            self.sockTCP.send(pesan.encode())
        except Exception as e:
            print(RED + 'Gagal membuat socket TCP: ' + str(e) + RESET)
            sys.exit(1)
        else:
            print(GREEN)
            print(f"╔══════════════════════════════════════╗") 
            print(f"║   CONNECTED ({self.HOST}:{self.PORT})   ║") 
            print(f"╚══════════════════════════════════════╝" + RESET)

    def handle_receive(self):
        while True:
            try:
                data = self.sockTCP.recv(1024)
                if not data:
                    self.safe_print(RED + "Disconnected from server" + RESET)
                    break
                self.safe_print(data.decode())
            except:
                break

    def handle_send(self):
        while True:
            pesan = input(CYAN + "YOU >> " + RESET)
            if pesan.strip() == "":
                continue
            try:
                self.sockTCP.send(pesan.encode())
            except:
                break

    def Process(self):
        threading.Thread(target=self.handle_receive, daemon=True).start()
        threading.Thread(target=self.handle_send, daemon=True).start()

        # tunggu selamanya tanpa load CPU
        threading.Event().wait()

    def Run(self):
        self.Create()
        self.Process()


if __name__ == "__main__":
    TCPClient().Run()
