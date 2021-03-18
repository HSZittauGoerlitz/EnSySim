""" Convert DWD reference year data for EnSySim """
# %% imports
import json
import os
import pandas as pd

# %% Parameter
# dictionary to translate file names to TRY type
REF_TRANSLATION = {"Jahr": "reference",
                   "Somm": "summer_extreme",
                   "Wint": "winter_extreme"
                   }


# %% helper functions
def _checkLocation(loc):
    loc.replace('\\', '/')
    if loc[-1] != '/':
        loc += '/'

    return loc


def _estimateNormedOutsideTemperature(data):
    """ When the normed outside temperature for a given region is'nt known,
    this method will estimate it as follows:

        - the two day mean temperatures are calculated for
            . reference year
            . extreme winter year
        - the normed outside temperature is the weighted min
          of both mean curves
            . the reference min is weighted with 0.35
            . the winter extreme min is weighted with 0.65

    A higher weighting of extreme winter data is used to model the tendency
    of oversize the heat systems.

    Arguments:
        data {pd DataFrame} -- Preprocessed TRY data for
                               reference and extreme years

    Returns:
        float - Estimation of normed outside temperature for
                given reference weather data
    """
    grouped_data = data.groupby('doy')
    meanT_ref = grouped_data.mean().reference['T']
    meanT_win = grouped_data.mean().winter_extreme['T']

    twoDayMeanT_ref = 0.5 * (meanT_ref[1:].values + meanT_ref[:-1].values)
    twoDayMeanT_win = 0.5 * (meanT_win[1:].values + meanT_win[:-1].values)

    return 0.35 * twoDayMeanT_ref.min() + 0.65 * twoDayMeanT_win.min()


def _findBeginning(file_name, loc):
    """Scan given TRY dat file and find end of header (start of data)

    Arguments:
        file_name {string} -- Name of TRY data file
        loc {string} -- Location of TRY data file

    Returns:
        (int, string) -- (lines before data starts,
                          column header)
    """
    with open(loc + file_name, 'r') as dat_file:
        last_line = dat_file.readline()
        current_line = dat_file.readline()
        dat_start = 2
        while current_line[:3] != '***':
            last_line = current_line  # save column header
            current_line = dat_file.readline()
            dat_start += 1
            if dat_start == 100:
                break

    # get header as list of string
    last_line = last_line.split()

    return (dat_start, last_line)


def _getNormedOutsideTemperature(data, region):
    """ Load normed outside temperature for given region.

    Those temperatures have to be added to the 'ToutNorm.json' file, with the
    corresponding region name. If this information is missing, a value is
    estimated for the region TRY data.

    Arguments:
        data {pd DataFrame} -- Preprocessed TRY data for
                               reference and extreme years
        region {string} -- Name of the region for wich the normed outside
                           temperature is needed

    Returns:
        float - Normed outside temperature
    """
    with open('TnormOut.json', 'r') as ToutFile:
        ToutData = json.load(ToutFile)

    try:
        return ToutData[region]
    except KeyError:
        print("WARNING: Normed outside temperature for given region ({}) not "
              "found. The value will be estimated.".format(region))
        return _estimateNormedOutsideTemperature(data)


def _getRefYear(file_name):
    """ Read reference year from given file name

    Arguments:
        file_name {string} -- Name of file with DWD reference weather data

    Returns:
        int -- Reference year
    """
    return int(file_name.split('_')[0][-4:])


