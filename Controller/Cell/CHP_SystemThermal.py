from abc import ABC, abstractmethod
from typing import Tuple


class CtrlTemplate(ABC):
    @abstractmethod
    def step(self, StorageState: float) -> Tuple[bool, bool]:
        pass


class CtrlDefault(CtrlTemplate):
    def __init__(self):
        self.STORAGE_LEVEL_H = 0.3
        self.STORAGE_LEVEL_L = 0.2
        self.STORAGE_LEVEL_LL = 0.05

    def step(self, StorageState, *args):
        """ Default controller strategy

        Arguments:
            StorageState {float} -- Relative charge of thermal storage (0 to 1)

        Returns:
            (bool, bool) -- Operational state of CHP and Boiler
                            (True => running)
        """
        CHPstate = False
        BoilerState = False

        if StorageState <= self.STORAGE_LEVEL_LL:
            BoilerState = True
            CHPstate = True
        elif (((StorageState <= self.STORAGE_LEVEL_L) and not CHPstate) or
              ((StorageState >= self.STORAGE_LEVEL_H) and BoilerState)):
            CHPstate = True

        return (CHPstate, BoilerState)
