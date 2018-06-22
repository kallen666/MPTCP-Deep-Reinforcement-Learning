import threading
import time
import socket
from configparser import ConfigParser
import mpsched


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


class record(object):
    """docstring for record."""
    def __init__(self, timestep=0.2, datafile="record"):
        self.data = []
        self.timestep = timestep
        self.datafile = datafile

    def save(self):
        lenth = len(self.data)
        with open(self.datafile, 'w') as f:
            f.write(str(self.timestep))
            f.write('\n')
            f.write(str(lenth))
            f.write('\n')
            for i in range(lenth):
                f.write('%d %d\n' % (self.data[i][0][1], self.data[i][1][1]))
        f.close()

    def put(self, recd):
        self.data.append(recd)

    def draw(self):
        pass


def main():
    cfg = ConfigParser()
    cfg.read('config.ini')

    IP = cfg.get('server', 'ip')
    PORT = cfg.getint('server', 'port')
    FILE = cfg.get('file', 'file')
    SIZE = cfg.getint('env', 'buffer_size')
    timestep = cfg.getfloat('env', 'time')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, PORT))
    fd = sock.fileno()

    io = io_thread(sock=sock, filename='./256mb.dat', buffer_size=SIZE)
    

    start_time = time.time()
    io.start()
    io.join();
   
    end_time = time.time()
    print("completion time: ", end_time - start_time)


if __name__ == '__main__':
    main()
