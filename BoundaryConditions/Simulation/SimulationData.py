
import numpy as np
import numpy.matlib
import pandas as pd
import pvlib as pv
from math import sin, cos, radians
from scipy.interpolate import interp1d


DOY_LEAPDAY = 60


def _addHotwater(simData):
    """ Calculate hot water demand profile in W
    All load values are modified by a daily profile.
    The profile values have to be scaled by each agents COC value.

    Args:
        simData (pandas data frame): Simulation time and data

    Returns:
        pandas data frame: simData complemented by hot water day profile factor
    """
    # all agents are using PHH profile,
    # since there is no statistic to business hot water demand available
    HWP = pd.read_hdf("./BoundaryConditions/Thermal/HotWaterProfile/"
                      "HotWaterDayProfile.h5", key='PHH')
    simData.insert(simData.shape[1], ('HWPfactor', ''),
                   HWP.loc[simData[('time', '')].dt.hour,
                           'fProportion'].values)

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
    cIdx = [('SLP', 'PHH'), ('SLP', 'BSLa'), ('SLP', 'BSLc')]
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
    newData.loc[mask, [('SLP', 'PHH'), ('SLP', 'BSLc'),
                       ('SLP', 'BSLa')]] = np.tile(
      np.array([PHH.Winter.WorkDay.values,
                G0.Winter.WorkDay.values,
                L0.Winter.WorkDay.values]), nDays).T
    mask = simData.winter & (simData.weekDaySLP == 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, [('SLP', 'PHH'), ('SLP', 'BSLc'),
                       ('SLP', 'BSLa')]] = np.tile(
      np.array([PHH.Winter.Saturday.values,
                G0.Winter.Saturday.values,
                L0.Winter.Saturday.values]), nDays).T
    mask = simData.winter & (simData.weekDaySLP == 6)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, [('SLP', 'PHH'), ('SLP', 'BSLc'),
                       ('SLP', 'BSLa')]] = np.tile(
      np.array([PHH.Winter.Sunday.values,
                G0.Winter.Sunday.values,
                L0.Winter.Sunday.values]), nDays).T
    # Intermediate
    mask = simData.intermediate & (simData.weekDaySLP < 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, [('SLP', 'PHH'), ('SLP', 'BSLc'),
                       ('SLP', 'BSLa')]] = np.tile(
      np.array([PHH.InterimPeriod.WorkDay.values,
                G0.InterimPeriod.WorkDay.values,
                L0.InterimPeriod.WorkDay.values]), nDays).T
    mask = simData.intermediate & (simData.weekDaySLP == 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, [('SLP', 'PHH'), ('SLP', 'BSLc'),
                       ('SLP', 'BSLa')]] = np.tile(
      np.array([PHH.InterimPeriod.Saturday.values,
                G0.InterimPeriod.Saturday.values,
                L0.InterimPeriod.Saturday.values]), nDays).T
    mask = simData.intermediate & (simData.weekDaySLP == 6)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, [('SLP', 'PHH'), ('SLP', 'BSLc'),
                       ('SLP', 'BSLa')]] = np.tile(
      np.array([PHH.InterimPeriod.Sunday.values,
                G0.InterimPeriod.Sunday.values,
                L0.InterimPeriod.Sunday.values]), nDays).T
    # Summer
    mask = simData.summer & (simData.weekDaySLP < 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, [('SLP', 'PHH'), ('SLP', 'BSLc'),
                       ('SLP', 'BSLa')]] = np.tile(
      np.array([PHH.Summer.WorkDay.values,
                G0.Summer.WorkDay.values,
                L0.Summer.WorkDay.values]), nDays).T
    mask = simData.summer & (simData.weekDaySLP == 5)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, [('SLP', 'PHH'), ('SLP', 'BSLc'),
                       ('SLP', 'BSLa')]] = np.tile(
      np.array([PHH.Summer.Saturday.values,
                G0.Summer.Saturday.values,
                L0.Summer.Saturday.values]), nDays).T
    mask = simData.summer & (simData.weekDaySLP == 6)
    nDays = int(mask.sum() / 96)
    newData.loc[mask, [('SLP', 'PHH'), ('SLP', 'BSLc'),
                       ('SLP', 'BSLa')]] = np.tile(
      np.array([PHH.Summer.Sunday.values,
                G0.Summer.Sunday.values,
                L0.Summer.Sunday.values]), nDays).T
    # Dynamic sampling of PHH profile
    newData[('SLP', 'PHH')] *= (- 3.92*1e-10*simData.doy**4 +
                                3.2*1e-7*simData.doy**3 -
                                7.02*1e-5*simData.doy**2 +
                                2.1*1e-3*simData.doy + 1.24)
    # merge data frames
    simData = simData.join(newData.astype(np.float32))

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

    df = pd.DataFrame({('time', ''): time, 'doy': doy,
                       'weekDaySLP': weekDaySLP})
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
    cols = RefWeather.reference.columns

    # at first create simulation weather data without interpolation
    SimWeather = pd.DataFrame(columns=['t [s]'] + cols.to_list())

    # ensure ref Weather time steps are hourly
    if RefWeather.date_time.dt.freq != 'H':
        # TODO: Catch -> Create hourly stepped ref Data
        raise ValueError("Weather data time step must be one hour")

    # Fill sim time in seconds hourly stepped
    SimWeather['time'] = pd.date_range(simData[('time', '')].iloc[0],
                                       simData[('time', '')].iloc[-1],
                                       freq='H')
    SimWeather['doy'] = SimWeather.time.dt.dayofyear
    SimWeather['t [s]'] = ((SimWeather.time - SimWeather.time[0])
                           .dt.total_seconds())
    # get mask of all non leap year days once -> keep out doy 366
    maskDoy = (SimWeather.doy >= 1) & (SimWeather.doy <= 365)

    # one-time create weight function to get smooth transistions
    # between years or december extrapolation
    lenDay = 24  # h -> since ref weather data is hourly stepped
    wDay = np.vstack(np.arange(lenDay-1, -1., -1.) / lenDay)
    wDay = wDay**10
    wDayInv = 1 - wDay

    yearEnd = None

    # Split up Eg data generation into linked doy sequences
    for year in range(SimWeather.time.dt.year.min(),
                      SimWeather.time.dt.year.max()+1):
        # for now ignore the possibility of leap year
        maskY = ((SimWeather.time.dt.year == year) & maskDoy)
        # get start and end Idx for current year
        doyStart = SimWeather.doy[(SimWeather.time.dt.year == year).idxmax()]
        startY = (RefWeather.doy == doyStart).idxmax()
        endY = startY + maskY.sum()-1

        # get weighting factors
        w = np.random.random(3)
        w /= w.sum()  # sum of all factors must be 1

        # Calculate simulation data
        SimWeather.loc[maskY, cols] = (
          RefWeather.reference.loc[startY:endY, cols]*w[0] +
          RefWeather.winter_extreme.loc[startY:endY, cols]*w[1] +
          RefWeather.summer_extreme.loc[startY:endY, cols]*w[2]
          ).values

        # get smooth transition if there is a year before
        if yearEnd is not None:
            mask_new = maskY & (SimWeather.doy == 1)
            SimWeather.loc[mask_new, cols] = (
                    wDay * yearEnd +
                    wDayInv * SimWeather.loc[maskY, cols].values[:lenDay])

        # leap day treatment
        if SimWeather.time[maskY].dt.is_leap_year.any():
            # update year mask
            maskY = SimWeather.time.dt.year == year
            # handle different cases
            doyEnd = SimWeather.doy[maskY].max()

            # there is missing data, only if last day of year is considered
            if doyEnd == 366:
                # prepare
                doyStart = SimWeather.doy[maskY].min()
                # random weights for inter-/extrapolation
                w = np.random.random(2)
                w /= w.sum()

                # two cases:
                # 1. Start before leap -> interpolate leap
                # 2. Start after leap -> extrapolate end pf year
                if doyStart < DOY_LEAPDAY:
                    # move data beginning from leap day
                    mask_new = maskY & ((SimWeather.doy >= DOY_LEAPDAY+1) &
                                        (SimWeather.doy <= 366))
                    mask_old = maskY & ((SimWeather.doy >= DOY_LEAPDAY) &
                                        (SimWeather.doy <= 365))
                    SimWeather.loc[mask_new, cols] = (
                        SimWeather.loc[mask_old, cols].values)
                    # interpolate leap day data with surrounding days
                    # leap day has March 1st for know -> add Feb 28th
                    mask_new = maskY & (SimWeather.doy == DOY_LEAPDAY)
                    mask_old = maskY & (SimWeather.doy == DOY_LEAPDAY-1)
                    New = (w[0] * SimWeather.loc[mask_new, cols].values +
                           w[1] * SimWeather.loc[mask_old, cols].values)
                    Last = SimWeather.loc[mask_old, cols].values[-1]
                    # first transition
                    SimWeather.loc[mask_new, cols] = (wDay*Last + wDayInv*New)
                    # second transition -> new is now old
                    mask_old = maskY & (SimWeather.doy == DOY_LEAPDAY+1)
                    New = SimWeather.loc[mask_old, cols].values[-1]
                    Last = SimWeather.loc[mask_new, cols].values
                    SimWeather.loc[mask_old, cols] = (wDayInv*Last + wDay*New)
                else:
                    # just add missing data to last day of year
                    # since information is missing
                    # for time before doyStart,
                    # the last two known days will be extrapolated
                    mask_new = maskY & (SimWeather.doy == 366)
                    mask_old_1 = maskY & (SimWeather.doy == 364)
                    mask_old_2 = maskY & (SimWeather.doy == 365)
                    # scale new temperature in relation to
                    # last temperature of day before
                    Last = SimWeather.loc[mask_old_2, cols].values[-1]
                    New = (w[0] * SimWeather.loc[mask_old_1, cols].values +
                           w[1] * SimWeather.loc[mask_old_2, cols].values)
                    SimWeather.loc[mask_new, cols] = (wDay*Last + wDayInv*New)
        # set year Flag
        yearEnd = SimWeather.loc[maskY, cols].values[-1]

    # go threw simulated weather data and interpolate it for simData
    simTime = (simData[('time', '')] -
               simData[('time', '')][0]).dt.total_seconds()
    for col in cols:
        fWeather = interp1d(SimWeather['t [s]'], SimWeather[col], 'linear',
                            bounds_error=False, fill_value='extrapolate')
        simData[('Weather', col)] = fWeather(simTime).astype(np.float32)

    return simData


