""" A collection of functions to generate a generic model

    Statistics and boundary conditions used are documented in
    TODO: Source Final Report
"""
import numpy as np
import pandas as pd
import logging as lg
from SystemComponentsFast import Agent, Building, Cell, SepBSLagent

lg.basicConfig(level=lg.DEBUG)


def _addAgents(building, pAgent, pPHH, pAgriculture):
    """ Add agents to building

    Args:
        building (Building): Object to represent building
        pAgent (float32): Probability that agents is created
                          (Corresponds to the propotion of agents on
                           max. possible Agents in Building(s))
        pPHH (float32): Proportion of PHH agents in Building
        pAgriculture (float32): Proportion of BSL agents which are
                                agricultural

    Returns:
        Building: Building object with agents
    """
    for aNr in range(building.n_max_agents):
        if np.random.random() > pAgent:
            continue

        # determine agent type
        if np.random.random() <= pPHH:
            aType = 0
        else:
            if np.random.random() <= pAgriculture:
                aType = 1
            else:
                aType = 2

        agent = Agent(aType)
        building.add_agent(agent)

    return building


def _addBuildings(cell, nBuilding, pBuilding, pDHN, region, Geo, U, g, n,
                  pAgent, pPHH, pAgriculture, pPV, pHP, hist=0):
    """ Add Buildings of one type to cell

    Args:
        cell (Cell): Cell where to add buildings
        nBuilding (uint32): Number of buildings to add
        pBuilding (dict): Probability dict of building for
                          age class, Modernisation state and
                          ventilation method
        pDHN (float32): Proportion of buildings connected
                        to the district heating network
        region (string): Region location of cell (determines climate / weather)
                         Supported regions:
                            East, West, South, North
        Geo (pd DataFrame): Geometry data of building type
        U (pd DataFrame): U-Values of building type
        g (pd DataFrame): Solar factors for building type
        n (pd DataFrame): Infiltration rates of building type
        pAgent (float32): Probability that agents is created
                          (Corresponds to the propotion of agents on
                           max. possible Agents in Building(s))
        pPHH (float32): Propotion of PHH agents in Building
        pAgriculture (float32): Propotion of BSL agents which are
                                agricultural
        pPV (float32): Proportion of buildings with PV plants
        pHP (dict): Mapping of proportion factor for heatpumps
                                   in each building class (0 to 1)
        hist (int): Size of history for power balance of buildings, pv etc.
    """
    pClass = np.array(pBuilding['Class'])
    pModern = np.array(pBuilding['Modern'])
    pAirMech = np.array(pBuilding['AirMech'])

    # generate names for all age classes of specific building type
    classNames = ['class_' + str(Nr+1) for Nr in range(pClass.size)]
    # get cumulative probabilities for vectorized class mapping
    pClass = pClass.cumsum()

    for Nr in range(nBuilding):
        p = np.random.random()
        # get building age class
        classIdx = (p <= pClass).argmax()
        # get modernisation state
        if np.random.random() <= pModern[classIdx]:
            mState = 'modernised'
        else:
            mState = 'original'
        # get ventilation state
        if np.random.random() <= pAirMech[classIdx]:
            airState = 'VentilationMech'
        else:
            airState = 'VentilationFree'
        # for Air infiltration/ventilation consider new buildings
        if classNames[classIdx] == 'class_5':
            infState = 'new'
        else:
            infState = mState

        isAtDHN = np.random.random() <= pDHN

        # create a_uv_array
        a_uv_values = np.array([Geo.loc['Areas'].values.T[0],
                                U.loc[('UValues', Geo.loc['Areas'].index),
                                      (classNames[classIdx], mState)].values.T
                                ]).T

        # create building
        # effective heat capacity with fixed C_eff of 15. (Wh)/(m^3K)
        building = Building(Geo.loc['nUnits'].values.astype(np.uint32)[0][0],
                            a_uv_values,
                            U.loc[('DeltaU', ''),
                                  (classNames[classIdx], mState)],
                            n.loc['Infiltration', infState],
                            n.loc[airState, infState],
                            (Geo.loc['cp_effective'] *
                             Geo.loc['Volume']).Value,
                            g.loc[mState, classNames[classIdx]],
                            Geo.loc[('Volume')].values.astype(np.uint32)[0][0],
                            isAtDHN, cell.t_out_n, hist
                            )
        # Create and add agents
        _addAgents(building, pAgent, pPHH, pAgriculture)
        # add PV to buildings
        if np.random.random() <= pPV:
            building.add_dimensioned_pv(cell.eg, hist)
        # add heatpump to building
        t_ref = pd.read_hdf('BoundaryConditions/Weather/{}.h5'.format(region),
                            key='Weather').reference['T [degC]'].tolist()

        if pHP[classNames[classIdx]] > np.random.random():
            # choose supply temperature
            classTemperatures = {"class_1": 55,
                                 "class_2": 55,
                                 "class_3": 55,
                                 "class_4": 45,
                                 "class_5": 35}
            t_supply = classTemperatures[classNames[classIdx]]
            seas_perf_fac = 3.

            if building.q_hln < 5000 or building.q_hln > 80000:
                lg.warning("for this building no heatpump data is available, "
                           "maximum heat load is {:.2f}W"
                           .format(building.q_hln))
            # differentiate by installed power
            else:
                building.add_dimensioned_heatpump(seas_perf_fac,
                                                  t_supply,
                                                  t_ref,
                                                  hist)
                lg.debug("installed {:.2f}W thermal heatpump generation"
                         .format(building.q_hln))

        # add building to cell
        cell.add_building(building)

    return cell


