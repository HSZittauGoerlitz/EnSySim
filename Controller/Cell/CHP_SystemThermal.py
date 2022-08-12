from abc import ABC, abstractmethod
import math
import numpy as np
import plotly.graph_objects as go
import random
import torch
from torch import nn, optim
from typing import Tuple

from traitlets.traitlets import Bool
from CheckCostFunction import getCostInv

from Controller.Tools import DQN_MLP, ReplayMemory, Transition


class CtrlTemplate(ABC):
    @abstractmethod
    def step(self, StorageState: float, *args) -> Tuple[bool, bool]:
        pass


class CtrlDefault(CtrlTemplate):
    def __init__(self):
        self.STORAGE_LEVEL_H = 0.3
        self.STORAGE_LEVEL_L = 0.2
        self.STORAGE_LEVEL_LL = 0.05

    def step(self, StorageState, *args):
        """ Default controller strategy

        Arguments:
            StorageState {float} -- Relative charge of thermal storage (0 to 1)

        Returns:
            (bool, bool) -- Operational state of CHP and Boiler
                            (True => running)
        """
        CHPstate = False
        BoilerState = False

        if StorageState <= self.STORAGE_LEVEL_LL:
            BoilerState = True
            CHPstate = True
        elif (((StorageState <= self.STORAGE_LEVEL_L) and not CHPstate) or
              ((StorageState >= self.STORAGE_LEVEL_H) and BoilerState)):
            CHPstate = True

        return (CHPstate, BoilerState)


class CtrlBaselines(CtrlTemplate):
    def __init__(self, MaxPower_e: float, MaxPower_t: float):
        self._env = []
        self._feedback = []

        self.action = 0
        self.done = False

        self.reward = 1.

        # All possible actions: (CHP, Boiler)
        self.ACTIONS = [(False, False), (True, False),
                        (False, True), (True, True)]
        self.actionSize = len(self.ACTIONS)
        # size of observation vector
        self.stateSize = 7

        # System Parameter
        self.MaxPower_e = MaxPower_e
        self.MaxPower_t = MaxPower_t

        self.lastAction = random.randrange(self.actionSize)  # or always 0?
        self.lastState = np.zeros(self.stateSize)

    # feedback: [observation, reward, done]
    @property
    def reportFeedback(self):
        return self._feedback

    @reportFeedback.setter
    def reportFeedback(self, feedback):
        self._feedback = feedback
        for callback in self._env:
            callback(self._feedback)

    def feedbackConnection(self, callback):
        self._env.append(callback)

    def reset(self):
        self.StorageStateGrad = 0.
        self.ThermalDemandGrad = 0.

        self.lastState = np.zeros(self.stateSize)  # randomize??
        self.lastAction = 0
        self.done = False

    def _getRewards(self, state, aIdx):

        # check fulfilment of thermal demand -> stop criterion
        eDemand_t = state[4] - state[3]  # gen - load
        if eDemand_t != 0:
            return (self.reward, True)

        # if eDemand_t < -0.01 * self.MaxPower_t:
        #     return (self.reward, 1.)
        # elif eDemand_t > 0.01 * self.MaxPower_t:
        #     return (self.reward, 1.)

        extra_rewards = self.reward  # bonus for time step

        # hint for storage state
        storage = state[1]
        if storage > 0.1 or storage < 0.9:
            extra_rewards += 0.05 * self.reward

        if storage > 0.05 or storage < 0.95:
            extra_rewards += 0.03 * self.reward

        boiler = state[6]
        # prefer chp over boiler
        if boiler:
            extra_rewards -= 0.03 * self.reward

        # add consistency
        chp = state[5]
        if chp == self.lastState[5]:
            extra_rewards += 0.02 * self.reward

        return (extra_rewards, False)

    def step(self, StorageState, CellState, Ambient):
        # prepare boundary conditions
        gen_e, load_e, gen_t, load_t, contrib_e, contrib_t, fuel = CellState
        Eg, solEl, solAz, Tout, Tmean = Ambient

        load_t = load_t / self.MaxPower_t
        gen_t = gen_t / self.MaxPower_t

        if np.all((self.lastState == 0)):
            self.lastState[1] = StorageState
            self.lastState[3] = load_t

        self.StorageStateGrad = (StorageState - self.lastState[1]) / 0.25  # t
        self.ThermalDemandGrad = (load_t - self.lastState[3]) / 0.25

        Chp, Boiler = self.ACTIONS[self.lastAction]

        observation = np.array([self.StorageStateGrad,
                                StorageState,
                                self.ThermalDemandGrad,
                                load_t,
                                gen_t,
                                Chp,
                                Boiler], dtype=np.float32)

        rewards, done = self._getRewards(observation, self.action)

        self.lastAction = self.action.copy()
        self.lastState = observation.copy()

        self.reportFeedback = [observation, rewards, done, {}]

        return (self.ACTIONS[self.action][0],
                self.ACTIONS[self.action][1],
                self.done)


