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


class env():
    """ """
    def __init__(self, fd, buff_size, time):
        self.fd = fd
        self.buff_size = buff_size
        self.time = time
        self.last = []
        self.count = 1

    """ adjust info to get goodput """
    def adjust(self, state):
        goodput = [state[i][2] - self.last[i] for i in range(len(state))]
        self.last = [sub_info[2] for sub_info in state]
        for i in range(len(state)):
            state[i][2] = goodput[i]
        return state

    """ reset env, return the initial state  """
    def reset(self):
        mpsched.persist_state(self.fd)
        time.sleep(1)
        state = mpsched.get_info(self.fd)
        self.last = [sub_info[2] for sub_info in state]
        time.sleep(self.time)
        state = mpsched.get_info(self.fd)
        return self.adjust(state)

    """ action = [sub1_buff_size, sub2_buff_size] """
    def step(self, action):
        # A = [self.fd, action[0], action[1]]
        # mpsched.set_seg(A)
        time.sleep(self.time)
        state_nxt = mpsched.get_info(self.fd)
        done = False
        #print(state_nxt)
        if len(state_nxt) == 0:
            done = True
        self.count = self.count + 1
        return self.adjust(state_nxt), self.count, done


def main():
    cfg = ConfigParser()
    cfg.read('config.ini')

    IP = cfg.get('server', 'ip')
    PORT = cfg.getint('server', 'port')
    FILE = cfg.get('file', 'file')
    SIZE = cfg.getint('env', 'buffer_size')
    TIME = cfg.getint('env', 'time')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, PORT))
    fd = sock.fileno()
    io = io_thread(sock=sock, filename=FILE, buffer_size=SIZE)
    mpsched.persist_state(fd)

    io.start()
    my_env = env(fd=fd, buff_size=SIZE, time=TIME)

    state=my_env.reset()
    while True:
        action = []
        state_nxt, count, done = my_env.step(action)
        if done:
            break
        print(state_nxt)
    print(count)

    io.join()


if __name__ == '__main__':
    main()
