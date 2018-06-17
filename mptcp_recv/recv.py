import socket
import threading
import info
import time


class recv_thread(threading.Thread):

    def __init__(self, sock, buff_size=2048):
        threading.Thread.__init__(self)
        self.sock = sock
        self.buffer_size = buff_size

    def run(self):
        buff = self.sock.recv(self.buffer_size)
        filename = str(buff, encoding='utf8')
        fp = open(filename, 'wb')
        if not fp:
            print("open file error.\n")
            self.sock.send(bytes("open file error.", encoding='utf8'))
            pass
        else:
            self.sock.send(bytes("ok", encoding='utf8'))
            while(True):
                buff = self.sock.recv(self.buffer_size)
                if not buff:
                    break
                else:
                    fp.write(buff)
            print("recieve file {} from sender finished.".format(filename))
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
                f.write('%d %d %d\n' % (self.data[i][0], self.data[i][1], self.data[i][2]))
        f.close()

    def load(self, datafile):
        self.datafile = datafile
        try:
            f = open(datafile, 'r')
            self.timestep = float(f.readline())
            lenth = int(f.readline())
            for i in range(lenth):
                s = f.readline().split(' ')
                self.data.append([int(s[0]), int(s[1]), int(s[2])])
        finally:
            if f:
                f.close()

    def put(self, recd):
        self.data.append(recd)

    def draw(self):
        pass


def main():
    server = socket.socket()
    host = '*'
    port = 6669
    server.bind((host, port))

    server.listen(1)
    num = 0;
    while True:
        c, addr = server.accept()
        print('connect addr : {}'.format(addr))
        fd = c.fileno()
        io = recv_thread(fd)
        info.persist_state(fd)
        io.start()

        timestep = 0.2
        r = record(timestep=timestep, datafile="record{}".format(num))
        time.sleep(1)
        while True:
            time.sleep(timestep)
            data = info.get_info(fd)
            if len(data) == 0:
                io.join()
                break
            r.put(data)

        r.save()
        num = num + 1


if __name__ == '__main__':
    main()