class CtrlSmartSimple(CtrlTemplate):
    def __init__(self, capacity: int, batchSize: int,
                 epsStart: float, epsMin: float, epsDecay: int, cMax: float,
                 targetUpdate: int, nHL1: int, nHL2: int,
                 trainHistSize: int,
                 MaxPower_e: float, MaxPower_t: float, MaxFuelDemand: float,
                 visualise: Bool):
        """ Init Smart cell controller for thermal CHP Systems

        Arguments:
            capacity {int} -- Size of process memory
            batchSize {int} -- Number of samples used from memory
                               for each training
            epsStart {float} -- Initial value for Epsilon (epsMin to 1.)
            epsMin {float} -- Minimum value for Epsilon (0. to 1.)
            epsDecay {int} -- Strength of Epsilon decay
                              (after this number of Epochs Epsilon is
                               approx 0.5 of Start-End)

            targetUpdate {int} -- Rate of Epochs to update target model
            nHL1 {int} -- Number of Neurons in Q Models fist Hidden Layer
            nHL2 {int} -- Number of Neurons in Q Models second Hidden Layer
            trainHistSize {int} -- Size of history for training progress
            MaxPower_e {float} -- Max. possible electrical Power of
                                  thermal System [W]
            MaxPower_t {float} -- Max. possible thermal Power of
                                  thermal System [W]
            MaxFuelDemand {float} -- Max. Fuel demand of thermal System [W]
            visualise {Bool} -- When true, the batch costs are shown to see
                                training progress

        Raises:
            ValueError: Reports erroneous inputs
        """
        if batchSize < 1:
            raise ValueError("Size of Training Batches must be greater than 0")

        if capacity < batchSize:
            raise ValueError("Memory Capacity must be at least equal to "
                             "Batch Size. It's recommended, that the Capacity "
                             "is much greater than the Batch Size.")

        if epsMin < 0.:
            raise ValueError("Min. Epsilon must be between 0. and 1.")

        if epsStart < epsMin:
            raise ValueError("Starting Epsilon must not be smaller than "
                             "min. Epsilon")

        if epsDecay < 0:
            raise ValueError("Epsilon Decay must be greater than 0")

        if targetUpdate < 0:
            raise ValueError("Target Update Rate must be greater than 0")

        if (nHL1 < 1) or (nHL2 < 1):
            raise ValueError("Number of Neurons must be a positive integer")

        self.stateSize = 7
        # All possible actions: (CHP, Boiler)
        self.ACTIONS = [(False, False), (True, False),
                        (False, True), (True, True)]
        self.actionSize = len(self.ACTIONS)

        self._done = False
        self._observers = []

        self.mean = 0.
        self.std = 1.

        self.Training = True

        # Training parameter (exploration)
        self.EpsilonStart = max(epsStart, 1.)
        self.Epsilon = self.EpsilonStart
        self.EpsilonDecay = epsDecay
        self.EpsilonEnd = epsMin

        # Training parameter (discount of future reward and costs)
        self.gamma = 0.95
        self.cMax = cMax

        self.targetUpdate = targetUpdate

        # Memory and Model
        self.batchSize = batchSize
        self.memory = ReplayMemory(capacity)
        self.model = DQN_MLP(self.stateSize, self.actionSize, nHL1, nHL2)
        self.targetModel = DQN_MLP(self.stateSize, self.actionSize, nHL1, nHL2)
        self.targetModel.load_state_dict(self.model.state_dict().copy())
        self.targetModel.eval()
        self.optimizer = optim.RMSprop(self.model.parameters(),
                                       lr=0.00025,
                                       momentum=0.95,
                                       alpha=0.95,
                                       eps=0.01
                                       )
        self.criterion = nn.SmoothL1Loss()

        # temp memory for step method
        self.Batch = 0
        self.Epoch = 0
        self.lastAction = random.randrange(self.actionSize)
        self.lastState = np.zeros(self.stateSize)

        # evaluation of training progress
        self.visualise = visualise
        self.trainHistSize = max(trainHistSize, 1)
        self.cEpoch = 0.
        if self.visualise:
            self._initCostVis()
            self._initTrainVis()
        else:
            self.cHist = np.zeros(self.trainHistSize)
            self.epsHist = np.zeros(self.trainHistSize)

        # System Parameter
        self.MaxPower_e = MaxPower_e
        self.MaxPower_t = MaxPower_t
        self.MaxFuelDemand = MaxFuelDemand

    @property
    def done(self):
        return self._done

    @done.setter
    def done(self, value):
        self._done = value
        if self.done:
            for callback in self._observers:
                callback(self._done)

    def report_done(self, callback):
        self._observers.append(callback)

    def getCostInv(w, y, cMax=0.01, mu=0.5):
        e = np.abs(w-y)
        omega = np.tanh(np.sqrt(0.95) / mu)

        return np.tanh(e/omega)**2. * cMax

    def _getCosts(self, state, aIdx):

        costs = 0
        # check fulfilment of thermal demand -> stop criterion
        eDemand_t = state[4] - state[3]  # gen - load
        if eDemand_t != 0:
            return (self.cMax, 1.)

        # if eDemand_t < -0.01 * self.MaxPower_t:
        #     return (self.cMax, 1.)
        # elif eDemand_t > 0.01 * self.MaxPower_t:
        #     return (self.cMax, 1.)

        costs -= 0.25  # bonus for time step

        # hint for storage state
        storage = state[1]
        if storage < 0.1 or storage > 0.9:
            costs += 0.3 * self.cMax

        if storage < 0.05 or storage > 0.95:
            costs += 0.5 * self.cMax

        boiler = state[6]
        # prefer chp over boiler
        if boiler:
            costs += 0.25 * self.cMax

        # add consistency
        chp = state[5]
        # if chp == 0 and self.lastState[5] == 0:
        #     costs -= 0.1

        if chp != self.lastState[5]:
            costs += 0.1 * self.cMax

        return (costs, 0.)

    def _getQbounds(self, Q):
        return (Q.min(), Q.max())

    def _getQtarget(self, state):
        """ Evaluate Q-Network
        """
        with torch.no_grad():
            return self.targetModel(torch.FloatTensor(state))

    def _initCostVis(self):
        self.VisWin = 50
        self.trainHistSize = max(self.trainHistSize, self.VisWin+1)
        self.xEpochs = np.arange(self.trainHistSize)
        self.cHist = np.zeros(self.trainHistSize)
        self.cMean = np.zeros(self.trainHistSize - self.VisWin+1)
        self.cStdU = np.zeros(self.trainHistSize - self.VisWin+1)
        self.cStdL = np.zeros(self.trainHistSize - self.VisWin+1)

        fig = go.Figure()
        fig.update_xaxes(title_text="Number of Epoch")
        fig.update_yaxes(title_text="Costs",
                         range=[-20., 5.])

        lineCostsEnd = go.Scatter({"x": self.xEpochs,
                                   "y": self.cHist,
                                   "name": "costs",
                                   "opacity": 0.25,
                                   "uid": "uid_rEndLine",
                                   "yaxis": "y1",
                                   "line": {"color": "#000000",
                                            "width": 1
                                            }
                                   })
        lineCostsEndM = go.Scatter({"x": self.xEpochs[self.VisWin:],
                                    "y": self.cMean,
                                    "name": "costs mean",
                                    "uid": "uid_rEndLine",
                                    "yaxis": "y1",
                                    "line": {"color": "#000000",
                                             "width": 1
                                             }
                                    })
        lineCostsStdU = go.Scatter({"x": self.xEpochs[self.VisWin:],
                                    "y": self.cStdU,
                                    "name": "costs Std U",
                                    "uid": "uid_rStdULine",
                                    "yaxis": "y1",
                                    "line": {"color": "#000000",
                                             "width": 0.5,
                                             "dash": "dash",
                                             },
                                    })
        lineCostsStdL = go.Scatter({"x": self.xEpochs[self.VisWin:],
                                    "y": self.cStdL,
                                    "name": "costs Std L",
                                    "uid": "uid_rStdLLine",
                                    "yaxis": "y1",
                                    "line": {"color": "#000000",
                                             "width": 0.5,
                                             "dash": "dash",
                                             },
                                    })
        fig.add_trace(lineCostsEnd)
        fig.add_trace(lineCostsEndM)
        fig.add_trace(lineCostsStdU)
        fig.add_trace(lineCostsStdL)
        # create widget
        self.costVis = go.FigureWidget(fig)

    def _initTrainVis(self):
        self.VisWin = 50
        self.trainHistSize = max(self.trainHistSize, self.VisWin+1)
        self.xEpochs = np.arange(self.trainHistSize)
        self.epsHist = np.zeros(self.trainHistSize)

        fig = go.Figure()
        fig.update_xaxes(title_text="Number of Epoch")
        fig.update_yaxes(title_text="Exploration Rate",
                         range=[0., 1.])

        lineEps = go.Scatter({"x": self.xEpochs,
                              "y": self.epsHist,
                              "name": "exploration",
                              "uid": "uid_rEndLine",
                              "yaxis": "y1",
                              "line": {"color": "#000000",
                                       "width": 1
                                       }
                              })

        fig.add_trace(lineEps)

        # create widget
        self.trainVis = go.FigureWidget(fig)

    def _updateTargetModel(self):
        self.targetModel.load_state_dict(
          self.model.state_dict().copy())
        self.targetModel.eval()

    def act(self, state):
        """ Act with epsilon-greedy exploration
        """
        if random.random() > self.Epsilon:
            with torch.no_grad():
                Q = self.model(torch.FloatTensor((state - self.mean) /
                                                 self.std)).flatten()
                Qmin = Q.min(0)
                QminValue = Qmin[0]
                QeqMin = Q == QminValue
                nMin = QeqMin.sum()
                if nMin > 1:
                    return (QeqMin.nonzero(as_tuple=False)
                            [random.randrange(nMin)].item())
                else:
                    return Qmin[1].item()
        else:
            return random.randrange(self.actionSize)

    def batchTrainModel(self):
        batch = Transition(*zip(*self.memory.sample(self.batchSize)))

        state = torch.cat(batch.state).reshape(-1, self.stateSize)
        action = torch.reshape(torch.LongTensor(batch.action),
                               (self.batchSize, -1))
        nextState = torch.cat(batch.nextState).reshape(-1, self.stateSize)
        costs = torch.FloatTensor(batch.costs)
        done = torch.FloatTensor(batch.done)

        state = (state - self.mean) / self.std
        nextState = (nextState - self.mean) / self.std

        # Calculate future costs as training target
        # actual costs + discounted future costs
        Qtarget = self._getQtarget(nextState)
        # use min Q values for target estimation
        # no future cost estimation for finished episodes
        Q = costs + self.gamma * Qtarget.min(axis=1).values * (1. - done)
        Q[Q < 0.] = 0.
        Qbounds = self._getQbounds(Q)

        # estimate future costs from actual state -> test current NN
        # train only Q values for known actions
        Qest = self.model(state).gather(1, action)

        # NN Training
        # Compute loss
        loss = self.criterion(Qest, Q.reshape(action.size()))
        self.optimizer.zero_grad()
        loss.backward()
        # update model
        for param in self.model.parameters():
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step()

        return (loss.item(), Qbounds)

    def load(self, loc='./', fModel='SmartCtrlModel', fStats='SmartCtrlStats'):
        self.loadModel(loc, fModel)
        self.loadStats(loc, fStats)

    def loadModel(self, loc='./', fName='SmartCtrlModel'):
        self.model.load_state_dict(torch.load(loc + fName + '.pt'))
        self._updateTargetModel()

    def loadStats(self, loc='./', fName='SmartCtrlStats'):
        statData = np.load(loc + fName + '.npz')
        self.mean = statData['mean']
        self.std = statData['std']

    def remember(self, state, action, costs, nextState, done):
        self.memory.push(torch.FloatTensor(state),
                         action,
                         torch.FloatTensor(nextState),
                         costs, done)

    def replay(self, updateEpsilon=False):
        """ Training of agent model to generalise memory
             - Train all model outputs, update the output corresponding to
               the memory action by bellman equation (with costs of memory)

        Keyword Arguments:
            updateEpsilon {bool} -- When True Epsilon is recalculated
                                    (default: {False})

        Returns:
            (float, (float, float)) -- Loss of ANN training and
                                       spread of Q Values
        """
        if len(self.memory) < self.batchSize:
            return (None, (None, None))
        loss, Qbounds = self.batchTrainModel()

        if updateEpsilon:
            self.Epsilon = (self.EpsilonEnd +
                            (self.EpsilonStart - self.EpsilonEnd) *
                            math.exp(-1 * self.Epoch / self.EpsilonDecay))

        if self.Epoch % self.targetUpdate == 0:
            self._updateTargetModel()

        return (loss, Qbounds)

    def reset(self):
        self.StorageStateGrad = 0
        self.ThermalDemandGrad = 0

        self.lastState = np.zeros(self.stateSize)  # randomize??
        self.lastAction = 0
        self.done = False

    def save(self, loc='./', fModel='SmartCtrlModel', fStats='SmartCtrlStats'):
        self.saveModel(loc, fModel)
        self.saveStats(loc, fStats)

    def saveModel(self, loc='./', fName='SmartCtrlModel'):
        torch.save(self.model.state_dict(), loc + fName + '.pt')

    def saveStats(self, loc='./', fName='SmartCtrlStats'):
        np.savez(loc + fName, mean=self.mean, std=self.std)

    def step(self, StorageState, CellState, Ambient):

        # prepare boundary conditions
        gen_e, load_e, gen_t, load_t, contrib_e, contrib_t, fuel = CellState
        Eg, solEl, solAz, Tout, Tmean = Ambient

        load_t = load_t / self.MaxPower_t
        gen_t = gen_t / self.MaxPower_t

        if np.all((self.lastState == 0)):
            self.lastState[1] = StorageState
            self.lastState[3] = load_t

        self.StorageStateGrad = (StorageState - self.lastState[1]) / 0.25  # t
        self.ThermalDemandGrad = (load_t - self.lastState[3]) / 0.25

        Chp, Boiler = self.ACTIONS[self.lastAction]

        state = np.array([self.StorageStateGrad,
                          StorageState,
                          self.ThermalDemandGrad,
                          load_t,
                          gen_t,
                          Chp,
                          Boiler], dtype=np.float32)

        aIdx = self.act(state)
        Chp, Boiler = self.ACTIONS[aIdx]

        if self.Training:

            # get Costs and init done
            costs, self.done = self._getCosts(state, aIdx)
            self.cEpoch += costs
            # handle Batch / Epoch
            # since the system is not time limited, one batch is defined as
            # half a day
            self.Batch += 1
            if self.Batch >= 12 / 0.25:
                self.done = True

            if self.done:  # Batch >= 96:  # transitions per epoch
                if self.Epoch < self.trainHistSize:
                    self.cHist[self.Epoch] = self.cEpoch
                    self.epsHist[self.Epoch] = self.Epsilon
                    if self.visualise:
                        idx = max(self.Epoch - self.VisWin, 0)
                        idxEnd = max(self.Epoch, self.VisWin)
                        self.cMean[idx] = self.cHist[idx:idxEnd].mean()
                        cStd = self.cHist[idx:idxEnd].std()
                        self.cStdU[idx] = self.cMean[idx] + cStd
                        self.cStdL[idx] = self.cMean[idx] - cStd
                else:
                    self.cHist[:-1] = self.cHist[1:]
                    self.cHist[-1] = self.cEpoch
                    self.epsHist[:-1] = self.epsHist[1:]
                    self.epsHist[-1] = self.Epsilon
                    if self.visualise:
                        self.xEpochs[:-1] = self.xEpochs[1:]
                        self.xEpochs[-1] = self.Epoch
                        # self.cHist[:-1] = self.cHist[1:]
                        # self.cHist[-1] = self.cEpoch
                        idxStart = self.trainHistSize - self.VisWin
                        self.cMean[:-1] = self.cMean[1:]
                        self.cMean[-1] = self.cHist[idxStart:].mean()
                        cStd = self.cHist[idxStart:].std()
                        self.cStdU[:-1] = self.cStdU[1:]
                        self.cStdU[-1] = self.cMean[-1] + cStd
                        self.cStdL[:-1] = self.cStdL[1:]
                        self.cStdL[-1] = self.cMean[-1] - cStd

                self.Epoch += 1
                self.Batch = 0
                self.cEpoch = 0.

                if self.visualise:
                    with self.costVis.batch_update():
                        self.costVis.data[0].x = self.xEpochs
                        self.costVis.data[1].x = self.xEpochs[self.VisWin:]
                        self.costVis.data[2].x = self.xEpochs[self.VisWin:]
                        self.costVis.data[3].x = self.xEpochs[self.VisWin:]
                        self.costVis.data[0].y = self.cHist
                        self.costVis.data[1].y = self.cMean
                        self.costVis.data[2].y = self.cStdU
                        self.costVis.data[3].y = self.cStdL
                        self.trainVis.data[0].x = self.xEpochs
                        self.trainVis.data[0].y = self.epsHist

            # build replay memory
            self.remember(self.lastState,
                          self.lastAction,
                          costs,
                          state,
                          self.done)
            # train model
            self.replay(True)

        self.lastAction = aIdx
        self.lastState = state.copy()

        # print(state, aIdx, costs, self.done)
        return (Chp, Boiler, bool(self.done))

    def updateStateStats(self, weight=True):
        state = torch.cat(Transition(*zip(*self.memory.memory))
                          .state
                          ).reshape(-1, self.stateSize)
        # get data properties to rescale
        if weight:
            self.mean = (0.5 * self.mean +
                         0.5 * state.mean(0, keepdim=True).flatten().numpy())
            self.std = (0.5 * self.std +
                        0.5 * state.std(0, keepdim=True).flatten().numpy())
            self.std[self.std == 0] = 1.
        else:
            self.mean = state.mean(0, keepdim=True).flatten().numpy()
            self.std = state.std(0, keepdim=True).flatten().numpy()
            self.std[self.std == 0] = 1.


