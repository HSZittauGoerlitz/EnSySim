from SystemComponents.agent import Agent
from SystemComponents.pv import PV

from numba import optional, types, typed
from numba.experimental import jitclass

agent_type = Agent.class_type.instance_type

spec = [('agents', types.ListType(agent_type)),
        ('nMaxAgents', types.uint32),
        ('nAgents', types.uint32),
        ('Areas', types.float32[:]),  # m^2
        ('UValues', types.float32[:]),  # W / (K m^2)
        ('DeltaU', types.float32),  # W / (K m^2)
        ('nInfiltration', types.float32),  # 1/h
        ('nVentilation', types.float32),  # 1/h
        ('isAtDHN', types.boolean),
        ('V', types.float32),  # m^3
        ('Q_HLN', types.float32),  # W
        ('PV', optional(PV.class_type.instance_type)),
        ]


@jitclass(spec)
class Building():
    def __init__(self, nMaxAgents, Areas, UValues, DeltaU,
                 nInfiltration, nVentilation, V, isAtDHN, ToutN):
        """ Create building to simulate buildings energy demand as well

        Args:
            nMaxAgents (uint32): Number of max. possible agents
                                living in this building
            Areas (float32[:]): All building areas needed for
                                norm heat load calculation [m^2]
            UValues (float32[:]): All U-Values needed for
                                  norm heat load calculation [W/(m^2 K)]
            DeltaU (float32): Offset for U-Value correction [W/(m^2 K)]
                              (see _calculateNormHeatLoad for details)
            nInfiltration (float32): Air infiltration rate of building [^/h]
            nVentilation (float32): Air infiltration rate due ventilation [^/h]
            V (float32): Inner building Volume [m^3]
                         (This Value is used for calculation
                          of air renewal losses)
            isAtDHN (bool): If true building is connected to the
                            district heating network
            ToutN (float32): Normed outside temperature for
                             region of building [°C]
        """
        # check parameter
        if nMaxAgents <= 0:
            raise ValueError("Number of max. Agents must be greater than 0")

        if len(Areas) != len(UValues):
            raise ValueError("Number of Area values must match "
                             "number of U-Values")
        else:
            for idx in range(len(Areas)):
                if Areas[idx] < 0.:
                    raise ValueError("Area is smaller than 0")
                if UValues[idx] < 0.:
                    raise ValueError("U-Value is smaller than 0")

        if DeltaU <= 0.:
            raise ValueError("U-Value offset must not be negative")

        if (nInfiltration < 0.) | (nVentilation < 0.):
            raise ValueError("Infiltration rate must not be negative")

        if V < 0.:
            raise ValueError("Building volume must not be negative")

        # set attributes
        self.nMaxAgents = nMaxAgents
        self.nAgents = 0
        self.agents = typed.List.empty_list(agent_type)
        self.Areas = Areas
        self.UValues = UValues
        self.DeltaU = DeltaU
        self.nInfiltration = nInfiltration
        self.nVentilation = nVentilation
        self.V = V
        self._addNormHeatingLoad(ToutN)
        self.isAtDHN = isAtDHN
        # all other possible components are empty
        self.PV = None

    def addAgent(self, agent):
        if self.nAgents + 1 <= self.nMaxAgents:
            self.agents.append(agent)
            self.nAgents += 1
        else:
            print("WARNING: Number of max. Agents reached, "
                  "no agent is added")

    def addPV(self, PV):
        if self.PV is None:
            self.PV = PV
        else:
            print("WARNING: Building already has a PV plant, nothing is added")

    def addDimensionedPV(self, Eg):
        """ Add PV with dimensioning of installed PV power
        by agents demand statistics
        and environments global irradiation history.

        Args:
            Eg (float32): Mean annual global irradiation
                          for simulated region [kWh/m^2]
        """
        if len(self.agents) > 0:
            if self.PV is None:
                sumCOC = 0
                sumAPVdemand = 0
                nAgents = 0
                for agent in self.agents:
                    sumCOC += agent.COC
                    sumAPVdemand += agent.demandAPV
                    nAgents += 1

                self.PV = PV(Eg, sumCOC, sumAPVdemand/nAgents)
            else:
                print("WARNING: Building already has a PV plant, "
                      "nothing is added")
        else:
            print("HINT: Building has no agents, no PV added")

    def _addNormHeatingLoad(self, ToutN):
        """ Calculate normed heating load Q_HLN of a building [W]

        The calculation is done in reference to the simplified method
        of DIN EN 12831-1:2017-09
        Modifications / Simplifications:
            - Consideration of the whole building:
                o normed room temperature is set to 20°C
                o temperature matching coefficient is set to 1
            - Normed air heat losses include infiltration losses

        Args:
            ToutN (float32): Normed outside temperature for
                             region of building [°C]
        """
        # Temperature Difference
        dT = (20. - ToutN)
        # Transmission losses
        PhiT = 0.
        for i in range(len(self.Areas)):
            PhiT += self.Areas[i] * (self.UValues[i] + self.DeltaU)
        PhiT *= dT
        # Air renewal losses
        PhiA = self.V * (self.nInfiltration + self.nVentilation) * 0.3378 * dT

        self.Q_HLN = PhiT + PhiA

    def _getSpaceHeatingDemand(self, Tout, ToutN):
        """Calculate space heating demand in W

        The space heating demand is calculated in relation to outside
        temperature and a building specific heating load.
        Based on a linear regression model the mean daily heating power is
        calculated. The space heating energy demand is determined by
        multiplicating this power with 24h.

        Args:
            Tout (float32): Current (daily mean) outside temperature [°C]
            ToutN (float32): Normed outside temperature for
                             region of building [°C]

        Returns:
            float32: Space heating demand [W]
        """
        if Tout < 15:
            return self.Q_HLN * (ToutN-Tout) / (15-ToutN) + self.Q_HLN
        else:
            return 0.

    def _step(self, SLPdata, HWprofile, Tout, ToutN, Eg):
        """ Calculate and return current energy balance

        Args:
            SLPdata (dict with float): Standard load Profile of all agent types
            HWprofile (float): Actual hot water profile value [W]
            Tout (float32): Current (daily mean) outside temperature [°C]
            ToutN (float32): Normed outside temperature for
                             region of building [°C]
            Eg (float32): Current irradiation on PV module [W/m^2]

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

        # calculate loads
        for agent in self.agents:
            subBalance_e, subBalance_t = agent._step(SLPdata, HWprofile)
            electrical_load += subBalance_e
            thermal_load += subBalance_t

        thermal_load += self._getSpaceHeatingDemand(Tout, ToutN)

        # calculate generation
        # TODO: CHP
        if self.PV:
            electrical_generation += self.PV._step(Eg)

        if not self.isAtDHN:
            # Building is self-supplied
            thermal_generation = thermal_load

        # TODO: Storage, Controller

        # Calculate resulting energy balance
        electrical_balance = electrical_generation - electrical_load
        thermal_balance = thermal_generation - thermal_load

        return (electrical_balance, thermal_balance)
