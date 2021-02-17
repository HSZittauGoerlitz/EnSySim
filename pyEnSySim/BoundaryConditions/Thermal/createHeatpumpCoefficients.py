# %% imports 
import pandas as pd

# %% class names
class_1 = '5to18kW'
class_2 = '18to35kW'
class_3 = '35to80kW'

# %% read from xls
df_sheet_multi = pd.read_excel('heatpumpCoefficients.xls',
                               sheet_name=[class_1,
                                           class_2,
                                           class_3])

# %% store to hdf
name = 'HeatpumpCoefficients'

store = pd.HDFStore(name + '.h5')
store[class_1] = df_sheet_multi[class_1]
store[class_2] = df_sheet_multi[class_2]
store[class_3] = df_sheet_multi[class_3]

store.close()