class CtrlSmart(CtrlTemplate):
    def __init__(self, capacity: int, batchSize: int,
                 epsStart: float, epsMin: float, epsDecay: int, cMax: float,
                 targetUpdate: int, nHL1: int, nHL2: int,
                 trainHistSize: int,
                 MaxPower_e: float, MaxPower_t: float, MaxFuelDemand: float,
                 visualise: Bool):
        """ Init Smart cell controller for thermal CHP Systems

        Arguments:
            capacity {int} -- Size of process memory
            batchSize {int} -- Number of samples used from memory
                               for each training
            epsStart {float} -- Initial value for Epsilon (epsMin to 1.)
            epsMin {float} -- Minimum value for Epsilon (0. to 1.)
            epsDecay {int} -- Strength of Epsilon decay
                              (after this number of Epochs Epsilon is
                               approx 0.5 of Start-End)

            targetUpdate {int} -- Rate of Epochs to update target model
            nHL1 {int} -- Number of Neurons in Q Models fist Hidden Layer
            nHL2 {int} -- Number of Neurons in Q Models second Hidden Layer
            trainHistSize {int} -- Size of history for training progress
            MaxPower_e {float} -- Max. possible electrical Power of
                                  thermal System [W]
            MaxPower_t {float} -- Max. possible thermal Power of
                                  thermal System [W]
            MaxFuelDemand {float} -- Max. Fuel demand of thermal System [W]
            visualise {Bool} -- When true, the batch costs are shown to see
                                training progress

        Raises:
            ValueError: Reports erroneous inputs
        """
        if batchSize < 1:
            raise ValueError("Size of Training Batches must be greater than 0")

        if capacity < batchSize:
            raise ValueError("Memory Capacity must be at least equal to "
                             "Batch Size. It's recommended, that the Capacity "
                             "is much greater than the Batch Size.")

        if epsMin < 0.:
            raise ValueError("Min. Epsilon must be between 0. and 1.")

        if epsStart < epsMin:
            raise ValueError("Starting Epsilon must not be smaller than "
                             "min. Epsilon")

        if epsDecay < 0:
            raise ValueError("Epsilon Decay must be greater than 0")

        if targetUpdate < 0:
            raise ValueError("Target Update Rate must be greater than 0")

        if (nHL1 < 1) or (nHL2 < 1):
            raise ValueError("Number of Neurons must be a positive integer")

        self.stateSize = 12
        # All possible actions: CHP, Boiler
        self.ACTIONS = [(False, False), (True, False),
                        (False, True), (True, True)]
        self.actionSize = len(self.ACTIONS)

        self.mean = 0.
        self.std = 1.

        # Training parameter (exploration)
        self.EpsilonStart = max(epsStart, 1.)
        self.Epsilon = self.EpsilonStart
        self.EpsilonDecay = epsDecay
        self.EpsilonEnd = epsMin

        # Training parameter (discount of future reward and costs)
        self.gamma = 0.95
        self.cMax = cMax

        self.targetUpdate = targetUpdate

        # Memory and Model
        self.batchSize = batchSize
        self.memory = ReplayMemory(capacity)
        self.model = DQN_MLP(self.stateSize, self.actionSize, nHL1, nHL2)
        self.targetModel = DQN_MLP(self.stateSize, self.actionSize, nHL1, nHL2)
        self.targetModel.load_state_dict(self.model.state_dict().copy())
        self.targetModel.eval()
        self.optimizer = optim.RMSprop(self.model.parameters(),
                                       lr=0.00025,
                                       momentum=0.95,
                                       alpha=0.95,
                                       eps=0.01
                                       )
        self.criterion = nn.SmoothL1Loss()

        # temp memory for step method
        self.Batch = 0
        self.Epoch = 0
        self.lastAction = random.randrange(self.actionSize)
        self.lastState = np.zeros(self.stateSize)

        # evaluation of training progress
        self.visualise = visualise
        self.trainHistSize = max(trainHistSize, 1)
        self.cEpoch = 0.
        if self.visualise:
            self._initTrainVis()
        else:
            self.cHist = np.zeros(self.trainHistSize)

        # System Parameter
        self.MaxPower_e = MaxPower_e
        self.MaxPower_t = MaxPower_t
        self.MaxFuelDemand = MaxFuelDemand

    def _getCosts(self, state):
        # check fulfilment of thermal demand -> stop criterion
        eDemand_t = state[3] - state[4]  # gen - load
        if eDemand_t < -0.01 * self.MaxPower_t:
            return (self.cMax, 1.)
        elif eDemand_t > 0.01 * self.MaxPower_t:
            return (0.8 * self.cMax, 1,)

        # check electrical autarky and fuel demand
        costs = 0.
        eDemand_e = state[1] - state[2]  # electrical: gen - load
        if eDemand_e < 0.:
            costs = min(1., abs(eDemand_e) / self.MaxPower_e) * 0.5 * self.cMax

        costs += state[7] / self.MaxFuelDemand * 0.2 * self.cMax

        return (costs, 0.)

    def _getQbounds(self, Q):
        return (Q.min(), Q.max())

    def _getQtarget(self, state):
        """ Evaluate Q-Network
        """
        with torch.no_grad():
            return self.targetModel(torch.FloatTensor(state))

    def _initTrainVis(self):
        self.VisWin = 50
        self.trainHistSize = max(self.trainHistSize, self.VisWin+1)
        self.xEpochs = np.arange(self.trainHistSize)
        self.cHist = np.zeros(self.trainHistSize)
        self.cMean = np.zeros(self.trainHistSize - self.VisWin+1)
        self.cStdU = np.zeros(self.trainHistSize - self.VisWin+1)
        self.cStdL = np.zeros(self.trainHistSize - self.VisWin+1)

        fig = go.Figure()
        fig.update_xaxes(title_text="Number of Epoch")
        fig.update_yaxes(title_text="Costs",
                         range=[0., self.batchSize * self.cMax * 2.0])

        lineCostsEnd = go.Scatter({"x": self.xEpochs,
                                   "y": self.cHist,
                                   "name": "costs",
                                   "opacity": 0.25,
                                   "uid": "uid_rEndLine",
                                   "yaxis": "y1",
                                   "line": {"color": "#000000",
                                            "width": 1
                                            }
                                   })
        lineCostsEndM = go.Scatter({"x": self.xEpochs[self.VisWin:],
                                    "y": self.cMean,
                                    "name": "costs mean",
                                    "uid": "uid_rEndLine",
                                    "yaxis": "y1",
                                    "line": {"color": "#000000",
                                             "width": 1
                                             }
                                    })
        lineCostsStdU = go.Scatter({"x": self.xEpochs[self.VisWin:],
                                    "y": self.cStdU,
                                    "name": "costs Std U",
                                    "uid": "uid_rStdULine",
                                    "yaxis": "y1",
                                    "line": {"color": "#000000",
                                             "width": 0.5,
                                             "dash": "dash",
                                             },
                                    })
        lineCostsStdL = go.Scatter({"x": self.xEpochs[self.VisWin:],
                                    "y": self.cStdL,
                                    "name": "costs Std L",
                                    "uid": "uid_rStdLLine",
                                    "yaxis": "y1",
                                    "line": {"color": "#000000",
                                             "width": 0.5,
                                             "dash": "dash",
                                             },
                                    })
        fig.add_trace(lineCostsEnd)
        fig.add_trace(lineCostsEndM)
        fig.add_trace(lineCostsStdU)
        fig.add_trace(lineCostsStdL)
        # create widget
        self.trainVis = go.FigureWidget(fig)

    def _updateTargetModel(self):
        self.targetModel.load_state_dict(
          self.model.state_dict().copy())
        self.targetModel.eval()

    def act(self, state):
        """ Act with epsilon-greedy exploration
        """
        if random.random() > self.Epsilon:
            with torch.no_grad():
                Q = self.model(torch.FloatTensor((state - self.mean) /
                                                 self.std)).flatten()
                Qmin = Q.min(0)
                QminValue = Qmin[0]
                QeqMin = Q == QminValue
                nMin = QeqMin.sum()
                if nMin > 1:
                    return (QeqMin.nonzero(as_tuple=False)
                            [random.randrange(nMin)].item())
                else:
                    return Qmin[1].item()
        else:
            return random.randrange(self.actionSize)

    def batchTrainModel(self):
        batch = Transition(*zip(*self.memory.sample(self.batchSize)))

        state = torch.cat(batch.state).reshape(-1, self.stateSize)
        action = torch.reshape(torch.LongTensor(batch.action),
                               (self.batchSize, -1))
        nextState = torch.cat(batch.nextState).reshape(-1, self.stateSize)
        costs = torch.FloatTensor(batch.costs)
        done = torch.FloatTensor(batch.done)

        state = (state - self.mean) / self.std
        nextState = (nextState - self.mean) / self.std

        # Calculate future costs as training target
        # actual costs + discounted future costs
        Qtarget = self._getQtarget(nextState)
        # use min Q values for target estimation
        # no future cost estimation for finished episodes
        Q = costs + self.gamma * Qtarget.min(axis=1).values * (1. - done)
        Q[Q < 0.] = 0.
        Qbounds = self._getQbounds(Q)

        # estimate future costs from actual state -> test current NN
        # train only Q values for known actions
        Qest = self.model(state).gather(1, action)

        # NN Training
        # Compute loss
        loss = self.criterion(Qest, Q.reshape(action.size()))
        self.optimizer.zero_grad()
        loss.backward()
        # update model
        for param in self.model.parameters():
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step()

        return (loss.item(), Qbounds)

    def load(self, loc='./', fModel='SmartCtrlModel', fStats='SmartCtrlStats'):
        self.loadModel(loc, fModel)
        self.loadStats(loc, fStats)

    def loadModel(self, loc='./', fName='SmartCtrlModel'):
        self.model.load_state_dict(torch.load(loc + fName + '.pt'))
        self._updateTargetModel()

    def loadStats(self, loc='./', fName='SmartCtrlStats'):
        statData = np.load(loc + fName + '.npz')
        self.mean = statData['mean']
        self.std = statData['std']

    def remember(self, state, action, costs, nextState, done):
        self.memory.push(torch.FloatTensor(state),
                         action,
                         torch.FloatTensor(nextState),
                         costs, done)

    def replay(self, updateEpsilon=False):
        """ Training of agent model to generalise memory
             - Train all model outputs, update the output corresponding to
               the memory action by bellman equation (with costs of memory)

        Keyword Arguments:
            updateEpsilon {bool} -- When True Epsilon is recalculated
                                    (default: {False})

        Returns:
            (float, (float, float)) -- Loss of ANN training and
                                       spread of Q Values
        """
        if len(self.memory) < self.batchSize:
            return (None, (None, None))
        loss, Qbounds = self.batchTrainModel()

        if updateEpsilon:
            self.Epsilon = (self.EpsilonEnd +
                            (self.EpsilonStart - self.EpsilonEnd) *
                            math.exp(-1 * self.Epoch / self.EpsilonDecay))

        if self.Epoch % self.targetUpdate == 0:
            self._updateTargetModel()

        return (loss, Qbounds)

    def save(self, loc='./', fModel='SmartCtrlModel', fStats='SmartCtrlStats'):
        self.saveModel(loc, fModel)
        self.saveStats(loc, fStats)

    def saveModel(self, loc='./', fName='SmartCtrlModel'):
        torch.save(self.model.state_dict(), loc + fName + '.pt')

    def saveStats(self, loc='./', fName='SmartCtrlStats'):
        np.savez(loc + fName, mean=self.mean, std=self.std)

    def step(self, StorageState, CellState, Ambient):
        # prepare boundary conditions
        gen_e, load_e, gen_t, load_t, contrib_e, contrib_t, fuel = CellState
        Eg, solEl, solAz, Tout = Ambient
        state = np.array([StorageState, gen_e, load_e, gen_t, load_t,
                          contrib_e, contrib_t, fuel,
                          Eg, solEl, solAz, Tout], dtype=np.float32)

        # get Costs and init done
        costs, done = self._getCosts(state)
        self.cEpoch += costs

        # handle Batch / Epoch
        # since the system is not time limited, one batch is defined as one day
        self.Batch += 1
        if self.Batch >= 96:  # transitions per epoch
            if self.Epoch < self.trainHistSize:
                self.cHist[self.Epoch] = self.cEpoch
                if self.visualise:
                    idx = max(self.Epoch - self.VisWin, 0)
                    idxEnd = max(self.Epoch, self.VisWin)
                    self.cMean[idx] = self.cHist[idx:idxEnd].mean()
                    cStd = self.cHist[idx:idxEnd].std()
                    self.cStdU[idx] = self.cMean[idx] + cStd
                    self.cStdL[idx] = self.cMean[idx] - cStd
            else:
                self.cHist[:-1] = self.cHist[1:]
                self.cHist[-1] = self.cEpoch
                if self.visualise:
                    self.xEpochs[:-1] = self.xEpochs[1:]
                    self.xEpochs[-1] = self.Epoch
                    self.cHist[:-1] = self.cHist[1:]
                    self.cHist[-1] = self.cEpoch
                    idxStart = self.trainHistSize - self.VisWin
                    self.cMean[:-1] = self.cMean[1:]
                    self.cMean[-1] = self.cHist[idxStart:].mean()
                    cStd = self.cHist[idxStart:].std()
                    self.cStdU[:-1] = self.cStdU[1:]
                    self.cStdU[-1] = self.cMean[-1] + cStd
                    self.cStdL[:-1] = self.cStdL[1:]
                    self.cStdL[-1] = self.cMean[-1] - cStd

            self.Epoch += 1
            self.Batch = 0
            done = 1.
            self.cEpoch = 0.

            if self.visualise:
                with self.trainVis.batch_update():
                    self.trainVis.data[0].x = self.xEpochs
                    self.trainVis.data[1].x = self.xEpochs[self.VisWin:]
                    self.trainVis.data[2].x = self.xEpochs[self.VisWin:]
                    self.trainVis.data[3].x = self.xEpochs[self.VisWin:]
                    self.trainVis.data[0].y = self.cHist
                    self.trainVis.data[1].y = self.cMean
                    self.trainVis.data[2].y = self.cStdU
                    self.trainVis.data[3].y = self.cStdL

        # build replay memory
        self.remember(self.lastState, self.lastAction, costs, state, done)
        # train model
        self.replay(True)

        aIdx = self.act(state)
        Chp, Boiler = self.ACTIONS[aIdx]

        self.lastAction = aIdx
        self.lastState = state.copy()

        return (Chp, Boiler)

    def updateStateStats(self, weight=True):
        state = torch.cat(Transition(*zip(*self.memory.memory))
                          .state
                          ).reshape(-1, self.stateSize)
        # get data properties to rescale
        if weight:
            self.mean = (0.5 * self.mean +
                         0.5 * state.mean(0, keepdim=True).flatten().numpy())
            self.std = (0.5 * self.std +
                        0.5 * state.std(0, keepdim=True).flatten().numpy())
            self.std[self.std == 0] = 1.
        else:
            self.mean = state.mean(0, keepdim=True).flatten().numpy()
            self.std = state.std(0, keepdim=True).flatten().numpy()
            self.std[self.std == 0] = 1.
