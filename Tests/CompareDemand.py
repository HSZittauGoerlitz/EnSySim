""" Compare SynPro Demand curves with EnSySim Demand

SynPro Settings:
 - 3 default persons
 - One-family house
 - Old building (110 kWh/(m^2 a) - 140 kWh/(m^2 a))
 - Potsdam reference weather (2010)
 - Circulation losses for hot water
 - No night setback for heating system
 - Simulation time is year 2015 with 15min time steps
"""

# %% Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import _addAgents, _loadBuildingData
import numpy as np
import pandas as pd
import plotly.graph_objs as go
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
end = "01.01.2016"
# environment
region = "East"

bType = "FSH"

# %% load data to compare
SynProData = pd.read_hdf("Tests/Data/SynProTestHouse.h5", key="TDPcirc")

# %% prepare simulation
nSteps, time, SLP_PHH, SLP_BSLa, SLP_BSLc, HWP, Weather, Solar = getSimData(start, end,
                                                                   region)
climate = pd.read_hdf("./BoundaryConditions/Weather/" + region +
                      ".h5", 'Standard')
Geo, U, g, n = _loadBuildingData(bType)

cell = Cell(climate.loc['EgNorm [kWh/m^2]', 'Value'],
            climate.loc['ToutNorm [degC]', 'Value'],
            nSteps)

# %% Create Building
# Parameter
bClass = "class_2"
mState = "original"
airState = "VentilationFree"
isAtDHN = True
a_uv_values = np.array([Geo.loc['Areas'].values.T[0],
                        U.loc[('UValues', Geo.loc['Areas'].index),
                              (bClass, mState)].values.T
                        ]).T
if bClass == 'class_5':
    infState = 'new'
else:
    infState = mState

# Building and Occupants
building = Building(Geo.loc['nUnits'].values.astype(np.uint32)[0][0],
                    a_uv_values,
                    U.loc[('DeltaU', ''), (bClass, mState)],
                    n.loc['Infiltration', infState],
                    n.loc[airState, infState],
                    (Geo.loc['cp_effective'] * Geo.loc['Volume']).Value,
                    g.loc[mState, bClass],
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

# overwrite outside temperature
T = np.array(SynProData.loc[:, "Tout [degC]"].values, dtype=np.float32)

# %% Run simulation
simulate(cell, nSteps, SLP_PHH, SLP_BSLa, SLP_BSLc, HWP, Weather.to_dict('list'), Solar.to_dict('list'))

# %% recalculate agents hot water demand
# this recalculation does not correspond exactly the simulation course
# due to the random portion in the model
# -> this portion is neglected here, since it's balanced in long time course
agent_hw = agent.hw_demand * HWP * 1e-3  # in kW
building_sh = np.array(cell.load_t.get_memory())*1e-3 - agent_hw  # in kW

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
fig = plots.buildingTemperature(cell.buildings[0], time, T, True)
fig.add_trace(go.Scatter(x=time, y=SynProData['Tin [degC]'],
                         line={'color': 'rgba(100, 149, 237, 0.5)',
                               'width': 1},
                         name="SynPro",
                         )
              )
fig = fig.set_subplots(rows=2, cols=1,
                       shared_xaxes=True,
                       vertical_spacing=0.02)
fig.update_xaxes(title_text="", row=1, col=1)
fig.update_xaxes(title_text="Time", row=2, col=1)
fig.update_yaxes(title_text="Heating State", row=2, col=1)
fig.add_trace(go.Scatter(x=time, y=SynProData['Heating state'],
                         line={'color': 'rgba(100, 149, 237, 0.5)',
                               'width': 1},
                         name="SynPro",
                         ),
              row=2, col=1
              )
fig.show()

# %%
print("EnSySim Buildings has a yearly space heating demand of {:.2f} kWh/m^2"
      .format(building_sh.sum() * 0.25 / Geo.loc[('A_living', ''), 'Value']))
