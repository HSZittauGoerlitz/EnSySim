import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objs as go


COL_GEN = 'rgb(27,198,47)'  # color for generation
COL_CON = 'rgb(255,84,79)'  # color for consumption
COL_BAL = 'rgba(0,0,0,0.5)'  # color for balance


def arbitraryBalance(generation, load, time, unitPrefix,
                     title="", retFig=False):
    """Plot the power and energy balance for given curves

    Arguments:
        generation {np array} -- Course of generated power of type 'type_' [W]
        load {np array} -- Course of power load of type 'type_' [W]
        unitPrefix {str} -- Prefix used for power data, the data must be
                            converted accordingly
        time (pd series of datetime): Time

    Keyword Arguments:
        title {str} -- Title used for plot (default: {""})
        retFig {bool} -- When True figure is not showed, but returned
                         (default: {False})
    """
    # calculate resulting energy course
    dt = time.diff().dt.seconds / 3600.  # time difference in h
    energy_gen = generation.cumsum()
    energy_gen[1:] *= dt[1:]
    energy_load = load.cumsum()
    energy_load[1:] *= dt[1:]

    # Create Figure
    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.02)
    # Add Lines
    fig.add_trace(go.Scatter(x=time, y=generation,
                             line={'color': COL_GEN,
                                   'width': 1},
                             name="Generation",
                             legendgroup='Power'
                             ),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=-load,
                             line={'color': COL_CON,
                                   'width': 1},
                             name="Load",
                             legendgroup='Power'
                             ),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=generation-load,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="Balance",
                             legendgroup='Power'
                             ),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=energy_gen,
                             line={'color': COL_GEN,
                                   'width': 1},
                             name="Generation_en",
                             legendgroup='Energy',
                             showlegend=False
                             ),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=time, y=-energy_load,
                             line={'color': COL_CON,
                                   'width': 1},
                             name="Load_en",
                             legendgroup='Energy',
                             showlegend=False
                             ),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=time, y=energy_gen-energy_load,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="Balance_en",
                             legendgroup='Energy',
                             showlegend=False
                             ),
                  row=2, col=1)
    fig.update_layout(height=600, width=600,
                      title_text=title)
    # add axis labels
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Power [{}W]".format(unitPrefix),
                     row=1, col=1)
    fig.update_yaxes(title_text="Energy [{}W]".format(unitPrefix),
                     row=2, col=1)
    if retFig:
        return fig
    else:  # show figure
        fig.show()


