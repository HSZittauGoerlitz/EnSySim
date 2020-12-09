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
def getA_UValuePairs(data):
    """ Filter all area information from building data
    and find corresponding u values for each age class
    and modernisation state

    The aim of this method is, that the U-Values returned
    suit the Areas returned (both list are sorted equally)

    If geometry has information about volume or complete
    living Area (key='Aliving'), this informations are descarded.

    Args:
        data (dict): Data for building

    Returns:
        tuple with:
            - list of float: Areas
            - list of string: Component name of areas
            - nested lists of float: [[[U-Values], U-Delta], -> class 1
                                      [[U-Values], U-Delta], -> class 2
                                      ...]
            - list of tuple of string: Class and modernisation state names
    """
    A = []
    U = []
    CMnames = []
    names = []
    for part, area in data['Geometry'].items():
        # skip geometries not needed
        if part[0] != 'A':
            continue
        elif part == 'Aliving':
            continue

        names.append(part[1:].capitalize())
        A.append(float(area))

    for CName in data['Uvalues'].keys():
        for MName in data['Uvalues'][CName]:
            CMnames.append((CName, MName))
            Uclass = []
            for name in names:
                Uclass.append(data['Uvalues'][CName][MName][name])
            U.append([Uclass, data['Uvalues'][CName][MName]['Delta']])

    return (A, names, U, CMnames)


# %% run
for file_ in refFiles:
    name, ending = file_.split(".")
    if ending == "json":
        with open(loc + file_, 'r') as data_file:
            data = json.load(data_file)
        A, Anames, U, CMnames = getA_UValuePairs(data)
        A = pd.DataFrame(A, index=Anames, columns=['Area_in_m2'])
        U = pd.DataFrame(np.array(U).T,
                         columns=pd.MultiIndex.from_tuples(CMnames),
                         index=['UValues', 'DeltaU'])
        n = pd.DataFrame.from_dict(data['n'])
        # save to hdf file
        store = pd.HDFStore(name + '.h5')
        store['A'] = A
        store['U'] = U
        store['n'] = n
        store.close()

# %%
