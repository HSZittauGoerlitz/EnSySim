import numpy as np
import numpy.matlib
import pandas as pd
from scipy.interpolate import interp1d


DOY_LEAPDAY = 60


def _addHotwater(simData):
    """ Calculate hot water demand profile in W
    All load values are modified by a daily profile.
    The profile values have to be scaled by each agents COC value.

    Args:
        simData (pandas data frame): Simulation time and data

    Returns:
        pandas data frame: simData complemented by hot water profile
    """
    # all agents are using PHH profile,
    # since there is no statistic to business hot water demand available
    HWP = pd.read_hdf("./BoundaryConditions/Thermal/"
                      "HotWaterDayProfile.h5", key='PHH')
    simData.loc[:, 'HWP_in_W'] = (HWP.loc[simData.time.dt.hour,
                                  'fProportion'].values *
                                  1e3 / 8760.)  # kW -> W; 8760h = 1 year

    return simData


def _addSLPdata(simData):
    """ Add standard load profile for different agents to time data frame.
        The SLP is calculated for the time frame beginning at startDate
        and ending at endDate (inclusive). For each day a curve with
        15min steps is calculated, based on the SLP data (H0 for PHH,
        G0/L0 for business) from BDEW. The SLP differes between Summer,
        Winter, intermediate periods and Weekdays, Weekend, Holydays as well.
          The PHH SLP is additionally modyfied according to BDEW
        by a dynamic sampling profile.

    Args:
        simData (pandas data frame): Simulation time information
                                     (is created by getSimTime method)

    Returns:
        pandas data frame: Data frame with sim time and SLP data
    """
    # prepare columns
    cIdx = ['SLP_PHH', 'SLP_BSLa', 'SLP_BSLc']
    newData = pd.DataFrame(index=np.arange(simData.shape[0]), columns=cIdx)
    # load SLP base data
    PHH = pd.read_hdf("./BoundaryConditions/Electrical/SLP/PHH.h5",
                      key='PHH')
    G0 = pd.read_hdf("./BoundaryConditions/Electrical/SLP/G0.h5",
                     key='G0')
    L0 = pd.read_hdf("./BoundaryConditions/Electrical/SLP/L0.h5",
                     key='L0')
    # add SLP data
    # Winter
    mask = simData.winter & (simData.weekDaySLP < 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, 'SLP_PHH'] = np.matlib.repmat(PHH.Winter.WorkDay,
                                                    1, nDays)[0]
    newData.loc[mask, 'SLP_BSLc'] = np.matlib.repmat(G0.Winter.WorkDay,
                                                     1, nDays)[0]
    newData.loc[mask, 'SLP_BSLa'] = np.matlib.repmat(L0.Winter.WorkDay,
                                                     1, nDays)[0]
    mask = simData.winter & (simData.weekDaySLP == 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, 'SLP_PHH'] = np.matlib.repmat(PHH.Winter.Saturday,
                                                    1, nDays)[0]
    newData.loc[mask, 'SLP_BSLc'] = np.matlib.repmat(G0.Winter.Saturday,
                                                     1, nDays)[0]
    newData.loc[mask, 'SLP_BSLa'] = np.matlib.repmat(L0.Winter.Saturday,
                                                     1, nDays)[0]
    mask = simData.winter & (simData.weekDaySLP == 6)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, 'SLP_PHH'] = np.matlib.repmat(PHH.Winter.Sunday,
                                                    1, nDays)[0]
    newData.loc[mask, 'SLP_BSLc'] = np.matlib.repmat(G0.Winter.Sunday,
                                                     1, nDays)[0]
    newData.loc[mask, 'SLP_BSLa'] = np.matlib.repmat(L0.Winter.Sunday,
                                                     1, nDays)[0]
    # Intermediate
    mask = simData.intermediate & (simData.weekDaySLP < 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, 'SLP_PHH'] = np.matlib.repmat(PHH.InterimPeriod.WorkDay,
                                                    1, nDays)[0]
    newData.loc[mask, 'SLP_BSLc'] = np.matlib.repmat(G0.InterimPeriod.WorkDay,
                                                     1, nDays)[0]
    newData.loc[mask, 'SLP_BSLa'] = np.matlib.repmat(L0.InterimPeriod.WorkDay,
                                                     1, nDays)[0]
    mask = simData.intermediate & (simData.weekDaySLP == 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, 'SLP_PHH'] = np.matlib.repmat(PHH.InterimPeriod.Saturday,
                                                    1, nDays)[0]
    newData.loc[mask, 'SLP_BSLc'] = np.matlib.repmat(G0.InterimPeriod.Saturday,
                                                     1, nDays)[0]
    newData.loc[mask, 'SLP_BSLa'] = np.matlib.repmat(L0.InterimPeriod.Saturday,
                                                     1, nDays)[0]
    mask = simData.intermediate & (simData.weekDaySLP == 6)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, 'SLP_PHH'] = np.matlib.repmat(PHH.InterimPeriod.Sunday,
                                                    1, nDays)[0]
    newData.loc[mask, 'SLP_BSLc'] = np.matlib.repmat(G0.InterimPeriod.Sunday,
                                                     1, nDays)[0]
    newData.loc[mask, 'SLP_BSLa'] = np.matlib.repmat(L0.InterimPeriod.Sunday,
                                                     1, nDays)[0]
    # Summer
    mask = simData.summer & (simData.weekDaySLP < 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, 'SLP_PHH'] = np.matlib.repmat(PHH.Summer.WorkDay,
                                                    1, nDays)[0]
    newData.loc[mask, 'SLP_BSLc'] = np.matlib.repmat(G0.Summer.WorkDay,
                                                     1, nDays)[0]
    newData.loc[mask, 'SLP_BSLa'] = np.matlib.repmat(L0.Summer.WorkDay,
                                                     1, nDays)[0]
    mask = simData.summer & (simData.weekDaySLP == 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, 'SLP_PHH'] = np.matlib.repmat(PHH.Summer.Saturday,
                                                    1, nDays)[0]
    newData.loc[mask, 'SLP_BSLc'] = np.matlib.repmat(G0.Summer.Saturday,
                                                     1, nDays)[0]
    newData.loc[mask, 'SLP_BSLa'] = np.matlib.repmat(L0.Summer.Saturday,
                                                     1, nDays)[0]
    mask = simData.summer & (simData.weekDaySLP == 6)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, 'SLP_PHH'] = np.matlib.repmat(PHH.Summer.Sunday,
                                                    1, nDays)[0]
    newData.loc[mask, 'SLP_BSLc'] = np.matlib.repmat(G0.Summer.Sunday,
                                                     1, nDays)[0]
    newData.loc[mask, 'SLP_BSLa'] = np.matlib.repmat(L0.Summer.Sunday,
                                                     1, nDays)[0]
    # Dynamic sampling of PHH profile
    newData.loc[:, 'SLP_PHH'] *= (- 3.92*1e-10*simData.doy**4 +
                                  3.2*1e-7*simData.doy**3 -
                                  7.02*1e-5*simData.doy**2 +
                                  2.1*1e-3*simData.doy + 1.24)
    # merge data frames
    simData = simData.join(newData)

    return simData


