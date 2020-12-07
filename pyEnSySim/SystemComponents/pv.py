from numba import types
from numba.experimental import jitclass

from numpy import random


spec = [('A', types.float32),  # Effective Area of PV plant
        ]


@jitclass(spec)
class PV():
    def __init__(self, Eg, COC, demand):
        """ Create PV object with specific Area
        Args:
            Eg (float): Mean annual global irradiation
                        for simulated region [kWh/m^2]
            COC (float): Sum of all agents Coefficient of Consumer
                         of building corresponding to this PV plant
            demand (float): Factor to describe the demand of agent(s)
                            to cover their electrical energy demand with PV
                            E.g demand = 1 means agent likes to cover his
                            demand completely

        """
        self.A = (random.random() * 0.4 + 0.8) * 1e3/Eg * COC * demand
