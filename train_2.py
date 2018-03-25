import threading
import time
import socket
from configparser import ConfigParser
import mpsched


import argparse
import gym
import numpy as np
from gym import wrappers
from gym import spaces 

import torch
from ddpgMPTCP import DDPG
from normalized_actions import NormalizedActions
from ounoise import OUNoise
from replay_memory import ReplayMemory, Transition

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
        self.observation_space = spaces.Box(np.array([0,0,0,0,0]), np.array([float("inf"),float("inf"),float("inf"),float("inf"),float("inf")]))
        self.action_space = spaces.Box(np.array([1]), np.array([4]))

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
    
    parser = argparse.ArgumentParser(description='PyTorch REINFORCE example')
   
    parser.add_argument('--gamma', type=float, default=0.99, metavar='G',
                    help='discount factor for reward (default: 0.99)')                    
    parser.add_argument('--tau', type=float, default=0.001, metavar='G',
                    help='discount factor for model (default: 0.001)')                    
    parser.add_argument('--noise_scale', type=float, default=0.3, metavar='G',
                    help='initial noise scale (default: 0.3)')                
    parser.add_argument('--hidden_size', type=int, default=128, metavar='N',
                    help='number of hidden size (default: 128)')                    
    parser.add_argument('--replay_size', type=int, default=1000000, metavar='N',
                    help='size of replay buffer (default: 1000000)')
    parser.add_argument('--updates_per_step', type=int, default=5, metavar='N',
                    help='model updates per simulator step (default: 5)')
    parser.add_argument('--batch_size', type=int, default=1, metavar='N',
                    help='batch size (default: 128)')
                    
    io.start()
    my_env = env(fd=fd, buff_size=SIZE, time=TIME)
    
    args = parser.parse_args()
    agent = DDPG(args.gamma, args.tau, args.hidden_size,
                      my_env.observation_space.shape[0], my_env.action_space)
    memory = ReplayMemory(args.replay_size)
    ounoise = OUNoise(my_env.action_space.shape[0])
    

    state=my_env.reset()
    while True:
#        action = []
        state = torch.FloatTensor(state)
        print("state: {}\n ounoise: {}".format(state, ounoise))
        action = agent.select_action(state, ounoise)
        #print("action: {}".format(action))
        next_state, count, done = my_env.step(action)

        action = torch.FloatTensor(action)
        mask = torch.Tensor([not done])
        next_state = torch.FloatTensor(next_state)
        reward = torch.FloatTensor([float(count)]) #count -> reward  
        memory.push(state, action, mask, next_state, reward)
        #state = next_state
            
        if len(memory) > args.batch_size * 5:
            for _ in range(args.updates_per_step):
                transitions = memory.sample(args.batch_size)
                batch = Transition(*zip(*transitions))
                print("update",10*'--')
                agent.update_parameters(batch)      
                '''
                error:
               
  File "/home/han/githubfiles/pytorch-ddpg-naf/trian_2.py", line 150, in main
    agent.update_parameters(batch)

  File "/home/han/githubfiles/pytorch-ddpg-naf/ddpgMPTCP.py", line 140, in update_parameters
    expected_state_action_batch = reward_batch + (self.gamma * next_state_action_values)

RuntimeError: The size of tensor a (2) must match the size of tensor b (4) at non-singleton dimension 0

                '''
        
        if done:
            break
        # [[2, 4288, 1294, 1, 1], [1, 3492, 1160, 0, 1]]
        print("next state: {}".format(next_state))
        
    print(count)

    io.join()


if __name__ == '__main__':
    main()
