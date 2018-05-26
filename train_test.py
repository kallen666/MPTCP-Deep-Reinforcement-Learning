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
    def __init__(self, fd, buff_size, time, k, l, n, p):
        self.fd = fd
        self.buff_size = buff_size
        self.k = k  ##对以往k个时间段的观测
        self.l = l  ##吞吐量的奖励因子
        #self.m = m  ##RTT惩罚因子
        self.n = n  ##缓冲区膨胀惩罚因子
        self.p = p  ##重传惩罚因子
        self.time = time
        self.last = []
        self.tp = [[], []]
        self.rtt = [[], []]
        self.cwnd = [[], []]
        self.rr = 0
        self.count = 1
        self.recv_buff_size = 0


    """ adjust info to get goodput """
    def adjust(self, state):
        for j in range(len(state)):
            self.tp[j].pop(0)
            self.tp[j].append(state[j][0]-self.last[j])
            self.rtt[j].pop(0)
            self.rtt[j].append(state[j][1])
            self.cwnd[j].pop(0)
            self.cwnd[j].append(state[j][2])
        self.last = [x[0] for x in state]
        mate = mpsched.get_meta_info(self.fd)
        self.recv_buff_size = mate[0]
        self.rr = mate[1] - self.rr
        return [self.tp[0] + self.rtt[0] + self.cwnd[0] + [self.recv_buff_size, self.rr], self.tp[1] + self.rtt[1] + self.cwnd[1]+ [self.recv_buff_size, self.rr]]

    def reward(self):
        rewards = self.l * (sum(self.tp[0]) + sum(self.tp[1]))
        #rewards = rewards - self.m * (sum(self.rtt[0]) + sum(self.rtt[1]))
        rewards = rewards + self.n * self.recv_buff_size
        rewards = rewards - self.p * self.rr
        return rewards

    """ reset env, return the initial state  """
    def reset(self):
        mpsched.persist_state(self.fd)
        time.sleep(1)
        self.last = [x[0] for x in mpsched.get_sub_info(self.fd)]

        for i in range(self.k):
            subs = mpsched.get_sub_info(self.fd)
            for j in range(len(subs)):
                 self.tp[j].append(subs[j][0]-self.last[j])
                 self.rtt[j].append(subs[j][1])
                 self.cwnd[j].append(subs[j][2])
            self.last = [x[0] for x in subs]
            time.sleep(self.time)
        mate = mpsched.get_meta_info(self.fd)
        self.recv_buff_size = mate[0]
        self.rr = mate[1]
        return [self.tp[0] + self.rtt[0] + self.cwnd[0] + [self.recv_buff_size, self.rr], self.tp[1] + self.rtt[1] + self.cwnd[1]+ [self.recv_buff_size, self.rr]]

    """ action = [sub1_buff_size, sub2_buff_size] """
    def step(self, action):
        # A = [self.fd, action[0], action[1]]
        # mpsched.set_seg(A)
        time.sleep(self.time)
        state_nxt = mpsched.get_sub_info(self.fd)
        done = False
        if len(state_nxt) == 0:
            done = True
        self.count = self.count + 1
        return self.adjust(state_nxt), self.reward(), self.count, self.recv_buff_size, done


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
    my_env = env(fd=fd, buff_size=SIZE, time=TIME, k=4, l=0.01, n=0.03, p=0.05)
    lines = []
    state = my_env.reset()
    start_time = time.time()
    while True:
        action = []
        state_nxt, reward, count, recv_buff_size, done = my_env.step(action)
        if done:
            break
        #print(reward)
        #print(recv_buff_size)
        #print(state_nxt[0][0]," ", state_nxt[1][0])
        lines.append(str(state_nxt[0][0]) + " "+str(state_nxt[1][0])+"\n")
    end_time = time.time();
    print(count)
    fo = open("seg_rr.txt", "w")
    fo.writelines(lines)
    fo.close()
    print("completion time: ", end_time - start_time)
    io.join()


if __name__ == '__main__':
    main()
