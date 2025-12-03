#!usr/bin/env python

import sys
from socket import *

class TCPServer:
    def __init__(self):
        if len(sys.argv) != 3:
            print('Penggunaan:' + sys.argv[0] + ' [ip address] [port]')
            sys.exit(1)
        else:
            self.HOST = sys.argv[1]
            self.PORT = int(sys.argv[2])
        
    def Create(self):
        try:
            self.sockTCP = socket(AF_INET, SOCK_STREAM)
            self.sockTCP.bind((self.HOST, self.PORT))
            self.sockTCP.listen(5)
        except Exception as e:
            print('Gagal membuat socket TCP:', e)
            sys.exit(1)
        else:
            print('Server Message [tekan Ctrl+C untuk keluar]')
            print('----------------------------------')
            print('Mendengarkan pada %s:%d' % (self.HOST, self.PORT))
        
    def Accept(self):
        while True:
            koneksi, alamat = self.sockTCP.accept()
            print('Koneksi dari %s:%d' % (alamat[0], alamat[1]))

            while True:
                data = koneksi.recv(1024)
                if not data:
                    print('Koneksi ditutup oleh client.')
                    break

                text = data.decode()
                print('Pesan dari Client >> ' + text)

                balasan = input("Server >> ")
                koneksi.send(balasan.encode())

            koneksi.close()   # tutup koneksi client, kembali menunggu client baru
            
    def Run(self):
        self.Create()
        self.Accept()

    def __del__(self):
        print('\nSocket TCP ditutup. Terima kasih!')
        try: self.sockTCP.close()
        except: pass

if __name__ == '__main__':
    TCPServer().Run()