def _cleanSimData(simData):
    """ Remove unnecessary columns

    Args:
        simData (pandas data frame): Simulation data

    Returns:
        pandas data frame: Data frame with sim data
    """
    simData.drop(columns=["doy", "weekDaySLP", "summer",
                          "winter", "intermediate"], inplace=True)

    return simData


def _getSimTime(startDate, endDate):
    """ Prepare a pandas dataframe for simulation course
    This function will add all time related informations
    (Summer, Winter, day of year, hour of day, correct week days for SLP)

    Info to pandas WeekDays: Monday=0, Sunday=6.

    Args:
        startDate (string): Start date DD.MM.YYYY
                            (start time is hard coded to 00:00)
        endDate (string): End date DD.MM.YYYY
                          (end day is not in time range, so end date
                           should be end date + 1 day)

    Return:
        pandas data frame: Time course and additional informations
                           for preparing boundary conditions of
                           a simulation run
    """
    startDate = startDate.split(".")
    startDate = "/".join([startDate[1], startDate[0], startDate[2]])
    endDate = endDate.split(".")
    endDate = "/".join([endDate[1], endDate[0], endDate[2]])

    time = pd.date_range(startDate, endDate, freq='0.25H', closed='left')
    doy = time.dayofyear
    weekDaySLP = time.dayofweek

    df = pd.DataFrame({'time': time, 'doy': doy, 'weekDaySLP': weekDaySLP})
    # add relevant time periods
    df['summer'] = (((time.month > 5) & (time.month < 9)) |
                    ((time.month == 5) & (time.day >= 15)) |
                    ((time.month == 9) & (time.day <= 14)))
    df['winter'] = (((time.month >= 11) | (time.month < 3)) |
                    ((time.month == 3) & (time.day <= 20)))
    df['intermediate'] = ~(df['summer'] | df['winter'])
    # correct week days of SLP days
    # -> add Christmas Eve and New Years Eve to Sat if Week
    mask = ((time.month == 12) &
            ((time.day == 24) | (time.day == 31)) &
            (df.weekDaySLP < 5))
    df.loc[mask, 'weekDaySLP'] = 5
    # load and check holidays and set them to sunday
    holidays = pd.read_csv("./BoundaryConditions/Simulation/holydaysSN.csv",
                           parse_dates=[0],
                           dayfirst=True)

    mask = pd.to_datetime(time.date).isin(holidays.date)
    df.loc[mask, 'weekDaySLP'] = 6

    return df


