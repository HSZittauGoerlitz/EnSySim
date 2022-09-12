# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# Imports
from tkinter import NS
from urllib.request import HTTPPasswordMgrWithPriorAuth
from BoundaryConditions.Simulation.SimulationData import getSimData
from Controller.Cell.CHP_SystemThermal import CtrlBaselines
from GenericModel.Design import generateGenericCell
from GenericModel.PARAMETER import PBTYPES_NOW as pBTypes
from SystemComponentsFast import simulate, CellChpSystemThermal, EnSySimEnv
from PostProcesing import plots
import plotly.graph_objs as go
import numpy as np
import random
import logging

from stable_baselines3 import DQN
from stable_baselines3.common.evaluation import evaluate_policy

#from wandb.integration.sb3 import WandbCallback

from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecVideoRecorder
import wandb
from wandb.integration.sb3 import WandbCallback

import gym
from gym import spaces
# debug pid
import os
print(os.getpid())
# %%
# Logging
FORMAT = ("%(levelname)s %(name)s %(asctime)-15s "
          "%(filename)s:%(lineno)d %(message)s")
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

# %%


class EnSySimEnvPy(gym.Env):
    metadata = {}

    def __init__(self, hist=False) -> None:

        # from class CtrlSmartSimple(CtrlTemplate): def __init__
        # self.ACTIONS = [(False, False), (True, False),
        #         (False, True), (True, True)]
        self.action_space = spaces.Discrete(4)

        # from class CtrlSmartSimple(CtrlTemplate): def step
        #
        # state = np.array([self.StorageStateGrad,
        #                   StorageState,
        #                   self.ThermalDemandGrad,
        #                   load_t,
        #                   gen_t,
        #                   Chp,
        #                   Boiler], dtype=np.float32)
        low = np.array(
            [
                -np.finfo(np.float32).max,
                0.,
                -np.finfo(np.float32).max,
                -1,
                0.,
                0.,

            ],
            dtype=np.float32,
        )
        high = np.array(
            [
                np.finfo(np.float32).max,
                1.,
                np.finfo(np.float32).max,
                1,
                1.,
                1.,
            ],
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(low, high, dtype=np.float32)

        # set parameters for env
        # time
        start = '01.01.2020'
        end = '01.01.2021'
        # seperate agents
        nSepBSLagents = 2
        pAgricultureBSLsep = 0
        # pHH buildings
        nBuildings = {'FSH': 0, 'REH': 0, 'SAH': 3, 'BAH': 24}
        pAgents = {'FSH': 0, 'REH': 0, 'SAH': 1, 'BAH': 0.9}
        pPHHagents = {'FSH': 0, 'REH': 0, 'SAH': 0.75, 'BAH': 1}
        pAgriculture = {'FSH': 0, 'REH': 0, 'SAH': 0.25, 'BAH': 0.0}
        # portion of district heating for building types
        pDHN = {'FSH': 0, 'REH': 0, 'SAH': 1, 'BAH': 1}
        # portion of PV on buildings
        pPVplants = 0.2
        # portion of HP in buildings
        pHeatpumps = {'class_1': 0, 'class_2': 0,
                      'class_3': 0, 'class_4': 0.12,
                      'class_5': 0.27}
        # portion of CHP electrical generation in buildings on yearly load
        pCHP = 0
        # environment
        region = "East"

        # prepare simulation data
        self.nSteps, self.time, SLP, HWP, Weather, Solar = getSimData(start, end, region)

        if hist:
            hist = self.nSteps
        else:
            hist = 0

        # generate cell
        self.cell = generateGenericCell(nBuildings, pAgents,
                                   pPHHagents, pAgriculture,
                                        pDHN, pPVplants, pHeatpumps, pCHP,
                                        pBTypes, nSepBSLagents,
                                        pAgricultureBSLsep, region, hist)

        # get dhn demand
        demand = self.cell.get_thermal_demand(True)
        # generate chp system with storage for heating network
        chpSystem = CellChpSystemThermal(demand, 0.35, 2*demand, 0.05,
                                         0.98, 0.98, hist)

        # chp controller
        MaxPower_e = chpSystem.chp.pow_e
        MaxPower_t = chpSystem.chp.pow_t + chpSystem.boiler.pow_t

        self.controller = CtrlBaselines(MaxPower_e, MaxPower_t)
        self.controller.feedbackConnection(self.listenToFeedback)
        chpSystem.controller = self.controller
        self.cell.add_chp_thermal(chpSystem)

        # rust env
        self.env = EnSySimEnv(self.nSteps, SLP.to_dict('list'), HWP,
                              Weather.to_dict('list'), Solar.to_dict('list'))
        self.env.add_cell(self.cell)

    def reset(self):
        # reset env
        self.env.reset()
        # take some random action to produce initial observation
        action = 0 # random.randrange(self.controller.actionSize)
        # set action here directly
        self.controller.action = action
        # step env
        self.env.step()
        # return initial observation
        if self.done:
            self.observation = self.reset()
            print("mist!")
        return self.observation

    def step(self, action):
        # set action here directly
        self.controller.action = action
        # step env
        self.env.step()
        # controller reports feedback via callback
        return self.observation, self.reward, self.done, self.info

    def render():
        pass

    def listenToFeedback(self, feedback):
        self.observation = feedback[0]
        self.reward = feedback[1]
        self.done = feedback[2]
        self.info = feedback[3]

    def getData(self):
        self.cell = self.env.main_cell

# %%
# Training environment
env = EnSySimEnvPy()

# %%

wandb.tensorboard.patch(root_logdir="/")
# %%

config = {
    "policy type": "MlpPolicy",
    "total_timesteps": 1000,
    "env_name": "CartPole-v1", 
  #"learning_rate": 0.001,
  #"epochs": 100,
  #"batch_size": 128
}
# create env
# wandb.tensorboard.patch(root_logdir="/")
# see for symlink fix>
# https://www.scivision.dev/windows-symbolic-link-permission-enable/
run = wandb.init(project="nero", entity="hszg-ipm-mtpa", config=config, sync_tensorboard=True)

def make_env_wb():
    env = gym.make(config['env_name'])
    env = Monitor(env)
    return env

env = DummyVecEnv([make_env_wb])
env = VecVideoRecorder(env, 'videos', record_video_trigger=lambda x: x % 2000 == 0, video_length=200)

# train agent
model = DQN("MlpPolicy",
            env,
            verbose=2,
            learning_starts=10000,
            buffer_size=100000,
            #learning_rate=0.00001,
            exploration_fraction=0.05,
            )
<<<<<<< Updated upstream
model.learn(total_timesteps=500000)
model.save("DQN_gym-test")
=======
# model.tensorboard_log = "logs/"
wandb.watch(model.q_net)
model.learn(total_timesteps=config["total_timesteps"], callback=WandbCallback(gradient_save_freq=100,  verbose=2, model_save_path=f"models/{run.id}"))

run.finish()

# %%
# Evaluate the agent
mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10)
print(mean_reward, std_reward)

