""" Compare SynPro Demand curves with EnSySim Demand

SynPro Settings:
 - 3 default persons
 - one-family house
 - old building (110 kWh/(m^2 a) - 140 kWh/(m^2 a))
 - Potsdam reference weather (2010)
 - No circulation losses for hot water
 - No night setback for heating system
 - Simulation time is year 2015 with 15min time steps
h5 file key = 'ThreeDefaultPersons'
"""

# %% Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import _addAgents, _loadBuildingData
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from SystemComponentsFast import simulate, Building, Cell
from PostProcesing import plots
import logging

# %% logger config
FORMAT = ('%(levelname)s %(name)s %(asctime)-15s '
          '%(filename)s:%(lineno)d %(message)s')
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

# %% Parameter
# time
start = "01.01.2015"
end = "31.12.2015"
# environment
region = "East"

bType = "FSH"

# %% prepare simulation
nSteps, time, SLP_PHH, SLP_BSLa, SLP_BSLc, HWP, T, Eg = getSimData(start, end,
                                                                   region)
climate = pd.read_hdf("./BoundaryConditions/Weather/" + region +
                      ".h5", 'Standard')
Geo, U, n = _loadBuildingData(bType)

cell = Cell(climate.loc['EgNorm kWh', 'Value'],
            climate.loc['ToutNorm degC', 'Value'],
            nSteps)

# %% Create Building
# Parameter
bClass = "class_1"
mState = "original"
airState = "VentilationFree"
isAtDHN = True
a_uv_values = np.array([Geo.loc['Areas'].values.T[0],
                        U.loc['UValues', (bClass, mState)]
                        ]).T
if bClass == 'class_5':
    infState = 'new'
else:
    infState = mState

# Building and Occupants
building = Building(Geo.loc['nUnits'].values.astype(np.uint32)[0][0],
                    a_uv_values,
                    U.loc['DeltaU', (bClass, mState)],
                    n.loc['Infiltration', infState],
                    n.loc[airState, infState],
                    15. * Geo.loc[('Volume')].Value,  # cp_eff [Wh/K]
                    Geo.loc[('Volume')].values.astype(np.uint32)[0][0],
                    isAtDHN, cell.t_out_n, nSteps
                    )
# Create and add agents
_addAgents(building, 1., 1., 0.)

# set coc in relation to electrical demand data of SynPro ~3800kWh/a)
agent = building.agents[0]
agent.overwrite_coc(3.9)
building.replace_agent(0, agent)

# Add building to cell
cell.add_building(building)

# load SynPro weather data and replace temperature
weather = pd.read_hdf("Tests/Data/TRY_2010_Potsdam.h5", key='Weather')
fT = interp1d((weather.time - weather.time[0]).dt.total_seconds(),
              weather['T [degC]'])
T = np.array(fT((time - time[0]).dt.total_seconds()), dtype=np.float32)

# %% Run simulation
simulate(cell, nSteps, SLP_PHH, SLP_BSLa, SLP_BSLc, HWP, T, Eg)

# %% recalculate agents hot water demand
# this recalculation does not correspond exactly the simulation course
# due to the random portion in the model
# -> this portion is neglected here, since it's balanced in long time course
agent_hw = agent.hw_demand * HWP * 1e-3  # in kW
building_sh = np.array(cell.load_t.get_memory())*1e-3 - agent_hw  # in kW

# %% load data to compare
SynProData = pd.read_hdf("Tests/Data/SynProTestHouse_ThreeDefaultPersons.h5")

# %% compare electrical demand
plots.compareCurves([SynProData.time],
                    [SynProData['P_Electrical [W]']*1e-3,
                     np.array(cell.load_e.get_memory())*1e-3],
                    ['SynPro', 'EnSySim'], yLabel='Electrical Power in kW',
                    title='Comparison of electrical demand for one household')

plots.compareCurves([SynProData.time],
                    [SynProData['P_Electrical [W]'].cumsum()*1e-3*0.25,
                     np.array(cell.load_e.get_memory()).cumsum()*1e-3*0.25],
                    ['SynPro', 'EnSySim'], yLabel='Electrical Energy in kWh')

# %% compare space heating demand
plots.compareCurves([SynProData.time],
                    [SynProData['Q_SpaceHeating [W]']*1e-3,
                     building_sh],
                    ['SynPro', 'EnSySim'], yLabel='Thermal Power in kW',
                    title='Comparison of buildings heat losses')

plots.compareCurves([SynProData.time],
                    [SynProData['Q_SpaceHeating [W]'].cumsum()*1e-6*0.25,
                     building_sh.cumsum()*1e-3*0.25],
                    ['SynPro', 'EnSySim'], yLabel='Thermal Energy in MWh')

# %% compare hot water demand
plots.compareCurves([SynProData.time],
                    [SynProData['Q_HotWater [W]']*1e-3,
                     agent_hw],
                    ['SynPro', 'EnSySim'], yLabel='Thermal Power in kW',
                    title='Comparison of residents hot water demand')

plots.compareCurves([SynProData.time],
                    [SynProData['Q_HotWater [W]'].cumsum()*1e-6*0.25,
                     agent_hw.cumsum()*1e-3*0.25],
                    ['SynPro', 'EnSySim'], yLabel='Thermal Energy in MWh')

# %%
plots.buildingTemperature(cell.buildings[0], time, T)

# %%
