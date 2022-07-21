# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from Controller.Cell.CHP_SystemThermal import CtrlDefault
from GenericModel.Design import generateGenericCell
from GenericModel.PARAMETER import PBTYPES_NOW as pBTypes
from SystemComponentsFast import simulate, CellChpSystemThermal
from PostProcesing import plots
import plotly.graph_objs as go
import numpy as np
import logging

# %%
FORMAT = ("%(levelname)s %(name)s %(asctime)-15s "
          "%(filename)s:%(lineno)d %(message)s")
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

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

chpSystem.controller = controller
cell.add_chp_thermal(chpSystem)


# %%
# run the simulation
simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
         Solar.to_dict('list'))


# %%
plots.cellPowerBalance(cell, time)

# %%
plots.cellEnergyBalance(cell, time)

# %%
chpSystem = cell.get_thermal_chp_system()
chp_gen_e = np.array(chpSystem.chp.gen_e.get_memory())
CHPstate = chp_gen_e > 0.
fig = go.Figure()
fig.add_trace(go.Scatter(x=time, y=CHPstate,
                         line={'color': 'rgba(100, 149, 237, 0.5)',
                               'width': 1},
                         name="CHP state")
              )
fig.update_layout(height=600, width=600,
                  title_text="CHP operation")
fig.update_xaxes(title_text="Time")
fig.update_yaxes(title_text="On/Off")

# %%
chpSystem = cell.get_thermal_chp_system()
boiler_gen_t = np.array(chpSystem.boiler.gen_t.get_memory())
boile_state = boiler_gen_t > 0.
fig = go.Figure()
fig.add_trace(go.Scatter(x=time, y=boile_state,
                         line={'color': 'rgba(100, 149, 237, 0.5)',
                               'width': 1},
                         name="boiler state")
              )
fig.update_layout(height=600, width=600,
                  title_text="boiler operation")
fig.update_xaxes(title_text="Time")
fig.update_yaxes(title_text="On/Off")
# %%

plots.chargeState(chpSystem.storage, time)

# %%
