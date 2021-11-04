# %%
# Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import _addAgents, _loadBuildingData
from SystemComponentsFast import simulate, Building, Cell
import pandas as pd
import numpy as np
from PostProcesing import plots
import logging

# %%
# Configure logging
FORMAT = ("%(levelname)s %(name)s %(asctime)-15s "
          "%(filename)s:%(lineno)d %(message)s")
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

# %%
# Parameters & Data
# simulation time
start = '01.01.2020'
end = '01.01.2021'
# environment
region = "East"
# generate data using helper functions
nSteps, time, SLP, HWP, Weather, Solar = getSimData(start, end, region)
# norm parameters (irradiance, temperature)
climate = pd.read_hdf("./BoundaryConditions/Weather/" + region +
                      ".h5", 'Standard')
# get reference year temperatures
refWeather = pd.read_hdf("./BoundaryConditions/Weather/" + region +
                         ".h5", 'Weather')
t_ref = refWeather.reference['T [degC]'].values

# create cell
cell = Cell(climate.loc['EgNorm [kWh/m^2]', 'Value'],
            climate.loc['ToutNorm [degC]', 'Value'],
            nSteps)

# building parameters
bType = "FSH"
bClass = "class_5"
mState = "original"  # "modernised"
airState = "VentilationFree"  # "VentilationMech"
isAtDHN = False
# get geometry
Geo, U, g, n = _loadBuildingData(bType)
# reformat data
a_uv_values = np.array([Geo.loc['Areas'].values.T[0],
                        U.loc['UValues', (bClass, mState)]
                        ]).T
if bClass == 'class_5':
    infState = 'new'
else:
    infState = mState
# create building
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
# create and add agents
_addAgents(building, 1., 1., 0.)
# add dimensioned pv
building.add_dimensioned_pv(cell.eg, nSteps)
# add dimensioned heatpump
building.add_dimensioned_heatpump(3.5, 40., t_ref,
                                  climate.loc['ToutNorm [degC]', 'Value'],
                                  nSteps)
# add building to cell
cell.add_building(building)

# %%
# Run simulation
simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
         Solar.to_dict('list'))

# %%
# Plot cell power balance
plots.cellPowerBalance(cell, time)

# %%
# Plot cell energy balance
plots.cellEnergyBalance(cell, time)

# %%
# Plot building temperature
plots.buildingTemperature(cell.buildings[0], time, Weather['T [degC]'])
# %%
plots.heatpumpSystemOperation(cell.buildings[0].get_hp_system(), time)
# %%

# %%
