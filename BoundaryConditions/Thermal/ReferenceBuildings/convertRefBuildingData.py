# %% imports
import json
import numpy as np
import pandas as pd
import os

""" Load all available building reference data sets and provide them as
combined pandas data frame. The data of individual building types is
saved in the columns. The row index has the information to the data
sections: Geometry, UValues and n (Infiltration / Ventilation rate).

All json data not needed for model is neglected, e.g. building volume.
"""
# %% parameter
# choose location for execution via vs code jupyter or script
cwd = os.getcwd()
if cwd.split(os.sep)[-1] == "ReferenceBuildings":
    loc = cwd + os.sep
else:
    loc = "pyEnSySim/BoundaryConditions/Thermal/ReferenceBuildings/"
refFiles = os.listdir(loc)

buildingData = pd.DataFrame(index=['Geometry', 'UValues', 'n'])


# %% helper
def getA_UValuePairs(data, name):
    """ Filter all area information from building data
    and find corresponding u values for each age class
    and modernisation state

    The aim of this method is, that the U-Values returned
    suit the Areas returned (both list are sorted equally)

    If geometry has information about volume or complete
    living Area (key='Aliving'), this informations are descarded.

    Args:
        data (dict): Data for building
        name (string): Name of building data set to mention,
                       if something is wrong with data

    Returns:
        tuple with:
            - list of float: Areas
            - list of string: Component name of areas
            - float: Volume
            - nested lists of float: [[[U-Values], U-Delta], -> class 1
                                      [[U-Values], U-Delta], -> class 2
                                      ...]
            - list of tuple of string: Class and modernisation state names
    """
    A = []
    U = []
    CMnames = []
    Anames = []

    for part, value in data['Geometry'].items():
        # skip geometries not needed
        if part == 'V':
            V = np.float32(value)
            continue
        if part == 'nUnits':
            nUnits = np.uint32(value)
            continue
        elif part == 'Aliving':
            continue
        elif part[0] != 'A':
            print("WARNING: Unknown entry {} in Geometry of {}"
                  .format(part, name))
            continue

        Anames.append(part[1:].capitalize())
        A.append(value)

    for CName in data['Uvalues'].keys():
        for MName in data['Uvalues'][CName]:
            CMnames.append((CName, MName))
            Uclass = np.zeros(len(Anames), dtype=np.float32)
            for idx, name in enumerate(Anames):
                Uclass[idx] = data['Uvalues'][CName][MName][name]
            U.append([Uclass,
                      np.float32(data['Uvalues'][CName][MName]['Delta'])])

    return (np.array(A, dtype=np.float32), Anames, V, nUnits, U, CMnames)


# %% run
for file_ in refFiles:
    name, ending = file_.split(".")
    if ending == "json":
        with open(loc + file_, 'r') as data_file:
            data = json.load(data_file)
        A, Anames, V, nUnits, U, CMnames = getA_UValuePairs(data, name)
        GeoIdx = pd.MultiIndex.from_product([['Areas'], Anames])
        Geo = pd.DataFrame(A, index=GeoIdx, columns=['Value'])
        Geo.loc[('Volume', ''), 'Value'] = V
        Geo.loc[('nUnits', ''), 'Value'] = nUnits
        Geo.loc[('A_living', ''), 'Value'] = data['Geometry']['Aliving']
        U = pd.DataFrame(U,
                         index=pd.MultiIndex.from_tuples(CMnames),
                         columns=['UValues', 'DeltaU']).T
        n = pd.DataFrame.from_dict(data['n'])
        # save to hdf file
        store = pd.HDFStore(name + '.h5')
        store['Geo'] = Geo
        store['U'] = U
        store['n'] = n
        store.close()

# %%