def _getWeather(simData, region):
    """Calculate temperature and irradiation curve for
        given simulation time and region

    Test reference year data of DWD consist out of:
        - Data for reference year
        - Data for year with extreme summer
        - Data for extreme winter

    By randomly weighting those curves a new weather curve is generated. The
    random weights are updated per simulated year.

    Arguments:
        simData {pandas data frame} -- Simulation data
        region {string} -- Location of simulation
                           (determines climate / weather)
                           Supported regions:
                             East, West, South, North

    Returns:
        pandas data frame -- Simulation data extended by weather course
    """
    RefWeather = pd.read_hdf("./BoundaryConditions/Weather/" +
                             region + ".h5", 'Weather')
    # add columns for weather
    simData['T'] = 0.
    simData['Eg'] = 0.

    # get mask of all non leap year days once -> keep out doy 366
    maskDoy = (simData.doy >= 1) & (simData.doy <= 365)

    # Split up Eg data generation into linked doy sequences
    for year in range(simData.time.dt.year.min(),
                      simData.time.dt.year.max()+1):
        # for now ignore the possibility of leap year
        maskY = ((simData.time.dt.year == year) & maskDoy)

        # get weighting factors
        w = np.random.random(3)
        w /= w.sum()  # sum of all factors must be 1
        # Create Weather functions
        t = (RefWeather.date_time - RefWeather.date_time[0]).dt.total_seconds()
        t /= 3600.  # in [h]
        fT = interp1d(t,
                      (RefWeather.reference['T [degC]']*w[0] +
                       RefWeather.winter_extreme['T [degC]']*w[1] +
                       RefWeather.summer_extreme['T [degC]']*w[2]).values,
                      'linear', bounds_error=False, fill_value='extrapolate')
        fEg = interp1d(t,
                       (RefWeather.reference['Eg [kW]']*w[0] +
                        RefWeather.winter_extreme['Eg [kW]']*w[1] +
                        RefWeather.summer_extreme['Eg [kW]']*w[2]).values,
                       'linear', bounds_error=False, fill_value='extrapolate')

        # get time for interpolation
        t = simData.loc[maskY, 'time']
        t = ((t - pd.to_datetime("01.01.{}".format(year)))
             .dt.total_seconds() / 3600.)  # in h
        # add new Data
        simData.loc[maskY, 'T'] = fT(t)
        simData.loc[maskY, 'Eg'] = fEg(t)

        # leap day treatment
        if simData.time[maskY].dt.is_leap_year.any():
            # update year mask
            maskY = simData.time.dt.year == year
            # handle different cases
            doyEnd = simData.doy[maskY].max()

            # there is missing data, only if last day of year is considered
            if doyEnd == 366:
                # prepare
                doyStart = simData.doy[maskY].min()
                # random weights for inter-/extrapolation
                w = np.random.random(2)
                w /= w.sum()

                # two cases:
                # 1. Start before leap -> interpolate leap
                # 2. Start after leap -> extrapolate end pf year
                if doyStart < DOY_LEAPDAY:
                    # move data beginning from leap day
                    mask_new = maskY & ((simData.doy >= DOY_LEAPDAY+1) &
                                        (simData.doy <= 366))
                    mask_old = maskY & ((simData.doy >= DOY_LEAPDAY) &
                                        (simData.doy <= 365))
                    simData.loc[mask_new, ['T', 'Eg']] = simData.loc[mask_old,
                                                                     ['T',
                                                                      'Eg']
                                                                     ].values
                    # interpolate leap day data with surrounding days
                    # leap day has March 1st for know -> add Feb 28th
                    mask_new = maskY & (simData.doy == DOY_LEAPDAY)
                    mask_old = maskY & (simData.doy == DOY_LEAPDAY-1)
                    simData.loc[mask_new, ['T', 'Eg']] = (
                      w[0] * simData.loc[mask_new, ['T', 'Eg']] +
                      w[1] * simData.loc[mask_old, ['T', 'Eg']]).values
                elif doyStart >= DOY_LEAPDAY:
                    # just add missing data to last day of year
                    # since information is missing for time before doyStart,
                    # the last two known days will be extrapolated
                    mask_new = maskY & (simData.doy == 366)
                    mask_old_1 = maskY & (simData.doy == 364)
                    mask_old_2 = maskY & (simData.doy == 365)
                    simData.loc[mask_new, ['T', 'Eg']] = (
                      w[0] * simData.loc[mask_old_1, ['T', 'Eg']] +
                      w[1] * simData.loc[mask_old_2, ['T', 'Eg']]).values

    return simData


