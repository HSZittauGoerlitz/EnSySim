# %% Imports
# Model
import Examples.TheresaExp.Basic.Communication as c
from Examples.TheresaExp.Basic.Model import getDefaultCellData


# %% prepare Simulation
start = '23.01.2020'
end = '24.01.2020'

nSteps, time, SLP, HWP, Weather, Solar, cell = getDefaultCellData(start, end)

# %% connect to GateWay
pw = input("Enter OPC UA Server Password: ")
client = c.createClient(pw)
c.initClient(client)
devSetNode = c.getDeviceSetNode(client)
# Node of Prg where Measurement values are read in
theresaNode = c.getPrgNode(devSetNode, "THERESAtoOPC")
# Node of Interface Prg between THERESA and Simulatin
ifNode = c.getPrgNode(devSetNode, "StateSteamGenerator")
# Measurement values
SG = c.getSubNode(theresaNode, "SG")
