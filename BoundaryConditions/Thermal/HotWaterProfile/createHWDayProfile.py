# %% Imports
import numpy as np
import pandas as pd

# %% load original data
loc = "./BoundaryConditions/Thermal/HotWaterProfile/"
data = pd.read_csv(loc + "HWPdata_Paper.csv", sep=";")

# %% generate HWP
HWP = pd.DataFrame()
HWP['Hour'] = data.HourOfDay
HWP['fProportion'] = data.Percentage * 1e-2 * 24  # % -> -
HWP.loc[:, 'fProportion'] *= 1 / HWP.fProportion.mean()  # scale to mean=1
HWP.fProportion.mean()

# %% test profile
Pday = np.round(np.random.random() * 5000.)  # W
Eday = 24. * Pday  # Wh
Eoriginal = (data.Percentage * 1e-2 * Eday).sum()
E_HWP = (HWP.fProportion * Pday).sum()  # must be equal to Eday
print("Given daily demand: {:.2f} Wh".format(Eday))
print("Recalculation with Percentage: {:.2f} Wh".format(Eoriginal))
print("Recalculation with HWP: {:.2f} Wh".format(E_HWP))

# %% Save Profile
HWP.to_hdf(loc + "HotWaterDayProfile.h5", key='PHH')
