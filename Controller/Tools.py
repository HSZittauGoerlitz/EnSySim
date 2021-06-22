from collections import namedtuple
import random
import torch
from torch import nn


Transition = namedtuple('Transition',
                        ('state', 'action', 'nextState', 'costs', 'done'))


class ReplayMemory(object):
    """ Source: pytorch DQN tutorial """
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, *args):
        """Saves a transition."""
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


class DQN_MLP(nn.Module):
    def __init__(self, nState, nActions, nHL1, nHL2):
        """ Init DQN network

        Args:
            nState (int): Number of State Variables
            nActions (int): Number of of possible controller actions
        """
        super(DQN_MLP, self).__init__()
        self.inLayer = nn.Linear(nState, nHL1)
        self.H1Layer = nn.Linear(nHL1, nHL2)
        self.H2Layer = nn.Linear(nHL2, nActions)
        self.outLayer = nn.Linear(nActions, nActions)

    def forward(self, xb):
        xb = self.inLayer(xb)
        xb = torch.sigmoid(self.H1Layer(xb))
        xb = torch.sigmoid(self.H2Layer(xb))
        return self.outLayer(xb)
