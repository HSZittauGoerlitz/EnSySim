# %% imports
import json
import os
import pandas as pd

# %% parameter
# HINT: Standard mean annual global irradiation in kWh/m^2
# choose location for execution via vs code jupyter or script
cwd = os.getcwd()
if cwd.split(os.sep)[-1] == "Weather":
    loc = cwd + os.sep
else:
    loc = "pyEnSySim/BoundaryConditions/Weather/"

# %% load data
with open(loc + "Weather.json", 'r') as wf:
    data = json.load(wf)

regions = ['East', 'South', 'West', 'North']


# %% helper
def getRegionData(data, region):
    region_data = data[region]
    standard_data = data['dimensioning'][region]

    region_data = pd.DataFrame.from_dict(region_data)
    standard_data = pd.DataFrame.from_dict({'standard data': standard_data})

    return (region_data, standard_data)


# %% run
for region in regions:
    rd, sd = getRegionData(data, 'East')
    store = pd.HDFStore(region + '.h5')
    store['Weather'] = rd
    store['Standard'] = sd
    store.close()

# %%
