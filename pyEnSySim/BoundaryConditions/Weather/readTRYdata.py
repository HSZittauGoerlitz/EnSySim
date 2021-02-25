# %% imports
import pandas as pd
import numpy as np

# %% read file
path = "pyEnSySim/BoundaryConditions/Weather/"
file_name = "TRY2015_508912148089_Jahr.dat"

df = pd.read_fwf(file_name,
                 colspecs='infer',
                 skiprows=34,
                 names=['RW', 'HW', 'MM', 'DD', 'HH', 't', 'p', 'WR', 'WG',
                        'N', 'x', 'RF', 'B', 'D', 'A', 'E', 'IL'],
                 )

# %% convert to multiindex
_df = df[['MM', 'DD', 'HH']]
index = [np.array(_df['MM']), np.array(_df['DD']), np.array(_df['HH'])]
_dfmi = pd.MultiIndex.from_frame(_df, names=['month', 'day', 'hour'])
dfmi = pd.Series(np.array(df['t']), index=index)

# %%
display(dfmi)
# %%
dfmi = _dfmi.append(df['t'])
# %%
display(dfmi)
# %%
print(dfmi['t'])
# %%
