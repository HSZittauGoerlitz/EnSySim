# %% Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import _addAgents, _loadBuildingData
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from SystemComponentsFast import simulate, Building, Cell
from PostProcesing import dataCollection, plots
import logging

# %% logger config
FORMAT = ('%(levelname)s %(name)s %(asctime)-15s '
          '%(filename)s:%(lineno)d %(message)s')
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

# %% Parameter
# time
start = "01.01.2020"
end = "01.01.2021"
# environment
region = "East"

bType = "FSH"

# %% prepare simulation
nSteps, time, SLP, HWP, Weather, Solar = getSimData(start, end, region)
climate = pd.read_hdf("./BoundaryConditions/Weather/" + region +
                      ".h5", 'Standard')

Geo, U, g, n = _loadBuildingData(bType)

cell = Cell(climate.loc['EgNorm [kWh/m^2]', 'Value'],
            climate.loc['ToutNorm [degC]', 'Value'],
            nSteps)

# %% Create Building
# Parameter
bClass = "class_5"
mState = "original"  # "modernised"
airState = "VentilationFree"  # "VentilationMech"
isAtDHN = False
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
                    (Geo.loc['cp_effective'] * Geo.loc['Volume']).Value,
                    g.loc[mState, bClass],
                    Geo.loc[('Volume')].values.astype(np.uint32)[0][0],
                    isAtDHN, cell.t_out_n, nSteps
                    )
# Create and add agents
building = _addAgents(building, 1., 1., 0.)

# %% Add heatpump
# get reference year temperatures
refWeather = pd.read_hdf("./BoundaryConditions/Weather/" + region +
                         ".h5", 'Weather')

t_ref = refWeather.reference['T [degC]'].values

# classes of buildings for heating temperatures
classTemperatures = {"class_1": 55,
                     "class_2": 55,
                     "class_3": 55,
                     "class_4": 45,
                     "class_5": 35}
t_supply = classTemperatures[bClass]

# minimum Jahresarbeitszahl for BAFA-Förderung
if infState == 'new':
    seas_perf_fac = 3.
else:
    seas_perf_fac = 3.5

building.add_dimensioned_heatpump(seas_perf_fac,
                                  t_supply,
                                  t_ref,
                                  nSteps)
logging.debug("installed {:.2f}W thermal heatpump generation"
              .format(building.heatpump_system.heatpump.pow_t))
logging.debug("maximum heat load is {:.2f}W"
              .format(building.q_hln))

# %% Add building to cell
cell.add_building(building)


# %%
simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
         Solar.to_dict('list'))


# %%
plots.cellPowerBalance(cell, time)


# %%
plots.cellEnergyBalance(cell, time)


# %%
gen_t, load_t = dataCollection.getBuildingsThermalBalance(cell)
plots.arbitraryBalance(gen_t*1e-3, load_t*1e-3, time, 'k',
                       'Thermal balance in test building')

# %%
b = cell.buildings[0]
HPstate = np.array(b.heatpump_system.con_e.get_memory()) > 0.

fig_T = plots.buildingTemperature(b, time, Weather['T [degC]'], retFig=True)
fig_S = plots.chargeState(b.heatpump_system.storage, time, retFig=True)

fig_S.update_traces({'name': 'Storage'}, selector={'name': "charge"})

fig_T = fig_T.set_subplots(rows=2, cols=1,
                           shared_xaxes=True,
                           vertical_spacing=0.02,
                           subplot_titles=("",
                                           fig_S.layout.title.text
                                           ),
                           specs=[[{"secondary_y": True}],
                                  [{"secondary_y": False}]
                                  ]
                           )

fig_T.add_trace(go.Scatter(x=time, y=HPstate,
                           line={'color': 'rgba(100, 149, 237, 0.5)',
                                 'width': 1},
                           name="HP state"),
                secondary_y=True
                )

fig_T.update_layout({'height': 1000, 'width': 1000})
fig_T.update_xaxes(title_text="", row=1, col=1)
fig_T.update_xaxes(title_text="", row=2, col=1)
fig_T.append_trace(fig_S['data'][0], row=2, col=1)
fig_T.update_yaxes(fig_S.layout['yaxis'], row=2, col=1)

# %%
