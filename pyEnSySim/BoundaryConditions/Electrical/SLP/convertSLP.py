import json
import numpy as np
import pandas as pd

floc = "./pyEnSySim/BoundaryConditions/Electrical/SLP/"
fname = ["PHH", "G0", "L0"]


for name in fname:
    with open(floc + name + ".json", 'r') as data_file:
        data = json.load(data_file)

    keys_level1 = list(data[0].keys())
    keys_level2 = []

    for key in keys_level1:
        keys_level2.append(list(data[0][key][0].keys()))

    colIdx = []

    nKeys = len(keys_level1)

    if nKeys != len(keys_level2):
        raise("Error length of level1 and level2 keys must be equal")

    for idx in range(nKeys):
        for sub_idx in range(len(keys_level2[idx])):
            colIdx.append((keys_level1[idx], keys_level2[idx][sub_idx]))

    colIdx = pd.MultiIndex.from_tuples(colIdx)

    df = pd.DataFrame(0, index=np.arange(len(data)), columns=colIdx)

    for lNr, line in enumerate(data):
        for idx in colIdx:
            df.loc[lNr, idx] = line[idx[0]][0][idx[1]]

    df.to_hdf(floc + name + ".h5", name, 'w')