def addCHPtoCellBuildings(cell, pCHP, hist=0):
    """Add CHP to buildings

    Args:
        cell (Cell): cell where CHPs shall be added
        pCHP (float32): percentage of electricity production delivered by CHP
        hist (int): Size of history for power balance/energy level of chp,
                    storage etc. (Default: 0)
    """
    # default thermal-to-electrical factor
    th_el = 2.
    # default full run time in h
    full = 5000.
    # best ratio power_th to q_hln (maximum or 'norm' heat load)
    relPow = 0.4
    # upper and lower limit for ratio power_th to q_hln
    upLim = 0.25
    lowLim = 0.45

    # this is maybe not the fastest way to do this, could be moved to rust
    # get electricity consumption of cell
    buildings_q_hln = []
    COC = 0
    for building in cell.buildings:
        for agent in building.agents:
            COC += agent.coc
        buildings_q_hln.append(building.q_hln)

    # installed power gets scaled by hours/year
    instPower_el = 1000000. * COC * pCHP / full

    # generate CHP powers from ...
    # ... distribution:
    mu = -4.894316543131761
    sigma = 1.281345974473205
    _sum = 0
    # ... and make sure to match cell demand
    powers_el = []
    while _sum < instPower_el:
        powers_el.append(np.random.lognormal(mu, sigma)*1000000.)  # MW to W
        if powers_el[-1] < 3000 or powers_el[-1] > 6000:
            powers_el.pop()
            continue
        _sum += powers_el[-1]
    # convert to thermal power by thermal-to-electrical factor
    powers_th = [power*th_el for power in powers_el]

    # find first building with matching heat need
    instPower_th = 0
    for power in powers_th:
        idx, q_hln = min(enumerate(buildings_q_hln),
                         key=lambda x: abs(x[1]*relPow-power))

        # add chp to building if difference is below threshold
        if upLim < power/q_hln < lowLim:
            # get building
            building = cell.buildings[idx]
            # add chp
            building.add_dimensioned_chp(hist)
            # write back to buildings vec
            cell.update_building(idx, building)
            # keep track of already installed power
            instPower_th += power
            # ToDo: What if building already has e.g. heat pump?
            lg.debug("for chp with thermal power {:.2f}W building with {:.2f}W"
                     " heat load was found ({:.2f})".format(power,
                                                            q_hln,
                                                            power/q_hln))
            # prevent doubling
            buildings_q_hln[idx] = 0
        else:
            lg.warning("for chp with thermal power {:.2f}W closest "
                       "building had {:.2f}W maximum heat load."
                       "chp was dismissed, because pCHP for building "
                       "would be {:.2f}!!!"
                       .format(power, q_hln, power/q_hln))
    lg.debug("installed {:.2f}kW thermal chp generation"
             .format(instPower_th/1000))
    lg.debug("corresponds to {:.2f}kW electrical generation"
             .format(instPower_th/1000/2))
    lg.debug("electrical demand is {:.2f}kWh"
             .format(COC*1000))
    lg.debug("5000h full load generate {:.2f}% of electrical supply"
             .format(instPower_th/2*5000/(COC*1000000)))


