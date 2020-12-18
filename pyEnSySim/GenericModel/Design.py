""" A collection of functions to generate a generic model

    Statistics and boundary conditions used are documented in
    TODO: Source Final Report
"""
import numpy as np
import pandas as pd
from SystemComponentsFast import Agent, Building, Cell, SepBSLagent


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


def _addBuildings(cell, nBuilding, pBuilding, pDHN, Geo, U, n,
                  pAgent, pPHH, pAgriculture, pPV, hist=0):
    """ Add Buildings of one type to cell

    Args:
        cell (Cell): Cell where to add buildings
        nBuilding (uint32): Number of buildings to add
        pBuilding (dict): Probability dict of building for
                          age class, Modernisation state and
                          ventilation method
        pDHN (float32): Proportion of buildings connected
                        to the district heating network
        Geo (pd DataFrame): Geometry data of building type
        U (pd DataFrame): U-Values of building type
        n (pd DataFrame): Infiltration rates of building type
        pAgent (float32): Probability that agents is created
                          (Corresponds to the propotion of agents on
                           max. possible Agents in Building(s))
        pPHH (float32): Propotion of PHH agents in Building
        pAgriculture (float32): Propotion of BSL agents which are
                                agricultural
        pPV (float32): Proportion of buildings with PV plants
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
                                U.loc['UValues', (classNames[classIdx],
                                                  mState)]
                                ]).T

        # create building
        building = Building(Geo.loc['nUnits'].values.astype(np.uint32)[0][0],
                            a_uv_values,
                            U.loc['DeltaU', (classNames[classIdx], mState)],
                            n.loc['Infiltration', infState],
                            n.loc[airState, infState],
                            Geo.loc[('Volume')].values.astype(np.uint32)[0][0],
                            isAtDHN, cell.t_out_n, hist
                            )
        # Create and add agents
        _addAgents(building, pAgent, pPHH, pAgriculture)
        # add PV to buildings
        if np.random.random() <= pPV:
            building.add_dimensioned_pv(cell.eg, hist)
        # add building to cell
        cell.add_building(building)

    return cell


def addSepBSLAgents(cell, nAgents, pAgriculture, pPV, hist=0):
    """ Add separate BSL Agent to cell

    Args:
        cell (Cell): ell where to add Agent
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
    n = pd.read_hdf(bFile, key='n')

    return (Geo, U, n)


def generateGenericCell(nBuildings, pAgents, pPHHagents,
                        pAgriculture, pDHN, pPVplants, pBTypes,
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
    cell = Cell(climate.loc['Eg', 'standard data'],
                climate.loc['T', 'standard data'],
                hist)

    # init buildings and agents
    for key in pBTypes.keys():
        bType = pBTypes[key]['type']
        Geo, U, n = _loadBuildingData(bType)

        _checkParameter(U, pBTypes[key])

        _addBuildings(cell, nBuildings[bType], pBTypes[bType], pDHN[bType],
                      Geo, U, n,
                      pAgents[bType], pPHHagents[bType], pAgriculture[bType],
                      pPVplants, hist)

    # init sep BSL agents
    addSepBSLAgents(cell, nSepBSLAgents, pAgricultureBSLsep, pPVplants, hist)

    return cell
