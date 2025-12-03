#!usr/bin/env python

import sys
import socket
import threading
import time

if len(sys.argv) != 3:
    print('Usage: test_client.py [host] [port]')
    sys.exit(1)

HOST = sys.argv[1]
PORT = int(sys.argv[2])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((HOST, PORT))
except Exception as e:
    print('Gagal connect:', e)
    sys.exit(1)

print('Terhubung ke server', HOST, PORT)

# start a receiver thread to print data from server

def receiver(sock):
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                print('Server menutup koneksi')
                break
            print('Server >>', data.decode())
    except Exception as e:
        print('Receive error:', e)

threading.Thread(target=receiver, args=(s,), daemon=True).start()

# send a few messages then close
messages = ['Halo server!', 'Test dari client', 'Selesai']
for m in messages:
    print('Client >>', m)
    s.send(m.encode())
    time.sleep(0.5)

# wait a bit to receive any replies then close
time.sleep(1)
s.close()
print('Client closed')