def _getSolarPosition(simData, latitude, longitude):
    """ Get position of sun from time and location
    Args:
        simData (pandas data frame): Simulation data
        latitude (float): Latitude in decimal degrees. Positive north of
                          equator, negative to south
        longitude (float): Longitude in decimal degrees. Positive east of
                           prime meridian, negative to west

    Returns:
        pandas data frame: Data frame with sim data

    """
    # TODO: calculation assumes UTC-time if not localized
    solarPosition = pv.solarposition.get_solarposition(
                                   simData[('time', '')],
                                   latitude,
                                   longitude
                               )

    simData[('SolarPosition',
             'elevation [degree]')] = solarPosition.elevation.values
    simData[('SolarPosition',
             'azimuth [degree]')] = solarPosition.azimuth.values

    return simData


# def _getSolarIrradiationWindows(simData):
#     """ Get irradiation on vertial faces in east/south/west/nord orientation
#         Result is area specific (W/m²)
#     Args:
#         simData (pandas data frame): Simulation data, solar position and
#         irradiance values (direct & diffuse)
#     Returns:
#         pandas data frame: Data frame with sim data
#     """
#     # # south, west, north, east
#     orientations = [0, 90, 180, 270]
#       # remember: for azimuth north is 0°!

#     for orientation in orientations:

#         # direct irradiation
#         I_b = simData[('Weather', 'E direct [W/m^2]')]
#         # elevation
#         h = simData[('SolarPosition', 'elevation [degree]')].apply(radians)
#         # tilt to horizontal
#         tilt = radians(90)
#         # azimuth
#         gamma = simData[('SolarPosition', 'azimuth [degree]')].apply(radians)

#         col_name = 'irradiance_' + str(orientation) + ' [W/m^2]'

#         simData[('Weather', col_name)] = I_b / h.apply(sin) * (h.apply(sin) * cos(tilt) +
#                                             h.apply(cos) * (orientation -
#                                             gamma).apply(cos) * sin(tilt))

#     return simData


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

    # Mittelpunkt Deutschland
    latitude = 51.164305
    longitude = 10.4541205
    data = _getSolarPosition(data, latitude, longitude)
    #data = _getSolarIrradiationWindows(data)
    data = _cleanSimData(data)

    data.columns = pd.MultiIndex.from_tuples(data.columns)

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
            data.SLP,
            data.HWPfactor.to_numpy(dtype=np.float32),
            data.Weather
            )
