# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# Imports

from BoundaryConditions.Simulation.SimulationData import getSimData
from Controller.Cell.CHP_SystemThermal import CtrlDefault
from GenericModel.Design import generateGenericCell
from GenericModel.PARAMETER import PBTYPES_NOW as pBTypes
from SystemComponentsFast import simulate, CellChpSystemThermal, Wind
from PostProcesing import plots, dataCollection
import logging
import plotly.graph_objs as go



# %%
FORMAT = ("%(levelname)s %(name)s %(asctime)-15s "
          "%(filename)s:%(lineno)d %(message)s")
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

# %%
# Parameter
# time
start = '01.01.2020'
end = '01.05.2020'
# agents
nSepBSLagents = 100
pAgricultureBSLsep = 0.7
nBuildings = {'FSH': 300, 'REH': 800, 'SAH': 300, 'BAH': 100}
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

# set controller to use it or set variable to None
controller = CtrlDefault()

# %%
# prepare simulation
nSteps, time, SLP, HWP, Weather, Solar = getSimData(start, end, region)

# %%
cell = generateGenericCell(nBuildings, pAgents,
                           pPHHagents, pAgriculture,
                           pDHN, pPVplants, pHeatpumps, pCHP, pBTypes,
                           nSepBSLagents, pAgricultureBSLsep,
                           region, nSteps)

demand = cell.get_thermal_demand(True)
chpSystem = CellChpSystemThermal(demand, 0.75, 2*demand, 0.,
                                 0.98, 0.98, nSteps)
chpSystem.controller = controller
cell.add_chp_thermal(chpSystem)
#Add the wind turbine
windTurbine = Wind(160., 80., 4., 30., 0.4, nSteps)
cell.add_wind_turbine(windTurbine)

# %%
simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
         Solar.to_dict('list'))

# %%
plots.cellPowerBalance(cell, time)

# %%
plots.cellEnergyBalance(cell, time)

# %%
# Generate graph for energy generation chart of different energy types (PV, CHP, wind...).

PVgen_e = dataCollection.getCellsPVgeneration(cell)
CHPgen_e = dataCollection.getCellsCHPgeneration(cell)
WINDgen_e = cell.wind.gen_e.get_memory()

plots.EnergyGenerationChart(time, 'PV generation', PVgen_e, 'CHP generation',
                             CHPgen_e, 'Wind turbine generation', WINDgen_e)
