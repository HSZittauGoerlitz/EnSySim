from numba.core import types
from numba.typed import Dict


def simulate(mainCell, steps, SLP_PHH, SLP_BSLa, SLP_BSLc,
             HotWaterData, T, Eg):
    """ Run Simulation with given models main cell

    Args:
        mainCell (Cell): Main cell of energy system model
        steps (int): Number of simulation steps to execute
        SLP_PHH (np float array): Standard load profile data for
                                  phh agents
        SLP_BSLa (np float array): Standard load profile data for
                                  agriculture business agents
        SLP_BSLc (np float array): Standard load profile data for
                                  common business agents
        HotWaterData (np float array): Hot water profile data
        T (np float array): Temperature curve
        Eg (np float array): Global irradiation curve
    """
    # prepare dict of SLP data for agents
    SLP = Dict.empty(key_type=types.unicode_type,
                     value_type=types.float32,)
    SLP['PHH'] = 0.
    SLP['BSLa'] = 0.
    SLP['BSLc'] = 0.

    for step in range(steps):
        # add current SLP data
        SLP['PHH'] = SLP_PHH[step]
        SLP['BSLa'] = SLP_BSLa[step]
        SLP['BSLc'] = SLP_BSLc[step]

        mainCell._step(SLP, HotWaterData[step], T[step], Eg[step])