# %%
# with hist
env = EnSySimEnvPy(True)
# load model
model = DQN.load("DQN_gym-test", env=env)
# %%
# demo
observation = env.reset()
print(observation)
done = False
while not done:
    action = model.predict(observation)
    (observation, reward, done, info) = env.step(action[0])
    print(observation)
    print(action)
    print(done)

env.getData()

# %%
plots.cellPowerBalance(env.cell, env.time)

# %%
plots.cellEnergyBalance(env.cell, env.time)

# %%
chpSystem = env.cell.get_thermal_chp_system()
chp_gen_e = np.array(chpSystem.chp.gen_e.get_memory())
CHPstate = chp_gen_e > 0.
fig = go.Figure()
fig.add_trace(go.Scatter(x=env.time, y=CHPstate,
                         line={'color': 'rgba(100, 149, 237, 0.5)',
                               'width': 1},
                         name="CHP state")
                )
fig.update_layout(height=600, width=600,
                  title_text="CHP operation")
fig.update_xaxes(title_text="Time")
fig.update_yaxes(title_text="On/Off")

chpSystem = env.cell.get_thermal_chp_system()
boiler_gen_t = np.array(chpSystem.boiler.gen_t.get_memory())
boilerState = boiler_gen_t > 0.
fig = go.Figure()
fig.add_trace(go.Scatter(x=env.time, y=boilerState,
                         line={'color': 'rgba(100, 149, 237, 0.5)',
                               'width': 1},
                         name="boiler state")
                )