def addSepBSLAgents(cell, nAgents, pAgriculture, pPV, hist=0):
    """ Add separate BSL Agent to cell

    Args:
        cell (Cell): cell where to add Agent
        nAgents (uint32): Number of agents to add
        pAgriculture (float32): Propotion of BSL agents which are
                                agricultural
        pPV (float32): Proportion of bsl agents with PV plants
        hist (int): Size of history for power balance of bsl agents, pv etc.
                    (Default: 0)
    """
    for Nr in range(nAgents):
        # get agent type
        if np.random.random() < pAgriculture:
            aType = 1
        else:
            aType = 2

        agent = SepBSLagent(aType, hist)

        if np.random.random() <= pPV:
            agent.add_dimensioned_pv(cell.eg, hist)

        cell.add_sep_bsl_agent(agent)


def _check_pBTypes(pBTypes):
    for key in pBTypes.keys():
        pBClass = pBTypes[key]['Class']
        pBModern = pBTypes[key]['Modern']
        pBAirMech = pBTypes[key]['AirMech']

        nClass = len(pBClass)
        if nClass <= 0:
            raise ValueError("The building class proportions must "
                             "have min. 1 value")

        if (min(pBClass) < 0) | (max(pBClass) > 1):
            raise ValueError("Each building class proportion must "
                             "be in range from 0 to 1")

        if (sum(pBClass) < 0.995) | (sum(pBClass) > 1.005):
            # allow slight deviation
            raise ValueError("The sum of building class proportions must be 1")

        if len(pBModern) != nClass:
            raise ValueError("The building modernisation proportions must "
                             "fit to number of class proportions")

        if (min(pBModern) < 0) | (max(pBModern) > 1):
            raise ValueError("Each building modernisation proportion must "
                             "be in range from 0 to 1")

        if len(pBAirMech) != nClass:
            raise ValueError("The building air renewing proportions must "
                             "fit to number of class proportions")

        if (min(pBAirMech) < 0) | (max(pBAirMech) > 1):
            raise ValueError("Each building air renewal proportion must "
                             "be in range from 0 to 1")


def _checkParameter(UValues, parameterSet):
    """ Compare U-Value Dataframe of building data set
        with given parameters.

    Args:
        UValues (pd DataFrame): Building U-Values data set
        parameterSet ([type]): Probabilities for building
                               age class, Modernisation state and
                               ventilation method
    """
    nClasses = UValues.columns.levels[0].size
    error = False
    failedParameter = ""

    if nClasses != len(parameterSet['Class']):
        error = True
        failedParameter += "Class"

    if nClasses != len(parameterSet['Modern']):
        if error:
            failedParameter += ", "
        else:
            error = True
        failedParameter += "Modernisation"

    if nClasses != len(parameterSet['AirMech']):
        if error:
            failedParameter += ", "
        else:
            error = True
        failedParameter += "Ventilation"

    if error:
        raise ValueError("The number of given {} probabilities for "
                         "building type {} does not fit to the number of "
                         "classes in the U-Values data set"
                         .format(failedParameter, parameterSet['type']))


def _loadBuildingData(bType):
    bFile = './BoundaryConditions/Thermal/ReferenceBuildings/' + bType + '.h5'
    Geo = pd.read_hdf(bFile, key='Geo')
    U = pd.read_hdf(bFile, key='U')
    g = pd.read_hdf(bFile, key='g')
    n = pd.read_hdf(bFile, key='n')

    return (Geo, U, g, n)


