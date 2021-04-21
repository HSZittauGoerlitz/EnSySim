# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import generateGenericCell
from GenericModel.PARAMETER import PBTYPES_NOW as pBTypes
from SystemComponentsFast import simulate
from PostProcesing import plots
import logging


# %%
FORMAT = ("%(levelname)s %(name)s %(asctime)-15s "
          "%(filename)s:%(lineno)d %(message)s")
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

# %%
# Parameter
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
pHeatpumps = {'class_1': 0, 'class_2': 0,
              'class_3': 0, 'class_4': 0.12,
              'class_5': 0.27}
pCHP = 0.1
# buildings are imported
# environment
region = "East"

# %%
# prepare simulation
nSteps, time, SLP, HWP, Weather, Solar = getSimData(start, end, region)

# %%
cell = generateGenericCell(nBuildings, pAgents,
                           pPHHagents, pAgriculture,
                           pDHN, pPVplants, pHeatpumps, pCHP, pBTypes,
                           nSepBSLagents, pAgricultureBSLsep,
                           region, nSteps)

# %%
simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
         Solar.to_dict('lists'))

# %%
plots.cellPowerBalance(cell, time)

# %%
plots.cellEnergyBalance(cell, time)

# %%
