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
    def __init__(self, fd, buff_size, time, k, l, m, n, p):
        self.fd = fd
        self.buff_size = buff_size
        self.k = k  ##对以往k个时间段的观测
        self.time = time
        self.last = []
        self.list = []
        self.count = 1
        self.l = l  ##吞吐量的奖励因子
        self.m = m  ##RTT惩罚因子
        self.n = n  ##缓冲区膨胀惩罚因子
        self.p = p  ##重传惩罚因子

    """ adjust info to get goodput """
    def adjust(self, state):
        temp = []
        for j in range(len(state)):
             temp.append([state[j][0]-self.last[j][0], state[j][1], state[j][2], state[j][3]])
        self.last = state
        self.list.pop(0)
        self.list.append(temp)
        return self.list

    def reward(self):
        rewards = 0;
        for i in range(self.k):
             temp = self.list[i]
             for j in range(len(temp)):
                 rewards = rewards + self.l * temp[j][0]
        temp = self.list[-1]
        for j in range(len(temp)):
            rewards = rewards - self.m*temp[j][1] - self.n * temp[j][2] - self.p * (temp[j][3] - self.list[0][j][3])
        return rewards

    """ reset env, return the initial state  """
    def reset(self):
        mpsched.persist_state(self.fd)
        time.sleep(1)
        self.last = mpsched.get_info(self.fd)

        for i in range(self.k):
            state = mpsched.get_info(self.fd)
            temp = []
            for j in range(len(state)):
                 temp.append([state[j][0]-self.last[j][0], state[j][1], state[j][2], state[j][3]])
            self.last = state
            self.list.append(temp)
            time.sleep(self.time)

        return self.list

    """ action = [sub1_buff_size, sub2_buff_size] """
    def step(self, action):
        # A = [self.fd, action[0], action[1]]
        # mpsched.set_seg(A)
        time.sleep(self.time)
        state_nxt = mpsched.get_info(self.fd)
        done = False
        if len(state_nxt) == 0:
            done = True
        self.count = self.count + 1
        return self.adjust(state_nxt), self.reward(), self.count, done


def main():
    cfg = ConfigParser()
    cfg.read('config.ini')

    IP = cfg.get('server', 'ip')
    PORT = cfg.getint('server', 'port')
    FILE = cfg.get('file', 'file')
    SIZE = cfg.getint('env', 'buffer_size')
    TIME = cfg.getfloat('env', 'time')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, PORT))
    fd = sock.fileno()
    io = io_thread(sock=sock, filename=FILE, buffer_size=SIZE)
    mpsched.persist_state(fd)

    io.start()
    my_env = env(fd=fd, buff_size=SIZE, time=TIME, k=4, l=0.01, m=0.02, n=0.03, p=0.05)

    state = my_env.reset()
    while True:
        action = []
        state_nxt, reward, count, done = my_env.step(action)
        if done:
            break
        print(reward)
    print(count)

    io.join()


if __name__ == '__main__':
    main()
