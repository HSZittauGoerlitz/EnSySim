# %% Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import _addAgents, _loadBuildingData
import numpy as np
import pandas as pd
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
start = "01.01.2020"
end = "01.01.2021"
# environment
region = "East"

bType = "FSH"


# %% prepare simulation
nSteps, time, SLP_PHH, SLP_BSLa, SLP_BSLc, HWP, T, Eg = getSimData(start, end,
                                                                   region)
climate = pd.read_hdf("./BoundaryConditions/Weather/" + region +
                      ".h5", 'Standard')
Geo, U, n = _loadBuildingData(bType)

cell = Cell(climate.loc['Eg', 'standard data'],
            climate.loc['T', 'standard data'],
            nSteps)


# %% Create Building
# Parameter
bClass = "class_1"
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
                    15. * Geo.loc['A_living'].Value,  # cp_eff [Wh/K]
                    Geo.loc[('Volume')].values.astype(np.uint32)[0][0],
                    isAtDHN, cell.t_out_n, nSteps
                    )
# Create and add agents
_addAgents(building, 1., 1., 0.)

# Add components


# Add building to cell
cell.add_building(building)


# %%
simulate(cell, nSteps, SLP_PHH, SLP_BSLa, SLP_BSLc, HWP, T, Eg)


# %%
plots.cellPowerBalance(cell, time)


# %%
plots.cellEnergyBalance(cell, time)


# %%
b = cell.buildings[0]
plots.buildingTemperature(b, time)


# %%
