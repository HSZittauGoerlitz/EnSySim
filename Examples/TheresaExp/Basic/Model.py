""" Helper functions for pre-/postprocessing """
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import generateGenericCell
from GenericModel.PARAMETER import PBTYPES_NOW
from SystemComponentsFast import TheresaSystem

import pandas as pd


def addTheresaSystem(cell, nSteps):
    theresa = TheresaSystem(250., nSteps)

    cell.add_theresa(theresa)

    return cell


def getDefaultCellData(start, end):
    """ Return simulation data and default cell for HiL Simulation

    Arguments:
        start {str} -- Start Date of Simulation
        end {str} -- End Date of Simulation

    Returns:
        tuple -- nSteps, time, SLP, HWP, Weather, Solar, cell
    """
    region = 'East'
    # agents
    nSepBSLagents = 10
    pAgricultureBSLsep = 0.7
    nBuildings = {'FSH': 500, 'REH': 500, 'SAH': 400, 'BAH': 150}
    pAgents = {'FSH': 1., 'REH': 1., 'SAH': 0.9, 'BAH': 0.75}
    pPHHagents = {'FSH': 0.9, 'REH': 0.9, 'SAH': 0.8, 'BAH': 1.}
    pAgriculture = {'FSH': 0.0, 'REH': 0.0, 'SAH': 0.0, 'BAH': 0.0}

    pDHN = {'FSH': 0.0, 'REH': 0.0, 'SAH': 0.25, 'BAH': 1.}
    pPVplants = 0.2
    pHeatpumps = {'class_1': 0, 'class_2': 0,
                  'class_3': 0, 'class_4': 0.12,
                  'class_5': 0.27}
    pCHP = 0.02  # Fraction of electrical chp generation at demand

    nSteps, time, SLP, HWP, Weather, Solar = getSimData(start, end, region)

    cell = generateGenericCell(nBuildings, pAgents,
                               pPHHagents, pAgriculture,
                               pDHN, pPVplants, pHeatpumps, pCHP, PBTYPES_NOW,
                               nSepBSLagents, pAgricultureBSLsep,
                               region, nSteps)

    return nSteps, time, SLP, HWP, Weather, Solar, cell


def getSaveDataFrame():
    colIdx = [('Cell', ['Electrical Generation [MW]',
                        'Thermal Generation [MW]',
                        'Electrical Load [MW]', 'Thermal Load [MW]']),
              ('Environment', ['T [degC]', 'E diffuse [W/m^2]',
                               'E direct [W/m^2]', 'Solar elevation [deg]',
                               'Solar azimuth [deg]']),
              ('1B01 Measurements', ['Level [m]', 'Pressure [bar]',
                                     'Temperature [degC]', 'Enthalpy [kJ/kg]',
                                     'MassFlow_in [kg/h]', 'Pressure_in [bar]',
                                     'Temperature_in [degC]',
                                     'Enthalpy_in [kJ/kg]',
                                     'MassFlow_out [kg/h]',
                                     'Pressure_out [bar]',
                                     'Temperature_out [degC]',
                                     'Enthalpy_out [kJ/kg]',
                                     'Heater State [%]']),
              ('Storage State', ['Energy stored [MWh]', 'Charge [%]']),
              ('Storage Balance', ['Thermal Energy Requested [MWh]',
                                   'Thermal Energy Delivered [MWh]',
                                   'Model Power Equivalence [MW]',
                                   'Energy in [MWh]']),
              ('Storage Input: CHP', ['actuation [%]',
                                      'Thermal Power Output [MW]',
                                      'Thermal Energy Delivered [MWh]',
                                      'Model Power Equivalence [MW]']),
              ('Storage Input: Boiler', ['actuation [%]',
                                         'Thermal Power Output [MW]',
                                         'Thermal Energy Delivered [MWh]',
                                         'Model Power Equivalence [MW]'])
              ]
    colIdx = [(main, element) for main, elements in colIdx
              for element in elements]
    colIdx = pd.MultiIndex.from_tuples(colIdx)

    return pd.DataFrame(columns=colIdx, dtype='float64')


def saveParameter(saveLoc, cell, PLCparameter):
    nAgents = 0
    pPV = 0
    for building in cell.buildings:
        nAgents += building.n_agents
        if building.pv:
            pPV += 1

    pPV = pPV / cell.n_buildings * 100.

    CellParameter = {'Nummber of Buildings': cell.n_buildings,
                     'Number of Agents in Buildings': nAgents,
                     'Number of sep. Business Agents': cell.n_sep_bsl_agents,
                     'Number of Sub-Cells': cell.n_cells,
                     'Mean annual global irradiation [kWh/m^2]': cell.eg,
                     'Normed outside temperature [degC]': cell.t_out_n,
                     'Proportion of Buildings with PV [%]': pPV
                     }

    parameter = {'Cell': CellParameter,
                 'Scaled Thermal System THERESA': PLCparameter
                 }

    parameter = pd.DataFrame.from_dict(parameter,
                                       orient='index').stack().to_frame()

    parameter.to_csv(saveLoc + "parameter.csv", sep=';', header=False)


