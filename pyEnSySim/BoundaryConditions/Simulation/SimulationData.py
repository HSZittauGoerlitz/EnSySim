import numpy as np
import numpy.matlib
import pandas as pd


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
    """ Calculate temperature and irradiation curve for
        given simulation time and region

    The caracteristic data is modified by an uniformly distributed random
    number in range from 0.8 to 1.2.

    Args:
        simData (pandas data frame): Simulation data
        region (string): Location of simulation (determines climate / weather)
                         Supported regions:
                            East, West, South, North

    """
    weatherBC = pd.read_hdf("./BoundaryConditions/Weather/" +
                            region + ".h5", 'Weather')
    # add columns for weather
    simData['T'] = 0.
    simData['Eg'] = 0.

    # Split up Eg data generation into linked doy sequences
    for year in range(simData.time.dt.year.min(),
                      simData.time.dt.year.max()+1):
        maskY = simData.time.dt.year == year
        # for years with leap day
        if simData.time[maskY].dt.is_leap_year.any():
            leapDay = 60
            # first time before leap day, if existing
            minDay = simData.doy[maskY].min()
            if minDay < leapDay:
                # time before
                maskBC = ((weatherBC.doy >= minDay) &
                          (weatherBC.doy <= leapDay-1))
                subMaskY = (maskY &
                            (simData.doy[maskY] >= minDay) &
                            (simData.doy[maskY] < leapDay))
                simData.loc[subMaskY, 'Eg'] = weatherBC.loc[maskBC,
                                                            'Eg'].values
                simData.loc[subMaskY, 'T'] = weatherBC.loc[maskBC, 'T'].values
                # set min day to leapDay
                minDay = leapDay

            # second is leap day
            if minDay == leapDay:
                maskBC = (weatherBC.doy == 0)  # leap day in BC is at doy 0
                subMaskY = (maskY & (simData.doy[maskY] == leapDay))
                simData.loc[subMaskY, 'Eg'] = weatherBC.loc[maskBC,
                                                            'Eg'].values
                simData.loc[subMaskY, 'T'] = weatherBC.loc[maskBC, 'T'].values
                # set min day to one after leapDay
                minDay = leapDay + 1

            # third is time after leap day
            maxDay = simData.doy[maskY].max()
            maskBC = ((weatherBC.doy >= minDay) &
                      (weatherBC.doy <= maxDay))
            subMaskY = (maskY &
                        (simData.doy[maskY] >= minDay) &
                        (simData.doy[maskY] < maxDay))
            simData.loc[subMaskY, 'Eg'] = weatherBC.loc[maskBC,
                                                        'Eg'].values
            simData.loc[subMaskY, 'T'] = weatherBC.loc[maskBC, 'T'].values

        else:  # no leap dy
            # get mask for BC data
            maskBC = ((weatherBC.doy >= simData.doy[maskY].min()) &
                      (weatherBC.doy <= simData.doy[maskY].max()))
            # fill up data for actual year
            # only use values to ignore indices
            simData.loc[maskY, 'Eg'] = weatherBC.loc[maskBC, 'Eg'].values
            simData.loc[maskY, 'T'] = weatherBC.loc[maskBC, 'T'].values

    # add an sligthly randomisation
    simData.loc[:, 'T'] *= (np.random.random(simData.loc[:, 'T'].size) *
                            0.4 + 0.8)
    simData.loc[:, 'Eg'] *= (np.random.random(simData.loc[:, 'T'].size) *
                             0.4 + 0.8)

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
