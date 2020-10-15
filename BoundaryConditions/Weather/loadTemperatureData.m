% load and prepare temperature data
%    - read in data set
%    - get data from reference year
%    - fill up missing data from other years
%    - get data from nearest leap year
%% load data
refYear = 2019;  % year for which the data shall be prioritised

fName = "East";
fLoc = "D:\Downloads\";

opts = detectImportOptions(fLoc + fName);
opts.SelectedVariableNames = {'TT_TU', 'MESS_DATUM'};
opts.VariableTypes{2} = 'char';
dataOrg = readtable(fLoc + fName, opts);

%% add time column
dataOrg.time = datetime(dataOrg.MESS_DATUM, 'InputFormat', 'yyyyMMddHH');

%% generate data output table and fill missing data
data = dataOrg(dataOrg.time.Year == refYear, :);
data.Properties.VariableNames{1} = 'T';
data = removevars(data, {'MESS_DATUM'});

% remove leap day, since it's handled later
data(data.time.Month == 2 & data.time.Day == 29, :) = [];

for year = max(dataOrg.time.Year):-1:min(dataOrg.time.Year)
    if year == refYear
        continue;
    end

    mask = data.T == -999;
    missing = data(mask, :);
    missing.time.Year = year;
    for row = 1:height(missing)
        newDataMask = dataOrg.time == missing.time(row);
        if sum(newDataMask) == 0 
            % dont catch > 1, since it must be investigated individually
            continue;
        end
        missing.T(row) = dataOrg.TT_TU(newDataMask);
    end
    data.T(mask) = missing.T;
    
    if sum(data.T == -999) == 0
        break;
    end
end
%% change time data to day of year, hour and minute
data.doy = day(data.time, 'dayofyear');
data.hour = data.time.Hour;
data.minute = data.time.Minute;
data = removevars(data, {'time'});
% reorder table columns
data = [data(:,2:4), data(:,1)];

%% add nearest leap day
for year = max(dataOrg.time.Year):-1:min(dataOrg.time.Year)
    mask = dataOrg.time.Year == year & dataOrg.time.Month == 2 & ...
           dataOrg.time.Day == 29;
    if sum(mask) > 0
       leapDay = dataOrg(mask, :);
    end
end

% fill missing data
for year = max(dataOrg.time.Year):-1:min(dataOrg.time.Year)
    mask = leapDay.TT_TU == -999;
    if sum(mask) == 0
        break;
    end
    
    if year == leapDay.time.Year
       if year ~= refYear
          % just look one week in past and ahead
          for diffDay = 1:7
              replacementData = dataOrg.TT_TU(dataOrg.time.Year == year & ...
                                              dataOrg.time.Month == 2 & ...
                                              dataOrg.time.Day == (29 - diffDay));
              leapDay.TT_TU(mask) = replacementData(mask);
              mask = leapDay.TT_TU == -999;
              if sum(mask) == 0
                  break;
              end
              replacementData = dataOrg.TT_TU(dataOrg.time.Year == year & ...
                                              dataOrg.time.Month == 3 & ...
                                              dataOrg.time.Day == diffDay);
              leapDay.TT_TU(mask) = replacementData(mask);
          end
       end
    else
        % only if year had leap day
        maskLeapDay = dataOrg.time.Year == year & ...
                      dataOrg.time.Month == 2 & ...
                      dataOrg.time.Day == 29;
        if sum(maskLeapDay) > 0
            replacementData = dataOrg.TT_TU(maskLeapDay);
            leapDay.TT_TU(mask) = replacementData(mask);
        end   
        if year ~= refYear % only use data of other days if not ref. year
            for diffDay = 1:7
                replacementData = dataOrg.TT_TU(dataOrg.time.Year == year & ...
                                                dataOrg.time.Month == 2 & ...
                                                dataOrg.time.Day == (29 - diffDay));
                leapDay.TT_TU(mask) = replacementData(mask);
                mask = leapDay.TT_TU == -999;
                if sum(mask) == 0
                  break;
                end
                replacementData = dataOrg.TT_TU(dataOrg.time.Year == year & ...
                                                dataOrg.time.Month == 3 & ...
                                                dataOrg.time.Day == diffDay);
                leapDay.TT_TU(mask) = replacementData(mask);
            end
        end
    end
end

% change time and order
leapDay.doy = zeros(height(leapDay), 1);
leapDay.hour = leapDay.time.Hour;
leapDay.minute = leapDay.time.Minute;
leapDay.T = leapDay.TT_TU;
leapDay = removevars(leapDay, {'MESS_DATUM', 'time', 'TT_TU'});

% merge
data = [leapDay; data];

%% interpolate in 15min steps
% use year with leap day for interpolation
startDate = datetime(2020, 1, 1, 0, 0, 0);
endDate = datetime(2020, 12, 31, 23, 45, 0);
t = startDate:hours(1):endDate;
T = [data.T(data.doy > 0 & data.doy < 60); ... % before leap day
     data.T(data.doy == 0); ... % leap day
     data.T(data.doy >= 60)]; % after leap day
 
tInterp = startDate:minutes(15):endDate;
TInterp = interp1(t, T, tInterp);
% create new table
dataInterp = table(day(tInterp, 'dayofyear')', tInterp.Hour', ...
                   tInterp.Minute', TInterp', ...
                   'VariableNames', ["doy", "hour", "minute", "T"]);
% move leap day (doy = 60) to doy = 0
dataInterp.doy(dataInterp.doy == 60) = 0;
dataInterp.doy(dataInterp.doy > 60) = dataInterp.doy(dataInterp.doy > 60) - 1;
dataInterp = sortrows(dataInterp, 1);

