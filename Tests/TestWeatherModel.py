# %% Imports
from BoundaryConditions.Simulation.SimulationData import (_getSimTime,
                                                          _getWeather)
from itertools import cycle
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

# %% Parameter
# region used for test
# Currently Supported: East, South, West, North
region = "East"
# time for test
# turn of year twice, one leap year
start = "01.12.2019"
end = "01.02.2021"

nTestCases = 10


# %% helper functions
def hex_to_rgba(hexCol):
    r = hexCol[1:3]
    g = hexCol[3:5]
    b = hexCol[5:]

    return 'rgba({0}, {1}, {2}, 0.8)'.format(int(r, 16),
                                             int(g, 16), int(b, 16))


def plotReferenceTemperatures(refTime, Tref, Tsum, Twin):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=refTime, y=Tref,
                             line={'color': 'rgba(0, 0, 0, 0.75)',
                                   'width': 1},
                             name="Reference"
                             ))
    fig.add_trace(go.Scatter(x=refTime, y=Tsum,
                             line={'color': 'rgba(199, 50, 0, 0.75)',
                                   'width': 1},
                             name="Summer extreme"
                             ))
    fig.add_trace(go.Scatter(x=refTime, y=Twin,
                             line={'color': 'rgba(2, 37, 177, 0.75)',
                                   'width': 1},
                             name="Winter extreme"
                             ))

    fig.update_layout(height=1300, width=2400,
                      title_text='Reference curves for region {}'
                                 .format(region))
    # add axis labels
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Temperature [degC]")
    # show figure
    fig.show()


def plotArrayTemperatures(time, nTestCases, region):
    fig = go.Figure()

    palette = cycle(px.colors.sequential.Viridis)

    for i in range(nTestCases):
        color = hex_to_rgba(next(palette))

        fig.add_trace(go.Scatter(x=time.time,
                                 y=_getWeather(time, region)[('Weather',
                                                              'T [degC]')],
                                 line={'color': color,
                                       'width': 1},
                                 name="T_{}".format(i+1)
                                 ))
    fig.update_layout(height=1300, width=2400,
                      title_text='Simulated temperature curves for region {}'
                                 .format(region))
    # add axis labels
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Temperature [degC]")
    # show figure
    fig.show()


# %% load/plot reference weather
RefWeather = pd.read_hdf("./BoundaryConditions/Weather/" + region + ".h5",
                         'Weather')
plotReferenceTemperatures(RefWeather.date_time,
                          RefWeather.reference['T [degC]'],
                          RefWeather.summer_extreme['T [degC]'],
                          RefWeather.winter_extreme['T [degC]'],
                          )

# %%
plotArrayTemperatures(_getSimTime(start, end), 10, region)

# %%
