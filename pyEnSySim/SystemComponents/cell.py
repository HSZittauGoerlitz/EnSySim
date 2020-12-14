import numpy as np

# from numba import types, typed
# from numba.experimental import jitclass

# buildingType = Building.class_type.instance_type
# spec = [('buildings', types.ListType(buildingType)),
#         ('nBuildings', types.int32),
#         ('Eg', types.float32),
#         ('ToutN', types.float32),
#         ('hist', types.int32),
#         ('balance_e', types.float32[:]),
#         ('balance_t', types.float32[:]),
#         ('PV', PV.class_type.instance_type),
#         ]


# @jitclass(spec)
class Cell():
    def __init__(self, Eg, ToutN, hist=None):
        """ Create cell to simulate a energy grid segment

        Args:
            Eg (float): Mean annual global irradiation
                        for simulated region [kWh/m^2]
            ToutN (float): Normed outside temperature for
                           specific region in °C
            hist (int): If not None the last "hist" values of
                        electrical and thermal balance are saved by this cell
                        (default: None)
        """
        # input checks
        if Eg < 0:
            raise ValueError("Mean annual global irradiation is "
                             "a negative number")

        # init instance attributes
        self.Eg = Eg
        self.ToutN = ToutN
        self.buildings = []
        self.nBuildings = 0
        self.hist = False
        self.PV = None
        self.cells = []
        self.nCells = 0

        if hist:
            self.hist = True
            self.balance_e = np.zeros(hist, dtype=np.float32)
            self.balance_t = np.zeros(hist, dtype=np.float32)

    def activateHist(self, nHist):
        self.hist = True
        self.balance_e = np.zeros(nHist, dtype=np.float32)
        self.balance_t = np.zeros(nHist, dtype=np.float32)

    def addBuilding(self, building):
        self.buildings.append(building)
        self.nBuildings += 1

    def addCell(self, cell):
        self.cells.append(cell)
        self.nCells += 1

    def addPV(self, PV):
        if not self.PV:
            self.PV = PV
        else:
            print("WARNING: Cell already has a PV plant, nothing is added")

    def deactivateHist(self):
        self.hist = False
        self.balance_e = None
        self.balance_t = None

    def _step(self, SLPdata, HWprofile, Tout, Eg):
        """ Calculate and return current energy balance

        Args:
            SLPdata (dict with float): Standard load Profile of all agent types
            HWprofile (float): Actual hot water profile value [W]
            Tout (float32): Current (daily mean) outside temperature [°C]
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

        # calculate buildings
        for building in self.buildings:
            subBalance_e, subBalance_t = building._step(SLPdata, HWprofile,
                                                        Tout, self.ToutN, Eg)
            electrical_balance += subBalance_e
            thermal_balance += subBalance_t

        # calculate cells
        for cell in self.cells:
            subBalance_e, subBalance_t = cell._step(SLPdata, HWprofile,
                                                    Tout, Eg)
            electrical_balance += subBalance_e
            thermal_balance += subBalance_t

        # calculate PV
        if self.PV is not None:
            electrical_generation += self.PV._step(Eg)

        # TODO: CHP, Storage, Controller

        electrical_balance += electrical_generation - electrical_load
        thermal_balance += thermal_generation - thermal_load

        if self.hist:
            self.balance_e[:-1] = self.balance_e[1:]
            self.balance_e[-1] = electrical_balance
            self.balance_t[:-1] = self.balance_t[1:]
            self.balance_t[-1] = thermal_balance

        return (electrical_balance, thermal_balance)
