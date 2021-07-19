# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from Controller.Cell.CHP_SystemThermal import CtrlSmart
from GenericModel.Design import generateGenericCell
from GenericModel.PARAMETER import PBTYPES_NOW as pBTypes
from SystemComponentsFast import simulate, CellChpSystemThermal
from PostProcesing import plots
import logging

# %% 
# debugging
import os

print(os.getpid())

# %% 
# logging
FORMAT = ("%(levelname)s %(name)s %(asctime)-15s "
          "%(filename)s:%(lineno)d %(message)s")
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

# %% 
# model parameters

# time
start = '01.01.2020'
end = '01.01.2021'
# agents
nSepBSLagents = 100
pAgricultureBSLsep = 0.7
nBuildings = {'FSH': 505, 'REH': 1010, 'SAH': 680, 'BAH': 100}
pAgents = {'FSH': 0.9, 'REH': 0.9, 'SAH': 0.85, 'BAH': 0.75}
pPHHagents = {'FSH': 0.8, 'REH': 0.8, 'SAH': 0.6, 'BAH': 0.9}
pAgriculture = {'FSH': 0.2, 'REH': 0.2, 'SAH': 0.0, 'BAH': 0.0}
# district heating and PV
pDHN = {'FSH': 0.1, 'REH': 0.1, 'SAH': 0.1, 'BAH': 0.1}
pPVplants = 0.2
# heatpumps and chp
pHeatpumps = {'class_1': 0, 'class_2': 0,
              'class_3': 0, 'class_4': 0.12,
              'class_5': 0.27}
pCHP = 0.1
# buildings are imported
# environment
region = "East"

# %% 
# DQN parameters
capacity = 96 * 300
batchSize = 48
epsStart = 0.9
epsMin = 0.5
epsDecay = 1000
cMax = 1.
targetUpdate = 100
nHL1 = 24
nHL2 = 12
trainHistSize = 365

visualise = True

# %%
# prepare simulation
nSteps, time, SLP, HWP, Weather, Solar = getSimData(start, end, region)

# %%
# generate cell, add systems
cell = generateGenericCell(nBuildings, pAgents,
                           pPHHagents, pAgriculture,
                           pDHN, pPVplants, pHeatpumps, pCHP, pBTypes,
                           nSepBSLagents, pAgricultureBSLsep,
                           region, nSteps)

demand = cell.get_thermal_demand(True)
chpSystem = CellChpSystemThermal(demand, 0.75, 2*demand, 0.,
                                 0.98, 0.98, nSteps)

MaxPower_e = chpSystem.chp.pow_e
MaxPower_t = chpSystem.chp.pow_t + chpSystem.boiler.pow_t
MaxFuelDemand = ((chpSystem.chp.pow_e + chpSystem.chp.pow_t) /
                 chpSystem.chp.efficiency +
                 chpSystem.boiler.pow_t / chpSystem.boiler.efficiency)

controller = CtrlSmart(capacity, batchSize, epsStart, epsMin, epsDecay,
                       cMax, targetUpdate, nHL1, nHL2, trainHistSize,
                       MaxPower_e, MaxPower_t, MaxFuelDemand, visualise)
controller.loadStats()
chpSystem.controller = controller
cell.add_chp_thermal(chpSystem)


# %%
# simulate
if visualise:
    display(controller.trainVis)

while True:


# Recommendation: Upate stats weighted
# and save controller for further use / training

# %%
plots.cellPowerBalance(cell, time)

# %%
plots.cellEnergyBalance(cell, time)

# %%
