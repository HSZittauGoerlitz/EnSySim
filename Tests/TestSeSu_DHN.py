# %% Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import _addAgents, _loadBuildingData
import numpy as np
import pandas as pd
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
nSteps, time, SLP, HWP, Weather = getSimData(start, end, region)
climate = pd.read_hdf("./BoundaryConditions/Weather/" + region +
                      ".h5", 'Standard')

Geo, U, g, n = _loadBuildingData(bType)

cell = Cell(climate.loc['EgNorm [kWh/m^2]', 'Value'],
            climate.loc['ToutNorm [degC]', 'Value'],
            nSteps)

# %% Create Building
# Parameter
bClass = "class_1"
mState = "original"  # "modernised"
airState = "VentilationFree"  # "VentilationMech"
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
                    (Geo.loc['cp_effective'] * Geo.loc['Volume']).Value,
                    g.loc[mState, bClass],
                    Geo.loc[('Volume')].values.astype(np.uint32)[0][0],
                    isAtDHN, cell.t_out_n, nSteps
                    )
# Create and add agents
_addAgents(building, 1., 1., 0.)

# Add building to cell
cell.add_building(building)

# %% Run simulation
simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'))

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
