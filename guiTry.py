# PyQt5 GUI + TCP Server Thread Integration

import sys, threading, datetime
from socket import *
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QLineEdit, QLabel

# ==========================
#  Utility
# ==========================
def timestamp():
    return datetime.datetime.now().strftime('%H:%M:%S')


# ==========================
#  Server Thread Wrapper
# ==========================
class ServerThread(threading.Thread):
    @staticmethod
    def safe_print(msg):
        sys.stdout.write("\033[2K\r")
        print(msg)
        sys.stdout.write(CYAN + "INPUT >> " + RESET)
        sys.stdout.flush()

    def __init__(self, host, port, callback_log):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.callback_log = callback_log
        self.connections = []

    def log(self, msg):
        self.callback_log(f"[{timestamp()}] {msg}")

    def broadcast(self, message, sender=None):
        for conn in self.connections:
            if conn != sender:
                try:
                    conn.send(message.encode())
                except:
                    conn.close()
                    self.connections.remove(conn)

    def handle_client(self, conn, addr):
        self.connections.append(conn)
        self.log(f"CLIENT CONNECTED {addr[0]}:{addr[1]}")

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
            except:
                break

            msg = data.decode()
            self.log(f"CLIENT {addr[0]}:{addr[1]} >> {msg}")

            self.broadcast(f"[{timestamp()}] {addr[0]}:{addr[1]}: {msg}", sender=conn)

        conn.close()
        self.connections.remove(conn)
        self.log(f"CLIENT DISCONNECTED {addr[0]}:{addr[1]}")

    def run(self):
        try:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.bind((self.host, self.port))
            sock.listen(5)
            self.log(f"SERVER STARTED on {self.host}:{self.port}")
        except Exception as e:
            self.log(f"ERROR: {e}")
            return

        while True:
            conn, addr = sock.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()


# ==========================
#  Qt Signal Bridge
# ==========================
class LogBridge(QObject):
    log_signal = pyqtSignal(str)


# ==========================
#  Main GUI Window
# ==========================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TCP Server GUI (PyQt5)")
        self.setGeometry(200, 200, 600, 450)

        self.bridge = LogBridge()
        self.bridge.log_signal.connect(self.appendLog)

        # Input Host
        self.inputHost = QLineEdit(self)
        self.inputHost.setPlaceholderText("Host IP")
        self.inputHost.setText("127.0.0.1")
        self.inputHost.move(20, 20)
        self.inputHost.resize(150, 30)

        # Input Port
        self.inputPort = QLineEdit(self)
        self.inputPort.setPlaceholderText("Port")
        self.inputPort.setText("5000")
        self.inputPort.move(180, 20)
        self.inputPort.resize(100, 30)

        # Start Button
        self.btnStart = QPushButton("Start Server", self)
        self.btnStart.move(300, 20)
        self.btnStart.resize(120, 30)
        self.btnStart.clicked.connect(self.startServer)

        # Log Output
        self.textLog = QTextEdit(self)
        self.textLog.setReadOnly(True)
        self.textLog.move(20, 70)
        self.textLog.resize(560, 350)

    def appendLog(self, text):
        self.textLog.append(text)

    def startServer(self):
        host = self.inputHost.text()
        port = int(self.inputPort.text())

        self.server = ServerThread(host, port, self.bridge.log_signal.emit)
        self.server.start()

        self.bridge.log_signal.emit(f"[{timestamp()}] GUI: Server starting...")


# ==========================
#  Main Entry
# ==========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
