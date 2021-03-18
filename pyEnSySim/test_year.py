# %% imports
import pandas as pd
from collections import Counter as cnt
from matplotlib import pyplot as plt

# %% functions


def get_uniques(list_in):
    # intilize an empty list
    unq_list = []

    # Check for elements
    for x in list_in:
        # check if exists in unq_list
        if x not in unq_list:
            unq_list.append(x)

    return unq_list

# %% get reference year temperatures


path = "BoundaryConditions/Weather/"
file_name = "TRY2015.h5"

df = pd.read_hdf(path+file_name)

t_ref = df['temperatures_15'].tolist()

# %% get only heating days
t_heat = 12
heating_days = []
for i in range(0, 365):
    t_day_mean = sum(t_ref[(i*24):(i*24+24)]) / 24.
    if t_day_mean < t_heat:
        heating_days.extend([True for i in range(24)])
    else:
        heating_days.extend([False for i in range(24)])
t_heating = []
for i in range(0, len(t_ref)):
    if heating_days[i] is True:
        t_heating.append(t_ref[i])

# %% pack data

t_heating.sort()
uniques = get_uniques(t_heating)
counts = cnt(t_heating)
count = []
for temp in uniques:
    count.append(counts[temp])

#plt.plot(uniques, count)

# %%
cum_count = []
for i in range(0, len(count)):
    cum_count.append(sum(count[0:i]))

fig, ax = plt.subplots(figsize=(5,5))
ax.plot(uniques, cum_count)
plt.xlim([-20,12])
ax.yaxis.set_label_position("right")
ax.yaxis.tick_right()
plt.ylim([0,6000])
#plt.plot(uniques, cum_count)
# %%
