# %% Imports
# Model
import Examples.TheresaExp.Basic.Communication as c
from Examples.TheresaExp.Basic.Model import getDefaultCellData
from time import sleep

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
# Node of Interface Prg between THERESA and Simulation
ifNode = c.getPrgNode(devSetNode, "StateSteamGenerator")
# Node for Simulation Communication Prg
simAlive = c.getPrgNode(devSetNode, "SimAlive")
simCtrl = c.getPrgNode(devSetNode, "SimCtrl")
aliveNode = c.getSubNode(simAlive, "alive")
endNode = c.getSubNode(simCtrl, "endSim")
endToggleNode = c.getSubNode(simCtrl, "endSimToggle")
stepModel = c.getSubNode(simCtrl, "stepModel")
# Measurement values
SG = c.getSubNode(theresaNode, "SG")

# %% Start Simulation Loop (Maintained by SPS)
try:
    run = c.maintainConnection(aliveNode, endNode, endToggleNode)
    while run:
        # reduce load
        sleep(0.1)  # 100ms
        run = c.maintainConnection(aliveNode, endNode, endToggleNode)
        if c.checkModelStep(stepModel):
            continue
finally:
    client.disconnect()
