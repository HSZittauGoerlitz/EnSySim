""" Calculate heating limit temperature for different building types """
# %% Imports
from matplotlib import pyplot as plt
import numpy as np
from scipy.stats import linregress

# % Data
# Data by Energiedepesche 1/2007
Tlim = np.array([15., 17., 14., 16., 12., 15., 11.5, 14., 10.5, 12., 9.5, 11.])
Pheat = np.array([80., 150., 60., 120., 25., 80., 20., 60., 15., 30., 5., 20.])

# %% determine Model
m, n, r, _, err = linregress(Pheat, Tlim)
print("Correlation coefficient: {:.2f}".format(r))
print("Resulting lin. Model is: T(P) = {:.2f} P + {:.2f}".format(m, n))
print("Std. error of regression: {:.2f}".format(err))


def fTHeatLim(Pheat):
    T = m*Pheat + n

    T[T < 9.5] = 9.5
    T[T > 17.] = 17.

    return T


P = np.arange(0., 201.)
T = fTHeatLim(P)

# %% Show results
fig = plt.figure(figsize=(10, 10))
ax = plt.subplot(1, 1, 1)
ax.set_xlabel("Specific Heatingpower $[\\frac{W}{m^2}]$", fontsize=16)
ax.set_ylabel("Min. heating temperature $[C^\\circ]$", fontsize=16)
ax.scatter(Pheat, Tlim, marker='x')
ax.plot(P, T, 'k', linewidth=1)
ax.grid()
ax.set_axisbelow(True)
ax.legend(["Data", "Model"], fontsize=14)

# %%
