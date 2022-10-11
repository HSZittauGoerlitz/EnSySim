# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from Controller.Cell.CHP_SystemThermal import CtrlDefault
from GenericModel.Design import _check_pBTypes, generateGenericCell
from GenericModel.PARAMETER import PBTYPES_NOW as pBTypes
from PostProcesing.dataCollection import getCellsCHPgeneration, getCellsPVgeneration, cumulativeEnergy
from SystemComponentsFast import simulate, CellChpSystemThermal, Wind, PV
from PostProcesing import plots
from plotly.subplots import make_subplots
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

# data for Flächenländer:
# seperate agents
nSepBSLagents = 100
pAgricultureBSLsep = 0.7
# pHH buildings
nBuildings = {'FSH': 634*4, 'REH': 338*4, 'SAH': 20*4, 'BAH': 8*4}
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
# generate cell
cell = generateGenericCell(nBuildings, pAgents,
                           pPHHagents, pAgriculture,
                           pDHN, pPVplants, pHeatpumps, pCHP, pBTypes,
                           nSepBSLagents, pAgricultureBSLsep,
                           region, nSteps)

# get dhn demand
demand_th = cell.get_thermal_demand(True)
# generate chp system with storage
chpSystem = CellChpSystemThermal(demand_th, 0.35, 2*demand_th, 0.05,
                                 0.98, 0.98, nSteps)
# configure controller
chpSystem.controller = None#controller
# add chp system to cell
cell.add_chp_thermal(chpSystem)

# get electrical demand
demand_el = cell.get_electrical_demand()
# add wind turbine
windTurbine = Wind(105., 90., 4., 12., 30., 0.115, nSteps)
cell.add_wind_turbine(windTurbine)

# add PV plant
pvPlant = PV(nSteps)
pvPlant.size_cell_pv(100.)
cell.add_pv(pvPlant)
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
plots.chargeState(chpSystem.storage, time)

# %%
# Generate graph for energy generation chart of different energy types (PV,
# CHP, wind...).

PVgen_e = getCellsPVgeneration(cell)
CHPgen_e = getCellsCHPgeneration(cell)
Windgen_e = cell.wind.gen_e.get_memory()

unit = "Electrical Power [MW]"
plots.EnergyGenerationChart(time, unit,
                            'PV', PVgen_e,
                            'building CHP', CHPgen_e,
                            'cell CHP', chp_gen_e,
                            'wind', Windgen_e)

# This second graph graph is meant to show the generation stacked
# across the year.

stackedPVgen_e = cumulativeEnergy(PVgen_e)
stackedCHPgen_e = cumulativeEnergy(CHPgen_e)
stackedWINDgen_e = cumulativeEnergy(Windgen_e)
stacked_chp_gen_e = cumulativeEnergy(chp_gen_e)

unit = "Electrical Energy [MWh]"
plots.EnergyGenerationChart(time, unit,
                            'PV', stackedPVgen_e,
                            'building CHP', stackedCHPgen_e,
                            'cell CHP', stacked_chp_gen_e,
                            'wind', stackedWINDgen_e)

#%%
plots.runningState(cell.get_thermal_chp_system(), time)
