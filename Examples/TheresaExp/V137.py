""" Design of HiL experiments with THERESA """
# %% Imports
# Model
from Examples.TheresaExp.Basic.Model import getDefaultCellData


# %% prepare Simulation
start = '23.01.2020'
end = '24.01.2020'

nSteps, time, SLP, HWP, Weather, Solar, cell = getDefaultCellData(start, end)
