from SystemComponents.agent import Agent
from SystemComponents.pv import PV

from numba import types, typed
from numba.experimental import jitclass
from numba.extending import overload_method


spec = [('agents', types.ListType(Agent.class_type.instance_type)),
        ('PV', PV.class_type.instance_type),
        ('nMaxAgents', types.int32),
        ]


@jitclass(spec)
class Building():
    def __init__(self, nMaxAgents, Eg, ToutN):
        """ Create building to simulate buildings energy demand as well

        Args:
            nMaxAgents (int): Number of max. possible agents
                              living in this building
            Eg (float): Mean annual global irradiation of parent Cell [kWh/m^2]
            ToutN (float): Normed outside temperature of parent Cell [°C]
        """
        self._createAgents(nMaxAgents)
        self._createPV(Eg)

    def _createAgents(self, nMaxAgents):
        if nMaxAgents <= 0:
            raise ValueError("Number of max. Agents must be greater than 0")

        self.nMaxAgents = nMaxAgents
        agents = []

        for idx in range(nMaxAgents):
            agents.append(Agent('PHH'))

        self.agents = typed.List(agents)

    def _createPV(self, Eg):
        """ Create PV object for building """
        sumCOC = 0
        sumAPVdemand = 0
        nAgents = 0
        for agent in self.agents:
            sumCOC += agent.COC
            sumAPVdemand += agent.demandAPV
            nAgents += 1

        self.PV = PV(Eg, sumCOC, sumAPVdemand/nAgents)

    def _step(self, SLPdata, HWprofile):
        """ Calculate and return current energy balance

        Args:
            SLPdata (dict with float): Standard load Profile of all agent types
            HWprofile (float): Actual hot water profile value [W]


        Returns:
            [(float, float)]: Current electrical and thermal energy balance [W]
        """
        # init current step
        electrical_load = 0.
        thermal_load = 0.
        electrical_generation = 0.
        thermal_generation = 0.
        electrical_balance = 0.
        thermal_balance = 0.

        for agent in self.agents:
            ae, at = agent._step(SLPdata, HWprofile)
            electrical_load += ae
            thermal_load += at

        electrical_balance = electrical_generation - electrical_load
        thermal_balance = thermal_generation - thermal_load

        return (electrical_balance, thermal_balance)

    def clone(inst,):
        if inst is Building.class_type.instance_type:
            def impl(inst,):
                return Building(inst.value)
            return impl
