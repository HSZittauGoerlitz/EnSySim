# run
%load_ext line_profiler

from SystemComponents.cell import Cell

%lprun -f Cell._step simulate(cell, nSteps, SLP_PHH, SLP_BSLa, SLP_BSLc, HWP, T, Eg)

Timer unit: 1e-07 s

Total time: 251.409 s
File: d:\ensysim\pyEnSySim\SystemComponents\cell.py
Function: _step at line 76

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    76                                               def _step(self, SLPdata, HWprofile, Tout, Eg):
    77                                                   """ Calculate and return current energy balance
    78
    79                                                   Args:
    80                                                       SLPdata (dict with float): Standard load Profile of all agent types
    81                                                       HWprofile (float): Actual hot water profile value [W]
    82                                                       Tout (float32): Current (daily mean) outside temperature [°C]
    83                                                       Eg (float32): Current irradiation on PV module [W/m^2]
    84
    85                                                   Returns:
    86                                                       [(float, float)]: Current electrical and thermal energy balance [W]
    87                                                   """
    88                                                   # init current step
    89      2976      27228.0      9.1      0.0          electrical_load = 0.
    90      2976      18198.0      6.1      0.0          thermal_load = 0.
    91      2976      16642.0      5.6      0.0          electrical_generation = 0.
    92      2976      16224.0      5.5      0.0          thermal_generation = 0.
    93      2976      15816.0      5.3      0.0          electrical_balance = 0.
    94      2976      16316.0      5.5      0.0          thermal_balance = 0.
    95
    96                                                   # calculate buildings
    97   1505856    9036000.0      6.0      0.4          for building in self.buildings:
    98   3005760 2466423019.0    820.6     98.1              subBalance_e, subBalance_t = building._step(SLPdata, HWprofile,
    99   1502880   10081921.0      6.7      0.4                                                          Tout, self.ToutN, Eg)
   100   1502880   17737570.0     11.8      0.7              electrical_balance += subBalance_e
   101   1502880   10555134.0      7.0      0.4              thermal_balance += subBalance_t
   102
   103                                                   # calculate cells
   104      2976      30820.0     10.4      0.0          for cell in self.cells:
   105                                                       subBalance_e, subBalance_t = cell._step(SLPdata, HWprofile,
   106                                                                                               Tout, Eg)
   107                                                       electrical_balance += subBalance_e
   108                                                       thermal_balance += subBalance_t
   109
   110                                                   # calculate PV
   111      2976      25242.0      8.5      0.0          if self.PV is not None:
   112                                                       electrical_generation += self.PV._step(Eg)
   113
   114                                                   # TODO: CHP, Storage, Controller
   115
   116      2976      26801.0      9.0      0.0          electrical_balance += electrical_generation - electrical_load
   117      2976      24081.0      8.1      0.0          thermal_balance += thermal_generation - thermal_load
   118
   119      2976      22837.0      7.7      0.0          if self.hist:
   120                                                       self.balance_e[:-1] = self.balance_e[1:]
   121                                                       self.balance_e[-1] = electrical_balance
   122                                                       self.balance_t[:-1] = self.balance_t[1:]
   123                                                       self.balance_t[-1] = thermal_balance
   124
   125      2976      19181.0      6.4      0.0          return (electrical_balance, thermal_balance)