def saveStep(time, cellData, envData, Nodes, sDF):
    sDF.loc[time, ('Cell',
                   'Electrical Generation [MW]')] = cellData['E gen'] * 1e-6
    sDF.loc[time, ('Cell',
                   'Electrical Load [MW]')] = cellData['E load'] * 1e-6
    sDF.loc[time, ('Cell',
                   'Thermal Generation [MW]')] = cellData['T gen'] * 1e-6
    sDF.loc[time, ('Cell',
                   'Thermal Load [MW]')] = cellData['E load'] * 1e-6
    sDF.loc[time, ('Environment', 'T [degC]')] = envData['T [degC]']
    sDF.loc[time, ('Environment',
                   'E diffuse [W/m^2]')] = envData['E diffuse [W/m^2]']
    sDF.loc[time, ('Environment',
                   'E direct [W/m^2]')] = envData['E direct [W/m^2]']
    sDF.loc[time, ('Environment',
                   'Solar elevation [deg]')] = envData['Solar elevation [deg]']
    sDF.loc[time, ('Environment',
                   'Solar azimuth [deg]')] = envData['Solar azimuth [deg]']

    SG = Nodes['steamGen'].get_value()
    sDF.loc[time, ('1B01 Measurements',
                   'Level [m]')] = SG.Level
    sDF.loc[time, ('1B01 Measurements',
                   'Pressure [bar]')] = SG.Pressure
    sDF.loc[time, ('1B01 Measurements',
                   'Temperature [degC]')] = SG.Temperature
    sDF.loc[time, ('1B01 Measurements',
                   'Enthalpy [kJ/kg]')] = Nodes['h'].get_value()
    sDF.loc[time, ('1B01 Measurements',
                   'MassFlow_in [kg/h]')] = SG.MassFlow_in
    sDF.loc[time, ('1B01 Measurements',
                   'Pressure_in [bar]')] = SG.Pressure_in
    sDF.loc[time, ('1B01 Measurements',
                   'Temperature_in [degC]')] = SG.Temperature_in
    sDF.loc[time, ('1B01 Measurements',
                   'Enthalpy_in [kJ/kg]')] = Nodes['hIn'].get_value()
    sDF.loc[time, ('1B01 Measurements',
                   'MassFlow_out [kg/h]')] = SG.MassFlow_out
    sDF.loc[time, ('1B01 Measurements',
                   'Pressure_out [bar]')] = SG.Pressure_out
    sDF.loc[time, ('1B01 Measurements',
                   'Temperature_out [degC]')] = SG.Temperature_out
    sDF.loc[time, ('1B01 Measurements',
                   'Enthalpy_out [kJ/kg]')] = Nodes['hOut'].get_value()
    sDF.loc[time, ('1B01 Measurements',
                   'Heater State [%]')] = SG.heater_proc

    CHP = Nodes['CHP'].get_value()
    sDF.loc[time, ('Storage Input: CHP',
                   'actuation [%]')] = CHP.actuation * 100.
    sDF.loc[time, ('Storage Input: CHP',
                   'Thermal Power Output [MW]')] = CHP.power
    sDF.loc[time, ('Storage Input: CHP',
                   'Thermal Energy Delivered [MWh]')] = CHP.E_Delivered
    sDF.loc[time, ('Storage Input: CHP',
                   'Model Power Equivalence [MW]')] = CHP.P_Model

    Boiler = Nodes['Boiler'].get_value()
    sDF.loc[time, ('Storage Input: Boiler',
                   'actuation [%]')] = Boiler.actuation * 100.
    sDF.loc[time, ('Storage Input: Boiler',
                   'Thermal Power Output [MW]')] = Boiler.power
    sDF.loc[time, ('Storage Input: Boiler',
                   'Thermal Energy Delivered [MWh]')] = Boiler.E_Delivered
    sDF.loc[time, ('Storage Input: Boiler',
                   'Model Power Equivalence [MW]')] = Boiler.P_Model

    Storage = Nodes['steamGenModel'].get_value()
    sDF.loc[time, ('Storage State',
                   'Energy stored [MWh]')] = Storage.stored
    sDF.loc[time, ('Storage State',
                   'Charge [%]')] = Storage.charge
    sDF.loc[time, ('Storage balance',
                   'Thermal Energy Requested [MWh]')] = Storage.E_requested
    sDF.loc[time, ('Storage balance',
                   'Thermal Energy Delivered [MWh]')] = Storage.E_delivered
    sDF.loc[time, ('Storage balance',
                   'Model Power Equivalence [MW]')] = Storage.P_equivalence
    sDF.loc[time, ('Storage balance',
                   'Energy in [MWh]')] = Storage.E_in

    return sDF