fig.update_layout(height=600, width=600,
                  title_text="boiler operation")
fig.update_xaxes(title_text="Time")
fig.update_yaxes(title_text="On/Off")
# %%

plots.chargeState(chpSystem.storage, env.time)

# observations = env.reset()
# max_cycles = 500
# for step in range(max_cycles):
    # actions = {agent: policy(observations[agent], agent) for agent in env.cell.agents}
    # observations, rewards, dones, infos = parallel_env.step(actions)



# %%
# Training
# # %%
# # Evaluation

# # controller.load()
# controller.Training = False
# controller.Epsilon = 0.

# # chpSystem.controller = controller
# # cell.add_chp_thermal(chpSystem)

# # run the simulation
# simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
#          Solar.to_dict('list'))

# # %%
# # Cell history
# plots.cellPowerBalance(cell, time)

# # %%
# plots.cellEnergyBalance(cell, time)

# # %%
# # CHP history
# chpSystem = cell.get_thermal_chp_system()
# chp_gen_e = np.array(chpSystem.chp.gen_e.get_memory())
# CHPstate = chp_gen_e > 0.
# fig = go.Figure()
# fig.add_trace(go.Scatter(x=time, y=CHPstate,
#                          line={'color': 'rgba(100, 149, 237, 0.5)',
#                                'width': 1},
#                          name="CHP state")
#               )
# fig.update_layout(height=300, width=1000,
#                   title_text="CHP operation")
# fig.update_xaxes(title_text="Time")
# fig.update_yaxes(title_text="On/Off")

# # %%
# # boiler history
# chpSystem = cell.get_thermal_chp_system()
# boiler_gen_t = np.array(chpSystem.boiler.gen_t.get_memory())
# boile_state = boiler_gen_t > 0.
# fig = go.Figure()
# fig.add_trace(go.Scatter(x=time, y=boile_state,
#                          line={'color': 'rgba(100, 149, 237, 0.5)',
#                                'width': 1},
#                          name="boiler state")
#               )
# fig.update_layout(height=300, width=1000,
#                   title_text="boiler operation")
# fig.update_xaxes(title_text="Time")
# fig.update_yaxes(title_text="On/Off")
# # %%
# # storage history
# chpSystem = cell.get_thermal_chp_system()
# plots.chargeState(chpSystem.storage, time)

# # %%

# # import pickle
# # time["load_t"] = cell.load_t.get_memory()
# # with open("timeseries_load_t.dat", 'wb') as filehandle:
# #     pickle.dump(time, filehandle)

# # %%
# # histogram of chp
# # get running times
# chpSystem = cell.get_thermal_chp_system()
# chp_gen_e = np.array(chpSystem.chp.gen_e.get_memory())
# CHPstate = chp_gen_e > 0.

# CHP_hist = []
# state_hist = []
# running_counter = 0
# previuos_state = CHPstate[0]
# for state in CHPstate:
#     if state == previuos_state:
#         running_counter += 1
#     else:
#         CHP_hist.append(running_counter)
#         state_hist.append(previuos_state)
#         running_counter = 1
#     previuos_state = state
# CHP_hist.append(running_counter)
# state_hist.append(previuos_state)
# if CHPstate[0] == CHPstate[-1]:
#     CHP_hist[0] += CHP_hist[-1]
#     CHP_hist.pop()
#     state_hist.pop()

# CHP_hist.pop(1)
# state_hist.pop(1)
# CHP_hist.pop(-1)
# state_hist.pop(-1)

# CHP_hist = np.array(CHP_hist) * 0.25
# state_hist = np.array(state_hist)


# import matplotlib.pyplot as plt
# # graph
# plt.hist([CHP_hist[state_hist], CHP_hist[np.invert(state_hist)]],
#          bins=100,
#          density=False,
#          stacked=True,
#          cumulative=False)
# plt.title("Runtime Histogram")
# plt.xlabel("Stunden ohne Zustandsänderung")
# plt.ylabel("Häufigkeit")
# plt.show()

# # %%
