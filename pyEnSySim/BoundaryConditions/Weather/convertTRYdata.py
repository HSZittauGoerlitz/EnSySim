# %% imports
import pandas as pd
import numpy as np

# %% read file and get extends of columns
path = "pyEnSySim/BoundaryConditions/Weather/"
file_name = "TRY2015_508912148089_Jahr.dat"

file = open(file_name)
all_lines = file.readlines()
chars = list(all_lines[36]) # better search for ***
file.close()

extends = []
i = 0
j = 0
last_char = False

for char in chars:
    if char == ' ' and last_char is True:
        extends.append((i, j))
        j += 1
        i = j
        last_char = False
    elif char == ' ':
        j += 1
    else:
        j += 1
        last_char = True

# %% get data from files
df15 = pd.read_fwf(file_name,
                   colspecs=extends,
                   skiprows=34,
                   names=['RW', 'HW', 'MM', 'DD', 'HH', 't', 'p', 'WR', 'WG',
                          'N', 'x', 'RF', 'B', 'D', 'A', 'E', 'IL'],)

file_name = "TRY2045_508912148089_Jahr.dat"
df45 = pd.read_fwf(file_name,
                   colspecs='infer',
                   skiprows=36,
                   names=['RW', 'HW', 'MM', 'DD', 'HH', 't', 'p', 'WR', 'WG',
                          'N', 'x', 'RF', 'B', 'D', 'A', 'E', 'IL'],)
# %% convert to multiindex, only keep temperatures
mi = pd.MultiIndex.from_frame(df15[['MM', 'DD', 'HH']],
                              names=['month', 'day', 'hour'])

dfmi = pd.DataFrame(np.array([df15.t.values, df45.t.values]).transpose(),
                    index=mi,
                    columns=['temperatures_15', 'temperatures_45'])


store = pd.HDFStore("TRY2015.h5")
store['TRY'] = dfmi
store.close()
