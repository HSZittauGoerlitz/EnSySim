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
logging.getLogger().setLevel(logging.DEBUG)

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
bClass = "class_5"
mState = "original"  # "modernised"
airState = "VentilationFree"  # "VentilationMech"
isAtDHN = False
a_uv_values = np.array([Geo.loc['Areas'].values.T[0],
                        U.loc['UValues', (bClass, mState)]
                        ]).T
if bClass == 'class_1':
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

# %% Add heatpump
# get reference year temperatures
path = "BoundaryConditions/Weather/"
file_name = "TRY2015.h5"

df = pd.read_hdf(path+file_name)

t_ref = df['temperatures_15']

# classes of buildings for heating temperatures
classTemperatures = {"class_1": 55,
                     "class_2": 55,
                     "class_3": 55,
                     "class_4": 45,
                     "class_5": 35}
t_supply = classTemperatures[bClass]

# minimum Jahresarbeitszahl for BAFA-Förderung
if infState == 'new':
    seas_perf_fac = 4.5
else:
    seas_perf_fac = 3.5

building.add_dimensioned_heatpump(seas_perf_fac,
                                  t_supply,
                                  t_ref,
                                  1)
logging.debug("installed {:.2f}W thermal heatpump generation"
              .format(building.heatpump.heatpump.pow_t))
logging.debug("maximum heat load is {:.2f}W"
              .format(building.q_hln))

# %% Add building to cell
cell.add_building(building)


# %%
simulate(cell, nSteps, SLP_PHH, SLP_BSLa, SLP_BSLc, HWP, T, Eg)


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
plots.buildingTemperature(b, time, T)
