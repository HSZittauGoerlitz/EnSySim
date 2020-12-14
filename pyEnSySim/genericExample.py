#%% doing imports
import pandas as pd

from GenericModel.Design import generateGenericCell
from Simulation.executeModel import simulate

import SystemComponents
import BoundaryConditions

#%% defining parameters
nBuildings = {'FSH':100, 'REH':100, 'SAH':1000,'BAH':100}
nAgents = {'FSH':1, 'REH':1, 'SAH':1,'BAH':1}
pPHHagents = {'FSH':1, 'REH':1, 'SAH':1,'BAH':1}
pAgriculture = {'FSH':0, 'REH':0, 'SAH':0,'BAH':0}
pDHN = {'FSH':0, 'REH':0, 'SAH':0,'BAH':0}

#%% building generic model
exec(open('.\GenericModel\PARAMETER.py').read())
cell = generateGenericCell(nBuildings, nAgents, pPHHagents, pAgriculture, pDHN, 0.4, PBTYPES_NOW, 'East')

#%% loading time series data
SLPPHH = pd.read_hdf('.\BoundaryConditions\Electrical\SLP\PHH.h5')
print(SLPPHH.head())

# %% running simulation
simulate(cell, 100, )