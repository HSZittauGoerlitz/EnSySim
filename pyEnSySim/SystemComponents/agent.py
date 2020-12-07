from numba import types
from numba.experimental import jitclass

from numpy import random

spec = [('_type', types.unicode_type),
        ('demandAPV', types.float32),
        ('COC', types.float32),
        ]


@jitclass(spec)
class Agent():
    def __init__(self, aType):
        """ Create agent to simulate human consumption behaviour

        Args:
            aType (string): Type of agent:
                                "PHH": private household
                                "BSLa": Small Agriculture business with
                                        electrical standard load profile and
                                        thermal phh standard load profile
                                "BSLc": Common business with
                                        electrical standard load profile and
                                        thermal phh standard load profile
        """
        self._checkType(aType)
        self._type = aType
        self._getAPVdemand()
        self._getCOC()

    def _getAPVdemand(self):
        """ Calculate the demand for PV area to cover a part of the
        electrical energy consumption.
        Determine between PHH and BSL, since they have different
        underlying statistics

        Raises:
            ValueError: Error if agent type is unknown
        """
        # each agent gets a random variation on it's APV
        self.demandAPV = random.random()*0.4 + 0.8
        # if agent is one of the 70% PHH with small demand use this APV
        if self._type == "PHH":
            if random.random() < 0.7:
                self.demandAPV *= random.normal(0.3, 0.025)
                return
        # BSL and other PHH agents are using this APV
        self.demandAPV *= (random.f(7.025235971695065, 2205.596792511838) *
                           0.299704041191481 + 0.1)

    def _getCOC(self):
        """ Get COC factor of agent
        Determine between PHH and BSL, since they have different
        underlying statistics
        """
        if self._type == "PHH":
            def dist():
                return random.beta(a=3.944677863332723,
                                   b=2.638609989052125) * 5.
        else:
            def dist():
                return random.gamma(shape=1.399147113755027,
                                    scale=1.876519590091970)

        for i in range(10):
            COC = dist()
            if COC >= 1.:
                break

        if COC < 1:
            self.COC = 1.
        else:
            self.COC = COC

    def _getHotWaterDemand(self, HWprofile):
        """ Calculate agents actual hot water demand
        in relation to current hot water profile value.
        For the calculation a regression model,
        deviated off destatis data, is used.

        Args:
            HWprofile (float): Actual hw profile value [W]

        Returns:
            float: agents hot water demand [W]
        """
        return ((684.7 * HWprofile + 314.4) *
                (random.random()*0.4 + 0.8))

    def _checkType(self, aType):
        """ Check if given agent type is valid """
        if aType not in ["PHH", "BSLa", "BSLc"]:
            raise ValueError("Unknown agent type")

    def _step(self, SLPdata, HWprofile):
        """ Calculate and return current energy load

        Args:
            SLPdata (dict with float): Standard load Profile of all agent types
            HWprofile (float): Actual hw profile value [W]

        Returns:
            [(float, float)]: Currend electrical and thermal energy demand [W]
        """

        electrical = SLPdata[self._type] * (random.random()*0.4 + 0.8)
        thermal = self._getHotWaterDemand(HWprofile)

        return (electrical, thermal)
