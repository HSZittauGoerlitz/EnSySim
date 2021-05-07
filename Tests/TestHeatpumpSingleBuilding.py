# %% Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import _addAgents, _loadBuildingData
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from SystemComponentsFast import simulate, Building, Cell
from PostProcesing import dataCollection, plots
import logging

# %% pid
import os
print(os.getpid())
# %% logger config
FORMAT = ('%(levelname)s %(name)s %(asctime)-15s '
          '%(filename)s:%(lineno)d %(message)s')
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.DEBUG)

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
bClass = "class_4"
mState = "modernised"  # "modernised"
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
                    Geo.loc[('A_living', ''), 'Value'], a_uv_values,
                    U.loc['DeltaU', (bClass, mState)],
                    n.loc['Infiltration', infState],
                    n.loc[airState, infState],
                    (Geo.loc['cp_effective'] * Geo.loc['Volume']).Value,
                    g.loc[mState, bClass],
                    Geo.loc[('Volume')].values.astype(np.uint32)[0][0],
                    isAtDHN, cell.t_out_n, nSteps
                    )
# Create and add agents
_addAgents(building, 1., 1., 0.)

# %% Add heatpump
# get reference year temperatures
refWeather = pd.read_hdf("./BoundaryConditions/Weather/" + region +
                         ".h5", 'Weather')

t_ref = refWeather.reference['T [degC]'].values

# supply temperatures for different classes of buildings
classTemperatures = {"class_1": {'original': 75, 'modernised': 65},
                     "class_2": {'original': 70, 'modernised': 60},
                     "class_3": {'original': 55, 'modernised': 45},
                     "class_4": {'original': 45, 'modernised': 40},
                     "class_5": {'original': 37, 'modernised': 32}}

t_supply = classTemperatures[bClass][mState]

# minimum Jahresarbeitszahl for BAFA-Förderung
# if bClass == 'class_5':
#     seas_perf_fac = 4.5
# else:
#     seas_perf_fac = 3.5

seas_perf_fac = 3.5


building.add_dimensioned_heatpump(seas_perf_fac,
                                  t_supply,
                                  t_ref,
                                  cell.t_out_n,
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

# %% yearly power factor
electrical_energy = np.array(cell.buildings[0].heatpump_system.heatpump.con_e.get_memory())
thermal_energy = np.array(cell.buildings[0].heatpump_system.heatpump.gen_t.get_memory())

power_factor = thermal_energy.sum() / electrical_energy.sum()

print(power_factor)

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
plots.buildingTemperature(b, time, Weather['T [degC]'])

# %%
plots.chargeState(b.heatpump_system.storage, time)

# %%
plots.compareCurves([time],
                    [thermal_energy, Weather['T [degC]']],
                    ['thermal output', 'outside  temperature'])

# %%
HPstate = np.array(b.heatpump_system.heatpump.gen_t.get_memory()) > 0.
Bstate = np.array(b.heatpump_system.boiler.gen_t.get_memory()) > 0.

fig_T = plots.buildingTemperature(b, time, Weather['T [degC]'], retFig=True)
fig_S = plots.chargeState(b.heatpump_system.storage, time, retFig=True)

fig_S.update_traces({'name': 'Storage'}, selector={'name': "charge"})

fig_T = fig_T.set_subplots(rows=3, cols=1,
                           shared_xaxes=True,
                           vertical_spacing=0.02,
                           subplot_titles=("",
                                           fig_S.layout.title.text,
                                           ""
                                           )
                           )

fig_T.add_trace(go.Scatter(x=time, y=HPstate,
                           line={'color': 'rgba(6, 99, 142, 0.7)',
                                 'width': 1},
                           name="HeatPump"),
                row=3, col=1
                )
fig_T.add_trace(go.Scatter(x=time, y=Bstate,
                           line={'color': 'rgba(85, 27, 192, 0.6)',
                                 'width': 1},
                           name="Boiler"),
                row=3, col=1
                )

fig_T.update_layout({'height': 1000, 'width': 1000})
fig_T.update_xaxes(title_text="", row=1, col=1)
fig_T.update_xaxes(title_text="", row=2, col=1)
fig_T.update_xaxes(title_text="Time", row=3, col=1)
fig_T.append_trace(fig_S['data'][0], row=2, col=1)
fig_T.update_yaxes(fig_S.layout['yaxis'], row=2, col=1)
fig_T.update_yaxes(title="State", row=3, col=1)

# %%
