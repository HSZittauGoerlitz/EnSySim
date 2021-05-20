""" Helper functions for pre-/postprocessing """
from BoundaryConditions.Simulation.SimulationData import getSimData
from GenericModel.Design import generateGenericCell
from GenericModel.PARAMETER import PBTYPES_NOW
from SystemComponentsFast import TheresaSystem


def addTheresaSystem(cell, nSteps):
    theresa = TheresaSystem(250., 500., nSteps)

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
