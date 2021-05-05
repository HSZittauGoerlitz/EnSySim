# %% Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import _addAgents, _loadBuildingData
from itertools import product
import numpy as np
import pandas as pd
from SystemComponentsFast import simulate, Building, Cell
import logging

# %% logger config
FORMAT = ('%(levelname)s %(name)s %(asctime)-15s '
          '%(filename)s:%(lineno)d %(message)s')
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.WARNING)

""" Following levels are used:
DEBUG: add manually to debug
INFO: feed back of successful operation
WARNING: logical problems
ERROR: operation failed
CRITICAL: simulation failed """

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

# Parameter
classes = ["class_" + str(nr) for nr in range(1, 6)]
mStates = ["original", "modernised"]
airStates = ["VentilationFree", "VentilationMech"]

isAtDHN = False

resParameter = ["Electrical Energy Generated [MWh]",
                "Electrical Energy Consumed [MWh]",
                "Thermal Energy Generated [MWh]",
                "Thermal Energy Consumed [MWh]",
                "Max. Building Temperature [degC]",
                "Min. Building Temperature [degC]",
                "Mean. Building Temperature [degC]",
                "CHP Full Load Hours [h]"]

# data frame for results
results = pd.DataFrame(columns=pd.MultiIndex.from_tuples(product(classes,
                                                                 mStates,
                                                                 airStates)),
                       index=resParameter)


# %% Create Building and Simulate
for bClass, mState, airState in results.columns.to_list():
    a_uv_values = np.array([Geo.loc['Areas'].values.T[0],
                            U.loc['UValues', (bClass, mState)]
                            ]).T
    if bClass == 'class_5':
        infState = 'new'
    else:
        infState = mState

    # cell
    cell = Cell(climate.loc['EgNorm [kWh/m^2]', 'Value'],
                climate.loc['ToutNorm [degC]', 'Value'],
                nSteps)

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

    # Add components
    building.add_dimensioned_chp(nSteps)

    # Add building to cell
    cell.add_building(building)

    simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
             Solar.to_dict('list'))

    # get results
    b = cell.buildings[0]
    gen_e = np.array(b.gen_e.get_memory())
    load_e = np.array(b.load_e.get_memory())
    gen_t = np.array(b.gen_t.get_memory())
    load_t = np.array(b.load_t.get_memory())
    bT = np.array(b.temperature_hist.get_memory())
    chp_gen_e = np.array(b.chp_system.gen_e.get_memory())

    results.loc['Electrical Energy Generated [MWh]',
                (bClass, mState, airState)] = gen_e.sum() * 0.25 * 1e-6
    results.loc['Electrical Energy Consumed [MWh]',
                (bClass, mState, airState)] = load_e.sum() * 0.25 * 1e-6
    results.loc['Thermal Energy Generated [MWh]',
                (bClass, mState, airState)] = gen_t.sum() * 0.25 * 1e-6
    results.loc['Thermal Energy Consumed [MWh]',
                (bClass, mState, airState)] = load_t.sum() * 0.25 * 1e-6
    results.loc['Max. Building Temperature [degC]',
                (bClass, mState, airState)] = bT.max()
    results.loc['Min. Building Temperature [degC]',  # exclude first week
                (bClass, mState, airState)] = bT[7*96:].min()
    results.loc['Mean. Building Temperature [degC]',
                (bClass, mState, airState)] = bT.mean()
    results.loc['CHP Full Load Hours [h]',
                (bClass, mState, airState)] = (chp_gen_e > 0.).sum() * 0.25

# %%
results

# %%