def buildingTemperature(building, time, T, retFig=False):
    """ Plot the temperature course for given building

    Args:
          building (Building): Building for which the temperature course
                               shall be plotted
          time (pd series of datetime): Time
          T (np array): Outside Temperature during Simulation [degC]

    Keyword Arguments:
        retFig {bool} -- When True figure is not showed, but returned
                         (default: {False})
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time, y=building.temperature_hist.get_memory(),
                             line={'color': COL_CON,
                                   'width': 1},
                             name="building",
                             )
                  )
    fig.add_trace(go.Scatter(x=time, y=T,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="outside",
                             )
                  )
    fig.update_layout(height=600, width=600,
                      title_text="Building Temperature Course")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Temperature [degC]")
    if retFig:
        return fig
    else:  # show figure
        fig.show()


def cellPowerBalance(cell, time, retFig=False):
    """ Plot the electrical and thermal power balance of a cell
        for a simulation with known simulation time.

    Args:
        cell (Cell): Cell for which the data is plotted
        time (pd series of datetime): Time

    Keyword Arguments:
        retFig {bool} -- When True figure is not showed, but returned
                         (default: {False})
    """
    # get data
    gen_e = np.array(cell.gen_e.get_memory()) * 1e-6
    gen_t = np.array(cell.gen_t.get_memory()) * 1e-6
    load_e = np.array(cell.load_e.get_memory()) * 1e-6
    load_t = np.array(cell.load_t.get_memory()) * 1e-6
    # calculate balance
    bal_e = gen_e - load_e
    bal_t = gen_t - load_t
    # Create Figure
    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.02)
    # Add Lines
    fig.add_trace(go.Scatter(x=time, y=gen_e,
                             line={'color': COL_GEN,
                                   'width': 1},
                             name="Generation E",
                             legendgroup='Electrical'
                             ),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=-load_e,
                             line={'color': COL_CON,
                                   'width': 1},
                             name="Load E",
                             legendgroup='Electrical'
                             ),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=bal_e,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="Balance E",
                             legendgroup='Electrical'
                             ),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=gen_t,
                             line={'color': COL_GEN,
                                   'width': 1},
                             name="Generation T",
                             legendgroup='Thermal'
                             ),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=time, y=-load_t,
                             line={'color': COL_CON,
                                   'width': 1},
                             name="Load T",
                             legendgroup='Thermal'
                             ),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=time, y=bal_t,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="Balance T",
                             legendgroup='Thermal'
                             ),
                  row=2, col=1)
    fig.update_layout(height=600, width=600,
                      title_text="Cell Power Balance")
    # add axis labels
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Electrical Power [MW]", row=1, col=1)
    fig.update_yaxes(title_text="Thermal Power [MW]", row=2, col=1)

    if retFig:
        return fig
    else:  # show figure
        fig.show()


def cellEnergyBalance(cell, time):
    """ Plot the electrical and thermal cumulative energy balance of a cell
        for a simulation with known simulation time.

    Args:
        cell (Cell): Cell for which the data is plotted
        time (pd series of datetime): Time
    """
    dt = time.diff().dt.seconds / 3600.  # time difference in h
    # get data
    gen_e = np.array(cell.gen_e.get_memory()) * 1e-6
    gen_t = np.array(cell.gen_t.get_memory()) * 1e-6
    load_e = np.array(cell.load_e.get_memory()) * 1e-6
    load_t = np.array(cell.load_t.get_memory()) * 1e-6
    # calculate energy
    gen_e = gen_e.cumsum()
    gen_e[1:] *= dt[1:]
    gen_t = gen_t.cumsum()
    gen_t[1:] *= dt[1:]
    load_e = load_e.cumsum()
    load_e[1:] *= dt[1:]
    load_t = load_t.cumsum()
    load_t[1:] *= dt[1:]
    # calculate balance
    bal_e = gen_e - load_e
    bal_t = gen_t - load_t

    # Create Figure
    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.02)
    # Add Lines
    fig.add_trace(go.Scatter(x=time, y=gen_e,
                             line={'color': COL_GEN,
                                   'width': 1},
                             name="Generation E",
                             legendgroup='Electrical'
                             ),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=-load_e,
                             line={'color': COL_CON,
                                   'width': 1},
                             name="Load E",
                             legendgroup='Electrical'
                             ),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=bal_e,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="Balance E",
                             legendgroup='Electrical'
                             ),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=time, y=gen_t,
                             line={'color': COL_GEN,
                                   'width': 1},
                             name="Generation T",
                             legendgroup='Thermal'
                             ),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=time, y=-load_t,
                             line={'color': COL_CON,
                                   'width': 1},
                             name="Load T",
                             legendgroup='Thermal'
                             ),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=time, y=bal_t,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="Balance T",
                             legendgroup='Thermal'
                             ),
                  row=2, col=1)
    fig.update_layout(height=600, width=600,
                      title_text="Cell Energy Balance")
    # add axis labels
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Electrical Energy [MWh]", row=1, col=1)
    fig.update_yaxes(title_text="Thermal Energy [MWh]", row=2, col=1)
    # show figure
    fig.show()


def chargeState(storage, time, retFig=False):
    """ Plot the charge state for given storage

    Args:
          storage (Storage): Storage for which the charge course
                             shall be plotted
          time (pd series of datetime): Time

    Keyword Arguments:
        retFig {bool} -- When True figure is not showed, but returned
                         (default: {False})
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time,
                             y=np.array(storage.charge_hist.get_memory())*1e-3,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="charge",
                             )
                  )
    fig.update_layout(height=600, width=600,
                      title_text="Storage with max. capacity of {:.2f}kWh"
                                 .format(np.round(storage.cap * 1e-3, 2)))
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Charge [kWh]")
    if retFig:
        return fig
    else:  # show figure
        fig.show()


def runningState(utility, time, retFig=False):
    """ Plot on/state for given utility on basis of thermal generation

    Args:
            utility: chp or heatpump etc.
            time (pd series of datetime): Time
    """
    states = np.array(utility.gen_t.get_memory()).astype(bool).astype(int)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time,
                             y=states,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="charge",
                             )
                  )
    fig.update_layout(height=600, width=600,
                      title_text="On/Off states of Utility")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="State")
    if retFig:
        return fig
    else:  # show figure
        fig.show()


def compareCurves(time, values, names,
                  xLabel='Time', yLabel='', title='', retFig=False):
    """Create comparison plot for given curves

    Arguments:
        time {list of arrays} -- Time (abscissae) values to plot,
                                 either one for all or each separate
        values {list of arrays} -- Ordinate values of curves to plot
        names {list of str} -- Name for each curve

    Keyword Arguments:
        xLabel {str} -- Label for x axis (default: {'Time'})
        yLabel {str} -- Label for y axis (default: {''})
        title {str} -- Plot title (default: {''})
        retFig {bool} -- When True figure is not showed, but returned
                         (default: {False})
    """
    nCurves = len(values)

    if len(time) == nCurves:
        idxTimeMul = 1
    elif len(time) == 1:
        idxTimeMul = 0
    else:
        raise ValueError("Number of x-arrays must be one or equal to number "
                         "of given curves.")

    if len(names) != nCurves:
        raise ValueError("Number of namess must be equal to "
                         "number of given curves.")

    fig = go.Figure()

    for i in range(nCurves):
        fig.add_trace(go.Scatter(x=time[i*idxTimeMul],
                                 y=values[i],
                                 line={'width': 1},
                                 name=names[i],
                                 )
                      )

    fig.update_layout(height=600, width=600, title_text=title)
    fig.update_xaxes(title_text=xLabel)
    fig.update_yaxes(title_text=yLabel)
    if retFig:
        return fig
    else:  # show figure
        fig.show()