def generateGenericCell(nBuildings, pAgents, pPHHagents,
                        pAgriculture, pDHN, pPVplants,
                        pHeatpumps, pCHP, pBTypes,
                        nSepBSLAgents, pAgricultureBSLsep,
                        region, hist=0):
    """ Create a cell of a generic energy system

    The default cell consists of 4 ref. building types:
      - free standong house (FSH)
      - row end house (REH)
      - small apartment house (SAH)
      - big apartment house (BAH)
    Additionally there are independent BSL agents
    with inherent buildings (the thermal load is neglected for
    those)[TODO].
    The cell composition for agents / buildings can be
    adjusted by the proportions accordingly.
    For BSL agents located in buildings a phh like thermal
    profile is assumed.

    Available Age classes:
      - Class 1: Before 1948
      - Class 2: 1948 - 1978
      - Class 3: 1979 - 1994
      - Class 4: 1995 - 2009
      - Class 5: new building

    Args:
        nBuildings (dict): Mapping of Number of buildings to building type
                           ({string: uint32})
        pAgents (dict):  Mapping of probability for Agents to be generated in
                         corresponding Buildings.
                         This allows to simulate vacancy.
                         (0 to 1 each) ({string: float32})
        pPHHagents (dict): Mapping of proportion factor for PHH agents
                           in each building type (0 to 1 each)
                           ({string: float32})
        pAgriculture (dict): Factor for propotion of agriculture agents on
                             BSL agents in each building type (0 to 1)
                             ({string: float32})
        pDHN (dict): Mapping of proportions for buildings of corresponding type
                     with connection to the district heating network
                     (0 to 1 each) ({string: float32})
        pPVplants (float32): Proportion of buildings with PV-Plants (0 to 1)
        pHeatpumps (dict): Mapping of proportion factor for heatpumps
                                   in each building class (0 to 1)
        pCHP (float32): Proportion of electricity produced by chp (0 to 1)
        pBTypes (dict): Dictionary of proportions for all reference building
                        types (0 to 1 each, Types: FSH, REH, SAH, BAH)
                          . Class for age classes
                          . Modern for proportion of modernised buildings
                          . AirMech for proportion of buildings with
                            enforced air renewal
                          . type for the name of the building type
                            (must be equal to the reference building data file)
        nSepBSLAgents (uint32): Number of agents to add
        pAgricultureBSLsep (float32): Factor for propotion of agriculture on
                                      separate BSL agents (0 to 1)
        region (string): Region location of cell (determines climate / weather)
                         Supported regions:
                            East, West, South, North
        hist (int): Size of history for power balance of cells, buildings etc.

    Returns:
        Cell: Generic energy system cell
    """
    # check input parameter
    if min(nBuildings.values()) < 0:
        raise ValueError("Number of buildings must be 0 or higher")

    if (min(pAgents.values()) < 0) | (max(pAgents.values()) > 1):
        raise ValueError("Agent probability must be between 0 and 1")

    if (min(pPHHagents.values()) < 0) | (max(pPHHagents.values()) > 1):
        raise ValueError("PHH probabilities must be between 0 and 1")

    if ((min(pAgriculture.values()) < 0) | (max(pAgriculture.values()) > 1) |
       (pAgricultureBSLsep < 0) | (pAgricultureBSLsep > 1)):
        raise ValueError("Agriculture probabilities must be between 0 and 1")

    if (min(pDHN.values()) < 0) | (max(pDHN.values()) > 1):
        raise ValueError("DHN probabilities must be between 0 and 1")

    if (pPVplants < 0) | (pPVplants > 1):
        raise ValueError("PV probability must be between 0 and 1")

    _check_pBTypes(pBTypes)

    if nSepBSLAgents < 0:
        raise ValueError("Number of separate BSL agents must be 0 or higher")

    supportedRegions = ["East", "West", "South", "North"]
    if region not in supportedRegions:
        raise ValueError("Unknown region, supported regions are {}"
                         .format(supportedRegions))

    # load region climate data (standard temperature and irradiation)
    climate = pd.read_hdf("./BoundaryConditions/Weather/" + region + ".h5",
                          'Standard')

    # init cell
    cell = Cell(climate.loc['EgNorm kWh', 'Value'],
                climate.loc['ToutNorm degC', 'Value'],
                hist)

    # init buildings and agents
    for key in pBTypes.keys():
        bType = pBTypes[key]['type']
        Geo, U, g, n = _loadBuildingData(bType)

        _checkParameter(U, pBTypes[key])

        _addBuildings(cell, nBuildings[bType], pBTypes[bType], pDHN[bType],
                      region, Geo, U, g, n,
                      pAgents[bType], pPHHagents[bType], pAgriculture[bType],
                      pPVplants, pHeatpumps, hist)

    # init sep BSL agents
    addSepBSLAgents(cell, nSepBSLAgents, pAgricultureBSLsep, pPVplants, hist)

    addCHPtoCellBuildings(cell, pCHP)

    return cell
