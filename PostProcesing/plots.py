import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objs as go


COL_GEN = 'rgb(27,198,47)'  # color for generation
COL_CON = 'rgb(255,84,79)'  # color for consumption
COL_BAL = 'rgba(0,0,0,0.5)'  # color for balance


def arbitraryBalance(generation, load, time, unitPrefix, title=""):
    """Plot the power and energy balance for given curves

    Arguments:
        generation {np array} -- Course of generated power of type 'type_' [W]
        load {np array} -- Course of power load of type 'type_' [W]
        unitPrefix {str} -- Prefix used for power data, the data must be
                            converted accordingly
        time (pd series of datetime): Time

    Keyword Arguments:
        title {str} -- Title used for plot (default: {""})
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
    fig.update_layout(height=600, width=1000,
                      title_text=title)
    # add axis labels
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Power [{}W]".format(unitPrefix),
                     row=1, col=1)
    fig.update_yaxes(title_text="Energy [{}W]".format(unitPrefix),
                     row=2, col=1)
    # show figure
    fig.show()


def buildingTemperature(building, time, T):
    """ Plot the temperature course for given building

    Args:
          building (Building): Building for which the temperature course
                               shall be plotted
          time (pd series of datetime): Time
          T (np array): Outside Temperature during Simulation [degC]
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
    fig.update_layout(height=600, width=1000,
                      title_text="Building Temperature Course")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Temperature degC")
    fig.show()


def cellPowerBalance(cell, time):
    """ Plot the electrical and thermal power balance of a cell
        for a simulation with known simulation time.

    Args:
        cell (Cell): Cell for which the data is plotted
        time (pd series of datetime): Time
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
    fig.update_layout(height=600, width=1000,
                      title_text="Cell Power Balance")
    # add axis labels
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Electrical Power [MW]", row=1, col=1)
    fig.update_yaxes(title_text="Thermal Power [MW]", row=2, col=1)
    # show figure
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
    fig.update_layout(height=600, width=1000,
                      title_text="Cell Energy Balance")
    # add axis labels
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Electrical Energy [MWh]", row=1, col=1)
    fig.update_yaxes(title_text="Thermal Energy [MWh]", row=2, col=1)
    # show figure
    fig.show()


def chargeState(storage, time):
    """ Plot the charge state for given storage

    Args:
          storage (Storage): Storage for which the charge course
                             shall be plotted
          time (pd series of datetime): Time
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time,
                             y=np.array(storage.charge_t.get_memory())*1e-3,
                             line={'color': COL_BAL,
                                   'width': 1},
                             name="charge",
                             )
                  )
    fig.update_layout(height=600, width=1000,
                      title_text="Storage charge state")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Charge [kWh]")
    fig.show()
