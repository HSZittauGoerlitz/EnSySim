""" Design of HiL experiments with THERESA """
# %% Imports
# Model
from Examples.TheresaExp.Basic.Model import (addTheresaSystem,
                                             getDefaultCellData)
from SystemComponentsFast import simulate
# Post processing
import numpy as np
from PostProcesing.plots import COL_BAL
from PostProcesing import plots
import plotly.graph_objs as go
from plotly.subplots import make_subplots


# %% prepare Simulation
start = '23.01.2020'
end = '24.01.2020'

nSteps, time, SLP, HWP, Weather, Solar, cell = getDefaultCellData(start, end)
cell = addTheresaSystem(cell, nSteps)

# %%
simulate(cell, nSteps, SLP.to_dict('list'), HWP, Weather.to_dict('list'),
         Solar.to_dict('list'))

# %%
ts = cell.get_theresa_system()
fig_S = plots.chargeState(ts.storage, time, retFig=True)
PBfig = plots.cellPowerBalance(cell, time, True)

CellFig = make_subplots(rows=4, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.02,
                        subplot_titles=("", "",
                                        ("Storage with max. capacity of "
                                         "{:.2f}MWh")
                                        .format(np.round(ts.storage.cap * 1e-6,
                                                         2)),
                                        "Environment Temperature"
                                        ),
                        )

CellFig.update_layout({'height': 1000, 'width': 1000,
                       'title': "Cell overview"})
CellFig.add_trace(PBfig['data'][0], row=1, col=1)
CellFig.add_trace(PBfig['data'][1], row=1, col=1)
CellFig.add_trace(PBfig['data'][2], row=1, col=1)
CellFig.add_trace(PBfig['data'][3], row=2, col=1)
CellFig.add_trace(PBfig['data'][4], row=2, col=1)
CellFig.add_trace(PBfig['data'][5], row=2, col=1)
CellFig.add_trace(go.Scatter(x=time,
                             y=np.array(ts.storage
                                        .charge_hist.get_memory())*1e-6,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="charge",
                             ), row=3, col=1)
CellFig.add_trace(go.Scatter(x=time, y=Weather['T [degC]'].values,
                             line={'color': 'rgba(100, 149, 237, 0.5)',
                                   'width': 1},
                             name="CHP state"),
                  row=4, col=1
                  )
CellFig.update_xaxes(title_text="", row=1, col=1)
CellFig.update_xaxes(title_text="", row=2, col=1)
CellFig.update_xaxes(title_text="", row=3, col=1)
CellFig.update_xaxes(title_text="Time", row=4, col=1)
CellFig.update_yaxes({'title': {'text': PBfig.layout.yaxis.title.text}},
                     row=1, col=1)
CellFig.update_yaxes({'title': {'text': PBfig.layout.yaxis2.title.text}},
                     row=2, col=1)
CellFig.update_yaxes({'title': {'text': "Charge [MWh]"}},
                     row=3, col=1)
CellFig.update_yaxes({'title': {'text': "Temperature in degC"}},
                     row=4, col=1)

# %%
plots.cellEnergyBalance(cell, time)
