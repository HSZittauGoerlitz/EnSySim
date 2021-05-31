# %% Imports
# Model
import Examples.TheresaExp.Basic.Communication as c
import Examples.TheresaExp.Basic.Model as m
from opcua import ua
from time import sleep

# %% prepare Simulation
saveLoc = "D:/V137/"

start = '23.01.2020'
end = '24.01.2020'

nSteps, time, slp, hwp, Weather, Solar, cell = m.getDefaultCellData(start, end)

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
# Measurement / Interface values
MNodes = {'steamGen': c.getSubNode(theresaNode, "SG"),
          'steamGenModel': c.getSubNode(ifNode, 'SGmodel'),
          'Boiler': c.getSubNode(ifNode, 'Boiler'),
          'CHP': c.getSubNode(ifNode, 'CHP'),
          'h': c.getSubNode(ifNode, 'hSG'),
          'hIn': c.getSubNode(ifNode, 'hIn'),
          'hOut': c.getSubNode(ifNode, 'hOut')
          }

# Send Connection
cellState = c.getSubNode(simCtrl, "cellState")
cellStateDataValue = cellState.get_data_value()
# prepare writing (wago doesn't support timestamps)
cellWriteValue = ua.DataValue(ua.Variant(cellStateDataValue.Value,
                              ua.VariantType.ExtensionObject))
cellWriteValue.ServerTimestamp = None
cellWriteValue.SourceTimestamp = None

# %% save parameter
PLCparameter = c.getPLC_Parameter(ifNode)
m.saveParameter(saveLoc, cell, PLCparameter)

# Simulation data
saveData = m.getSaveDataFrame()

# %% Start Simulation Loop (Maintained by SPS)
cellData = {'E gen': 0., 'E load': 0., 'T gen': 0., 'T load': 0.}
envData = {'T [degC]': 0., 'E diffuse [W/m^2]': 0., 'E direct [W/m^2]': 0.,
           'Solar elevation [deg]': 0., 'Solar azimuth [deg]': 0.}
# count steps, to assign input values
stepIdx = 0
try:
    run = c.maintainConnection(aliveNode, endNode, endToggleNode)
    while run:
        # reduce load
        sleep(0.1)  # 100ms
        run = c.maintainConnection(aliveNode, endNode, endToggleNode)
        if c.checkModelStep(stepModel):
            if stepIdx > 0:
                saveData = m.saveStep(time[stepIdx-1], cellData, envData,
                                      MNodes, saveData)

            # get actual input data
            slp_in = slp.loc[stepIdx].to_dict()
            env_in = Weather.loc[stepIdx].to_dict()
            sol_in = Solar.loc[stepIdx].to_dict()
            # run cell
            gen_e, load_e, gen_t, load_t = cell.py_step(0., 0., slp_in,
                                                        hwp[stepIdx],
                                                        env_in, sol_in)
            # send Results to GateWay (in MW)
            cellWriteValue.Value.Value.electrical_generation = gen_e * 1e-6
            cellWriteValue.Value.Value.electrical_load = load_e * 1e-6
            cellWriteValue.Value.Value.thermal_generation = gen_t * 1e-6
            cellWriteValue.Value.Value.thermal_load = load_t * 1e-6
            cellState.set_value(cellWriteValue)

            # prepare next step
            cellData['E gen'] = gen_e
            cellData['E load'] = load_e
            cellData['T gen'] = gen_t
            cellData['T load'] = load_t
            envData['T [degC]'] = env_in['T [degC]']
            envData['E diffuse [W/m^2]'] = env_in['E diffuse [W/m^2]']
            envData['E direct [W/m^2]'] = env_in['E direct [W/m^2]']
            envData['Solar elevation [deg]'] = sol_in['elevation [degree]']
            envData['Solar azimuth [deg]'] = sol_in['azimuth [degree]']
            stepIdx += 1

            # send acknowledge of model step to PLC
            sleep(0.05)  # 50ms
            c.ackModelStep(stepModel)

            if stepIdx >= nSteps:
                break

finally:
    saveData.to_hdf(saveLoc + "ExperimentData.h5", 'data')
    client.disconnect()

# %%
