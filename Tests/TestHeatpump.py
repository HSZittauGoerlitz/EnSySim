# %% Imports
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import _addAgents, _loadBuildingData
from itertools import product
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from SystemComponentsFast import simulate, Building, Cell
import logging

# %% pid
import os
print(os.getpid())

# %% logger config
# Following levels are used:
# DEBUG: add manually to debug
# INFO: feed back of successful operation
# WARNING: logical problems
# ERROR: operation failed, in rust 'panic!' is used
# CRITICAL: simulation failed
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



# Parameter
classes = ["class_" + str(nr) for nr in range(1, 6)]
mStates = ["original", "modernised"]
airStates = ["VentilationFree", "VentilationMech"]

isAtDHN = False

resParameter = ["Electrical Energy Generated [MWh]",
                "Electrical Energy Consumed [MWh]",
                "Thermal Energy Generated [MWh]",
                "Supplied by Heatpump [MWh]", 
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
# %% Create Building

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

# Parameter
for bClass, mState, airState in results.columns.to_list():
    try:
        logging.debug("class:" + bClass +
                      ", state: " + mState +
                      ", ventilation: " + airState)
        # create cell
        cell = Cell(climate.loc['EgNorm [kWh/m^2]', 'Value'],
                    climate.loc['ToutNorm [degC]', 'Value'],
                    nSteps)

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

        # supply temperature
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

        simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
                 Solar.to_dict('list'))

        # get results
        b = cell.buildings[0]
        gen_e = np.array(b.gen_e.get_memory())
        load_e = np.array(b.load_e.get_memory())
        gen_t = np.array(b.gen_t.get_memory())
        hp_gen_t = np.array(cell.buildings[0].heatpump_system.
                            heatpump.gen_t.get_memory())
        load_t = np.array(b.load_t.get_memory())
        bT = np.array(b.temperature_hist.get_memory())
        hp_con_e = np.array(b.heatpump_system.con_e.get_memory())

        results.loc['Electrical Energy Generated [MWh]',
                    (bClass, mState, airState)] = gen_e.sum() * 0.25 * 1e-6
        results.loc['Electrical Energy Consumed [MWh]',
                    (bClass, mState, airState)] = load_e.sum() * 0.25 * 1e-6
        results.loc['Thermal Energy Generated [MWh]',
                    (bClass, mState, airState)] = gen_t.sum() * 0.25 * 1e-6
        results.loc['Supplied by Heatpump [MWh]',
                    (bClass, mState, airState)] = hp_gen_t.sum() * 0.25 * 1e-6
        results.loc['Thermal Energy Consumed [MWh]',
                    (bClass, mState, airState)] = load_t.sum() * 0.25 * 1e-6
        results.loc['Max. Building Temperature [degC]',
                    (bClass, mState, airState)] = bT.max()
        results.loc['Min. Building Temperature [degC]',  # exclude first week
                    (bClass, mState, airState)] = bT[7*96:].min()
        results.loc['Mean. Building Temperature [degC]',
                    (bClass, mState, airState)] = bT.mean()
        results.loc['CHP Full Load Hours [h]',
                    (bClass, mState, airState)] = (hp_con_e > 0.).sum() * 0.25
        power_factor = hp_gen_t.sum() / hp_con_e.sum()
        logging.debug("yearly power factor:  {:.2f}"
                      .format(power_factor))

    except:
        logging.debug("heatpump configuration not feasable!!!!!!!!!")
        # %% Add building to cell
        building.is_at_dhn = True
        cell.add_building(building)

        simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
                 Solar.to_dict('list'))

        # get results
        b = cell.buildings[0]
        gen_e = np.array(b.gen_e.get_memory())
        load_e = np.array(b.load_e.get_memory())
        gen_t = np.array(b.gen_t.get_memory())
        gen_t = np.array(b.gen_t.get_memory())
        load_t = np.array(b.load_t.get_memory())
        bT = np.array(b.temperature_hist.get_memory())

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

# %%
results
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
