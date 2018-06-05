import threading
import time
import socket
from configparser import ConfigParser


class io_thread(threading.Thread):

    def __init__(self, sock, filename, buffer_size):
        threading.Thread.__init__(self)
        self.sock = sock
        self.buffer_size = buffer_size
        self.filename = filename

    def run(self):
        fp = open(self.filename, 'rb')
        self.sock.send(bytes(self.filename, encoding='utf8'))
        buff = self.sock.recv(16)
        print(str(buff, encoding='utf8'))

        while(True):
            buff = fp.read(self.buffer_size)
            if not buff:
                break
            self.sock.send(buff)
        self.sock.close()
        fp.close()


def main():
    cfg = ConfigParser()
    cfg.read('config.ini')

    IP = cfg.get('server', 'ip')
    PORT = cfg.getint('server', 'port')
    FILE = cfg.get('file', 'file')
    SIZE = cfg.getint('env', 'buffer_size')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, PORT))
    fd = sock.fileno()
    io = io_thread(sock=sock, filename="./64mb.dat", buffer_size=SIZE)

    start_time = time.time()
    io.start()
    io.join()
    end_time = time.time()
    print("completion time: ", end_time - start_time)


if __name__ == '__main__':
    main()