def getSimData_df(startDate, endDate, region):
    """ Get all boundary condition data needed for a simulation run

    Args:
        startDate (string): Start date DD.MM.YYYY
                            (start time is hard coded to 00:00)
        endDate (string): End date DD.MM.YYYY
                          (end day is not in time range, so end date
                           should be end date + 1 day)
        region (string): Location of simulation (determines climate / weather)
                         Supported regions:
                            East, West, South, North

    Returns:
        pandas data frame: All simulation data needed
    """
    data = _getSimTime(startDate, endDate)
    data = _addSLPdata(data)
    data = _addHotwater(data)
    data = _getWeather(data, region)
    data = _cleanSimData(data)

    return data


def getSimData(startDate, endDate, region):
    """ Get all boundary condition data needed for a simulation run

    Args:
        startDate (string): Start date DD.MM.YYYY
                            (start time is hard coded to 00:00)
        endDate (string): End date DD.MM.YYYY
                          (end day is not in time range, so end date
                           should be end date + 1 day)
        region (string): Location of simulation (determines climate / weather)
                         Supported regions:
                            East, West, South, North

    Returns:
        int / np float (arrays): nSteps, time, SLP_PHH, SLP_BSLa, SLP_BSLc,
                                 HWP, T, Eg
    """
    data = getSimData_df(startDate, endDate, region)

    return (data.time.size, data.time,
            data.SLP_PHH.to_numpy(dtype=np.float32),
            data.SLP_BSLa.to_numpy(dtype=np.float32),
            data.SLP_BSLc.to_numpy(dtype=np.float32),
            data.HWP_in_W.to_numpy(dtype=np.float32),
            data.loc[:, 'T'].to_numpy(dtype=np.float32),
            data.Eg.to_numpy(dtype=np.float32)
            )
