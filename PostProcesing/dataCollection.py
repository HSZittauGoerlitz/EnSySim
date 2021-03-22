import logging as lg
import numpy as np

lg.basicConfig(level=lg.WARNING)


def getCellsPVgeneration(cell):
    """ Calculate the complete electrical power generated by a cells PV plants
        (Cell + Buildings) over a complete simulation run, for each time step.

    If the hist-Size of pv plants differ, the data must be handled with caution

    Args:
        cell {Cell} -- Cell for which the pv power is calculated

    Returns:
        np array -- Curve of cells PV power [W]
    """
    PV = None

    if cell.pv is not None:
        if cell.pv.gen_e is None:
            lg.warning("The pv plant of cell has no history record")
        else:
            PV = np.array(cell.pv.gen_e.get_memory())

    for bNr, building in enumerate(cell.buildings):
        if building.pv is not None:
            if building.pv.gen_e is None:
                lg.warning("The pv plant of building {} "
                           "has no history record".format(bNr))
            else:
                if PV is None:
                    PV = np.array(building.pv.gen_e.get_memory())
                else:
                    bPV = np.array(building.pv.gen_e.get_memory())
                    if PV.size != bPV.size:
                        lg.warning("Record size for pv plant of building {} "
                                   "is different from other sizes, "
                                   "data is ignored".format(bNr))
                    else:
                        PV += bPV

    return PV


def getCellsHPgeneration(cell):
    """ Calculate the complete thermal power generated by a cells heatpumps
    (Buildings) over a complete simulation run, for each time step.

    If the hist-Size of heatpump differ, the data must be handled with caution

    Args:
        cell {Cell} -- Cell for which the heatpump power is calculated

    Returns:
        np array -- Curve of cells heatpump power [W]
    """
    HP = None

    for bNr, building in enumerate(cell.buildings):
        if building.heatpump is not None:
            if building.heatpump.heatpump.gen_t is None:
                lg.warning("The heatpump of building {} "
                           "has no history record".format(bNr))
            else:
                if HP is None:
                    HP = np.array(building.heatpump.heatpump.gen_t.get_memory())
                else:
                    bHP = np.array(building.heatpump.heatpump.gen_t.get_memory())
                    if HP.size != bHP.size:
                        lg.warning("Record size for heatpump of building {} "
                                   "is different from other sizes, "
                                   "data is ignored".format(bNr))
                    else:
                        HP += bHP

    return HP


def getCellsHPconsumption(cell):
    """ Calculate the complete electrical power consumed by a cells heatpumps
    (Buildings) over a complete simulation run, for each time step.

    If the hist-Size of heatpump differ, the data must be handled with caution

    Args:
        cell {Cell} -- Cell for which the heatpump power is calculated

    Returns:
        np array -- Curve of cells heatpump power [W]
    """
    HP = None

    for bNr, building in enumerate(cell.buildings):
        if building.heatpump is not None:
            if building.heatpump.heatpump.con_e is None:
                lg.warning("The heatpump of building {} "
                           "has no history record".format(bNr))
            else:
                if HP is None:
                    HP = np.array(building.heatpump.heatpump.con_e.get_memory())
                else:
                    bHP = np.array(building.heatpump.heatpump.con_e.get_memory())
                    if HP.size != bHP.size:
                        lg.warning("Record size for heatpump of building {} "
                                   "is different from other sizes, "
                                   "data is ignored".format(bNr))
                    else:
                        HP += bHP

    return HP


def getBuildingsThermalBalance(cell, subCells=True):
    """ Get thermal load and generation of each building in given cell.

    Arguments:
        cell {Cell} -- Cell for which the pv power is calculated

    Keyword Arguments:
        subCells {bool} -- When True also buildings of sub cells are
                           considered.(default: {True})

    Returns:
        (np array, np array) -- Curve of cells PV power [W]
    """
    gen = None
    load = None

    # at first collect sub cell balances
    if subCells:
        for scNr, sc in enumerate(cell.sub_cells):
            new_gen, new_load = getBuildingsThermalBalance(sc, subCells)
            # it's enough to check one array for existence
            if new_gen is None:
                lg.warning("No records found in sub cell {}".format(scNr))
                continue

            if gen is not None:
                gen += np.array(new_gen)
                load += np.array(new_load)
            else:
                if gen.size == len(new_gen):
                    gen = np.array(new_gen)
                    load = np.array(new_load)
                else:
                    lg.warning("Record size of sub cell {} "
                               "is different from other sizes, "
                               "data is ignored".format(scNr))

    for bNr, building in enumerate(cell.buildings):
        if building.gen_t is None:
            lg.warning("Building {} has no history record.".format(bNr))
            continue

        if gen is not None:
            new_gen = np.array(building.gen_t.get_memory())
            if gen.size == new_gen.size:
                gen += new_gen
                load += np.array(building.load_t.get_memory())
            else:
                lg.warning("Record size of building {} "
                           "is different from other sizes, "
                           "data is ignored".format(bNr))
        else:
            gen = np.array(building.gen_t.get_memory())
            load = np.array(building.load_t.get_memory())

    return (gen, load)