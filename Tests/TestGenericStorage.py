# %% imports
import numpy as np
from SystemComponentsFast import GenericStorage, test_generic_storage

import os
print(os.getpid())

# %% Parameter
dt = 0.25  # h
cap = 100.  # Wh
maxPow = 10.  # W
eff = 0.95  # -
selfDis = 0.05  # 1/h


# %% test test functions
def testStorage(pow_):
    storage = GenericStorage(cap, eff, eff, selfDis, maxPow, 0)

    # Energy before charging
    E_before = storage.charge
    # Energy from outside
    E_in = pow_ * dt

    diff, loss = test_generic_storage(storage, pow_)
    E_actual = (storage.charge - E_before) + diff*dt + loss*dt

    if np.abs(E_in - E_actual) > 1e-2:
        print("________________")
        print("Expected Energy: {:.2f} Wh; Actual Energy: {:.2f} Wh"
              .format(E_in, E_actual))
        print("Details\n-------")
        print("Storage charge start: {:.2f} Wh".format(E_before))
        print("Storage charge end: {:.2f} Wh".format(storage.charge))
        print("Storage charge difference: {:.2f} Wh"
              .format(storage.charge - E_before))
        print("Storage diff: {:.2f} Wh".format(diff*dt))
        print("Storage loss: {:.2f} Wh\n".format(loss*dt))

        return (False, E_before, E_in, diff, loss, E_actual)

    return (True, E_before, E_in, diff, loss, E_actual)


# %% charge test
for i in range(int(1e6)):
    success, E_before, E_in, diff, loss, E_actual = testStorage(maxPow)
    if not success:
        break

if success:
    print("Charging test passed")
else:
    print("Charging test failed")

# %% discharge test
for i in range(int(1e6)):
    success, E_before, E_in, diff, loss, E_actual = testStorage(-maxPow)
    if not success:
        break

if success:
    print("Discharging test passed")
else:
    print("Discharging test failed")
