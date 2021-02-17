import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objs as go


COL_GEN = 'rgb(27,198,47)'  # color for generation
COL_CON = 'rgb(255,84,79)'  # color for consumption
COL_BAL = 'rgba(0,0,0,0.5)'  # color for balance


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


def cellEnergyBalance(cell, time, step=0.25):
    """ Plot the electrical and thermal cumulative energy balance of a cell
        for a simulation with known simulation time.

    Args:
        cell (Cell): Cell for which the data is plotted
        time (pd series of datetime): Time
        step (float): Time step of time data [h] (Default: 0.25h)
    """
    # get data
    gen_e = np.array(cell.gen_e.get_memory()) * 1e-6
    gen_t = np.array(cell.gen_t.get_memory()) * 1e-6
    load_e = np.array(cell.load_e.get_memory()) * 1e-6
    load_t = np.array(cell.load_t.get_memory()) * 1e-6
    # calculate energy
    gen_e *= step
    gen_e = gen_e.cumsum()
    gen_t *= step
    gen_t = gen_t.cumsum()
    load_e *= step
    load_e = load_e.cumsum()
    load_t *= step
    load_t = load_t.cumsum()
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
