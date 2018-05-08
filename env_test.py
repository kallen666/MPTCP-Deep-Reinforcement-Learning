import argparse
import gym
import numpy as np
from gym import wrappers
from gym import spaces

import torch
from ddpg_cnn import DDPG_CNN

from normalized_actions import NormalizedActions
from ounoise import OUNoise
from replay_memory import ReplayMemory, Transition



class env():
    """ """
    def __init__(self):
        self.observation_space = spaces.Box(np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]), np.array([float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf"),float("inf")]))
        
        self.action_space = spaces.Box(np.array([1]), np.array([4]))

    

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
        state = np.array([[1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6],[1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6]])
        state = torch.FloatTensor(state)
        return state

    """ action = [sub1_buff_size, sub2_buff_size] """
    def step(self, action):
        state = np.array([[1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6],[1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6]])
        state = torch.FloatTensor(state)
        reward = 1
        done = 0
        return state, reward, done


def main():
    my_env = env()
    
    agent = DDPG_CNN(0.99, 0.001, 128,
                      my_env.observation_space.shape[0], my_env.action_space)
    
    parser = argparse.ArgumentParser(description='PyTorch REINFORCE example')
    parser.add_argument('--noise_scale', type=float, default=0.3, metavar='G',
                    help='initial noise scale (default: 0.3)')
    parser.add_argument('--final_noise_scale', type=float, default=0.3, metavar='G',
                    help='final noise scale (default: 0.3)')      
    parser.add_argument('--exploration_end', type=int, default=100, metavar='N',
                    help='number of episodes with noise (default: 100)')
    args = parser.parse_args()
    
    ounoise = OUNoise(my_env.action_space.shape[0])
    ounoise.scale = (args.noise_scale - args.final_noise_scale) * max(0, args.exploration_end - 1) / args.exploration_end + args.final_noise_scale
    ounoise.reset()

    state = my_env.reset()
    i = 10
    while i>0:
        action = agent.select_action(state, ounoise)
        print("action: {}".format(action))
        next_state, reward, done = my_env.step(action)
        if done:
            break
        print(reward)
        i = i-1
    

    

if __name__ == '__main__':
    main()
