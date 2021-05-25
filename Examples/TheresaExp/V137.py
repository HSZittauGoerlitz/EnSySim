# %% Imports
# Model
import Examples.TheresaExp.Basic.Communication as c
from Examples.TheresaExp.Basic.Model import getDefaultCellData
from time import sleep

# %% prepare Simulation
start = '23.01.2020'
end = '24.01.2020'

nSteps, time, slp, hwp, Weather, Solar, cell = getDefaultCellData(start, end)

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
steamGen = c.getSubNode(theresaNode, "SG")
cellState = c.getSubNode(simCtrl, "cellState")
cellStateValue = cellState.get_data_value()
cellStateValue.SourceTimestamp = None
cellStateValue.ServerTimestamp = None

# %% Start Simulation Loop (Maintained by SPS)
# count steps, to assign input values
stepIdx = 0
try:
    run = c.maintainConnection(aliveNode, endNode, endToggleNode)
    while run:
        # reduce load
        sleep(0.1)  # 100ms
        run = c.maintainConnection(aliveNode, endNode, endToggleNode)
        if c.checkModelStep(stepModel):
            # get actual input data
            slp_in = slp.loc[stepIdx].to_dict()
            env_in = Weather.loc[stepIdx].to_dict()
            sol_in = Solar.loc[stepIdx].to_dict()
            # run cell
            gen_e, load_e, gen_t, load_t = cell.py_step(0., 0., slp_in, hwp[0],
                                                        env_in, sol_in)
            # send Results to GateWay (in MW)
            cellStateValue.Value.Value.electrical_generation = gen_e * 1e-6
            cellStateValue.Value.Value.electrical_load = load_e * 1e-6
            cellStateValue.Value.Value.thermal_generation = gen_t * 1e-6
            cellStateValue.Value.Value.thermal_load = load_t * 1e-6
            cellState.set_value(cellStateValue)
            # prepare next step
            stepIdx += 1
finally:
    client.disconnect()
