# %% imports
import numpy as np
from plotly import graph_objects as go


# %%
def getCost(w, y, cMax=0.01, mu=0.5):
    e = np.abs(w-y)
    omega = np.tanh(np.sqrt(0.95) / mu)

    return np.tanh(e*omega)**2. * cMax


def getCostInv(w, y, cMax=0.01, mu=0.5):
    e = np.abs(w-y)
    omega = np.tanh(np.sqrt(0.95) / mu)

    return np.tanh(e/omega)**2. * cMax


# %%
y = np.arange(-10., 10.01, 0.001)
w = 0.

cMax = 1.
Mus = np.array([10.,50., 100., 1000])

# %%
fig = go.Figure()
fig.update_xaxes(title='plant output')
fig.update_yaxes(title='costs')

for mu in Mus:
    c = getCost(w, y, cMax, mu)
    line = go.Scatter({"x": y,
                       "y": c,
                       "name": "mu: {}".format(mu),
                       "yaxis": "y1",
                       "line": {"width": 1}
                       })
    fig.add_trace(line)

fig

# %%
fig = go.Figure()
fig.update_xaxes(title='plant output')
fig.update_yaxes(title='costs')

for mu in Mus:
    c = getCostInv(w, y, cMax, mu)
    line = go.Scatter({"x": y,
                       "y": c,
                       "name": "mu: {}".format(mu),
                       "yaxis": "y1",
                       "line": {"width": 1}
                       })
    fig.add_trace(line)

fig

# %%
