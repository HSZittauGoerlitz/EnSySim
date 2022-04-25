# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from Controller.Cell.CHP_SystemThermal import CtrlDefault
from Controller.Cell.CHP_SystemThermal import CtrlSmartSimple
from GenericModel.Design import _check_pBTypes, generateGenericCell
from GenericModel.PARAMETER import PBTYPES_NOW as pBTypes
from SystemComponentsFast import simulate, CellChpSystemThermal, EnSySimEnv
from PostProcesing import plots
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import numpy as np
import logging

# %% Logging
FORMAT = ("%(levelname)s %(name)s %(asctime)-15s "
          "%(filename)s:%(lineno)d %(message)s")
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

# %%
import os
print(os.getpid())

# %%
# set parameters
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
# district heating and PV
pDHN = {'FSH': 0, 'REH': 0, 'SAH': 1, 'BAH': 1}
pPVplants = 0.2
pHeatpumps = {'class_1': 0, 'class_2': 0,
              'class_3': 0, 'class_4': 0.12,
              'class_5': 0.27}
pCHP = 0
# buildings are imported
# environment
region = "East"

# set controller to use it or set variable to None
controller = CtrlDefault()

# %%
# prepare simulation
nSteps, time, SLP, HWP, Weather, Solar = getSimData(start, end, region)

# %%
# generate cell
cell = generateGenericCell(nBuildings, pAgents,
                           pPHHagents, pAgriculture,
                           pDHN, pPVplants, pHeatpumps, pCHP, pBTypes,
                           nSepBSLagents, pAgricultureBSLsep,
                           region, nSteps)

# get dhn demand
demand = cell.get_thermal_demand(True)
# generate chp system with storage
chpSystem = CellChpSystemThermal(demand, 0.35, 2*demand, 0.05,
                                 0.98, 0.98, nSteps)
# # configure controller
# chpSystem.controller = None#controller
# # add chp system to cell
# cell.add_chp_thermal(chpSystem)

# DQN parameters
capacity = 96 * 3650
batchSize = 48
epsStart = 1
epsMin = 0.01
epsDecay = 500
cMax = 1.
targetUpdate = 100
nHL1 = 24
nHL2 = 12
trainHistSize = 365

visualise = True
MaxPower_e = chpSystem.chp.pow_e
MaxPower_t = chpSystem.chp.pow_t + chpSystem.boiler.pow_t
MaxFuelDemand = ((chpSystem.chp.pow_e + chpSystem.chp.pow_t) /
                 chpSystem.chp.efficiency +
                 chpSystem.boiler.pow_t / chpSystem.boiler.efficiency)

controller = CtrlSmartSimple(capacity, batchSize, epsStart, epsMin, epsDecay,
                             cMax, targetUpdate, nHL1, nHL2, trainHistSize,
                             MaxPower_e, MaxPower_t, MaxFuelDemand, visualise)

# controller.loadStats()
# controller.loadMemory()

# %% Training environment

env = EnSySimEnv(SLP.to_dict('list'), HWP, Weather.to_dict('list'),
                 Solar.to_dict('list'))


class EnvStatus:
    def __init__(self, visualise=False) -> None:
        self.done = False
        if visualise:
            self._initEnvVis()

    def listen_to_controllers(self, done):
        self.done = done

    def _initEnvVis(self):

        VisWin = 50
        trainHistSize = 365
        max_episode_steps = 96

        trainHistSize = max(trainHistSize, VisWin+1)
        self.epoch_duration = np.zeros(trainHistSize)
        self.xEpochs = np.arange(trainHistSize)

        fig = go.Figure()
        fig.update_xaxes(title_text="Number of Epoch")
        fig.update_yaxes(title_text="Epoch duration",
                         range=[0., max_episode_steps])

        lineEpochSteps = go.Scatter({"x": self.xEpochs,
                                     "y": self.epoch_duration,
                                     "name": "steps per epoch",
                                     "uid": "uid_rEndLine",
                                     "yaxis": "y1",
                                     "line": {"color": "#000000",
                                              "width": 1
                                              }
                                     })
        fig.add_trace(lineEpochSteps)
        # create widget
        self.envVis = go.FigureWidget(fig)


env_status = EnvStatus(visualise)

controller.report_done(env_status.listen_to_controllers)

chpSystem.controller = controller

cell.add_chp_thermal(chpSystem)

env.add_cell(cell)

# %% Training
episodes = 1500
i = 0
steps = 0
controller.Training = True

controller.reset()
if visualise:
    display(controller.costVis)
    display(controller.trainVis)
    display(env_status.envVis)
while i < episodes:
    if not env_status.done:
        env.step()
        steps += 1
    else:

        i += 1

        if visualise:
            if i < trainHistSize:
                env_status.epoch_duration[i] = steps
            if i > trainHistSize:
                env_status.epoch_duration[:-1] = env_status.epoch_duration[1:]
                env_status.epoch_duration[-1] = steps
                env_status.xEpochs += 1
            with env_status.envVis.batch_update():
                env_status.envVis.data[0].y = env_status.epoch_duration
                env_status.envVis.data[0].x = env_status.xEpochs

        env.reset()
        controller.reset()
        env_status.done = False
        steps = 0

# %%
# Evaluation

# controller.load()
controller.Training = False
controller.Epsilon = 0.

# chpSystem.controller = controller
# cell.add_chp_thermal(chpSystem)

# run the simulation
simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
         Solar.to_dict('list'))

# %%

if visualise:
    display(controller.costVis)

for i in range(1):

    simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
             Solar.to_dict('list'))
    # plots.cellPowerBalance(cell, time)
    # plots.cellEnergyBalance(cell, time)
    # plots.chargeState(cell.get_thermal_chp_system().storage, time)

    # break

    # cell.get_thermal_chp_system().storage.initialize_random()


# %%
# Cell history
plots.cellPowerBalance(cell, time)

# %%
plots.cellEnergyBalance(cell, time)

# %%
# CHP history
chpSystem = cell.get_thermal_chp_system()
chp_gen_e = np.array(chpSystem.chp.gen_e.get_memory())
CHPstate = chp_gen_e > 0.
fig = go.Figure()
fig.add_trace(go.Scatter(x=time, y=CHPstate,
                         line={'color': 'rgba(100, 149, 237, 0.5)',
                               'width': 1},
                         name="CHP state")
              )
fig.update_layout(height=300, width=1000,
                  title_text="CHP operation")
fig.update_xaxes(title_text="Time")
fig.update_yaxes(title_text="On/Off")

# %%
# boiler history
chpSystem = cell.get_thermal_chp_system()
boiler_gen_t = np.array(chpSystem.boiler.gen_t.get_memory())
boile_state = boiler_gen_t > 0.
fig = go.Figure()
fig.add_trace(go.Scatter(x=time, y=boile_state,
                         line={'color': 'rgba(100, 149, 237, 0.5)',
                               'width': 1},
                         name="boiler state")
              )
fig.update_layout(height=300, width=1000,
                  title_text="boiler operation")
fig.update_xaxes(title_text="Time")
fig.update_yaxes(title_text="On/Off")
# %%
# storage history
chpSystem = cell.get_thermal_chp_system()
plots.chargeState(chpSystem.storage, time)

# %%

# import pickle
# time["load_t"] = cell.load_t.get_memory()
# with open("timeseries_load_t.dat", 'wb') as filehandle:
#     pickle.dump(time, filehandle)