def _getTRY_Data_T_Eg(file_name, loc):
    """ Get the temperature and global radiation values (Eg) for given
    DWD measurement file. The global radiation is calculated as sum of
    direct and diffuse sun light (Columns B and D).

    The temperature is taken directly as [degC]
    The radiation data is recalculated as [kw/m^2]
    The global radiation value is calculated as [kWh/m^2 ]
    (time integral of radiation data)

    Arguments:
        file_name {string} -- Name of TRY data file
        loc {string} -- Location of TRY data file

    Returns:
        pd DataFrame -- Ref. year data (T, Eg) for given TRY file
    """
    refYear = _getRefYear(file_name)

    skip_lines, header = _findBeginning(file_name, loc)

    data = pd.read_fwf(loc + file_name,
                       colspecs='infer', infer_nrows=365*24,
                       skiprows=skip_lines,
                       names=header)

    # Fix hour names 0 to 23
    data.HH -= 1
    data['date_time'] = pd.to_datetime((refYear*10000 +
                                        data.MM*100 + data.DD).apply(str),
                                       format='%Y%m%d')
    data.date_time += pd.to_timedelta(data.HH, unit='h')

    data['Eg'] = (data.B + data.D) * 1e-3  # W -> kW
    data['T'] = data.t

    # clean up
    data.drop(columns=header, inplace=True)
    # not necessary, but in case something happened to the data order
    data.sort_values('date_time', axis=0, ascending=True,
                     inplace=True, ignore_index=True)

    return data


def _loadAllTRYfiles(loc):
    """ Load TRY files for standard reference year as well as
    reference years with extreme summer and winter.

    Arguments:
        loc {string} -- Location TRY data files

    Returns:
        pandas DataFrame -- Ref. year data (T, Eg) for
                            standard and extreme cases
    """
    data = pd.DataFrame()

    for content in os.listdir(loc):
        file_name = content
        content = content.split('.')
        if content[-1] == "dat":
            refType = REF_TRANSLATION[content[-2].split('_')[-1]]
            sub_data = _getTRY_Data_T_Eg(file_name, loc)
            # time course is taken from reference year
            if refType == 'reference':
                data[('date_time', '')] = sub_data.date_time

            data[(refType, 'Eg [kW]')] = sub_data['Eg']
            data[(refType, 'T [degC]')] = sub_data['T']

    data[('doy', '')] = data[('date_time', '')].dt.day_of_year
    data.columns = pd.MultiIndex.from_tuples(data.columns)

    return data


def _saveData(data, ToutNorm, name):
    """ Save given weather data as h5 file

    There are two kinds of data stored:
        1. Key: Weather (reference and extreme years)
            - date_time / doy for the reference year
            - Eg (global irradiation in kW/m^2)
            - T (Air temperature in degC)
        2. Key: Standard
            - Eg (yearly global radiation in kWh/m^2)
            - T (Normed outside temperature)

    The yearly global radiation is calculated by the reference year data.

    Arguments:
        data {pd DataFrame} -- Preprocessed TRY data for
                               reference and extreme years
        ToutNorm {float} -- Normed outside temperature [degC]
        Name {String} -- Name of h5-file in which the data is stored
    """
    # store weather data
    store = pd.HDFStore(name + '.h5')
    store['Weather'] = data
    # calculate and store standard data
    sd = pd.DataFrame(columns=['Value'])
    # in case of unequally spaced data get time steps
    dt = data.date_time.diff()
    # calculate yearly Eg Energy and store it
    sd.loc['EgNorm kWh', 'Value'] = (data.reference['Eg [kW]'].values[0] +
                                     (data.reference['Eg [kW]'][1:].cumsum() *
                                     dt.dt.total_seconds()[1:] / 3600.)
                                     .values[-1])
    sd.loc['ToutNorm degC', 'Value'] = ToutNorm
    store['Standard'] = sd
    print(sd)
    store.close()


def importData(loc):
    """ Load all raw data of DWD reference weather data in given location

    This method will browse all sub directories, load and preprocess the
    data. The results are saved in the directory of this script as '.h5' files.
    The weather data is stored under the key 'Weather'. The generalized
    data, needed for design, is stored under the key 'Standard'.

    Arguments:
        loc {[type]} -- [description]
    """
    loc = _checkLocation(loc)

    for content in os.listdir(loc):
        if os.path.isdir(loc + content):
            data = _loadAllTRYfiles(loc + content + os.sep)
            T = _getNormedOutsideTemperature(data, content)
            _saveData(data, T, content)


# %%
dat_loc = './TRWdata_raw'

importData(dat_loc)


# %%
