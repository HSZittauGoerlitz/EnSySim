% load and prepare global radiation data
%    - read in data set
%    - get data from reference year
%    - fill up missing data from other years
%    - get data from nearest leap year
%% load data
refYear = 2019;  % year for which the data shall be prioritised

fName = "North";
fLoc = "D:\Downloads\";

opts = detectImportOptions(fLoc + fName);
opts.SelectedVariableNames = {'FG_LBERG', 'MESS_DATUM_WOZ'};
dataOrg = readtable(fLoc + fName, opts);

%% add time column
dataOrg.time = datetime(dataOrg.MESS_DATUM_WOZ, 'InputFormat', 'yyyyMMddHH:mm');

%% generate data output table and fill missing data
data = dataOrg(dataOrg.time.Year == refYear, :);
data.Properties.VariableNames{1} = 'Eg';
data = removevars(data, {'MESS_DATUM_WOZ'});

% remove leap day, since it's handled later
data(data.time.Month == 2 & data.time.Day == 29, :) = [];

for year = max(dataOrg.time.Year):-1:min(dataOrg.time.Year)
    if year == refYear
        continue;
    end

    mask = data.Eg == -999;
    missing = data(mask, :);
    missing.time.Year = year;
    for row = 1:height(missing)
        newDataMask = dataOrg.time == missing.time(row);
        if sum(newDataMask) == 0 
            % dont catch > 1, since it must be investigated individually
            continue;
        end
        missing.Eg(row) = dataOrg.FG_LBERG(newDataMask);
    end
    data.Eg(mask) = missing.Eg;
    
    if sum(data.Eg == -999) == 0
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
    mask = leapDay.FG_LBERG == -999;
    if sum(mask) == 0
        break;
    end
    
    if year == leapDay.time.Year
       if year ~= refYear
          % just look one week in past and ahead
          for diffDay = 1:7
              replacementData = dataOrg.FG_LBERG(dataOrg.time.Year == year & ...
                                                 dataOrg.time.Month == 2 & ...
                                                 dataOrg.time.Day == (29 - diffDay));
              leapDay.FG_LBERG(mask) = replacementData(mask);
              mask = leapDay.FG_LBERG == -999;
              if sum(mask) == 0
                  break;
              end
              replacementData = dataOrg.FG_LBERG(dataOrg.time.Year == year & ...
                                                 dataOrg.time.Month == 3 & ...
                                                 dataOrg.time.Day == diffDay);
              leapDay.FG_LBERG(mask) = replacementData(mask);
          end
       end
    else
        % only if year had leap day
        maskLeapDay = dataOrg.time.Year == year & ...
                      dataOrg.time.Month == 2 & ...
                      dataOrg.time.Day == 29;
        if sum(maskLeapDay) > 0
            replacementData = dataOrg.FG_LBERG(maskLeapDay);
            leapDay.FG_LBERG(mask) = replacementData(mask);
        end   
        if year ~= refYear % only use data of other days if not ref. year
            for diffDay = 1:7
                replacementData = dataOrg.FG_LBERG(dataOrg.time.Year == year & ...
                                                   dataOrg.time.Month == 2 & ...
                                                   dataOrg.time.Day == (29 - diffDay));
                leapDay.FG_LBERG(mask) = replacementData(mask);
                mask = leapDay.FG_LBERG == -999;
                if sum(mask) == 0
                  break;
                end
                replacementData = dataOrg.FG_LBERG(dataOrg.time.Year == year & ...
                                                 dataOrg.time.Month == 3 & ...
                                                 dataOrg.time.Day == diffDay);
                leapDay.FG_LBERG(mask) = replacementData(mask);
            end
        end
    end
end

% change time and order
leapDay.doy = zeros(height(leapDay), 1);
leapDay.hour = leapDay.time.Hour;
leapDay.minute = leapDay.time.Minute;
leapDay.Eg = leapDay.FG_LBERG;
leapDay = removevars(leapDay, {'MESS_DATUM_WOZ', 'time', 'FG_LBERG'});

% merge
data = [leapDay; data];

%% interpolate in 15min steps
data.Eg = data.Eg / 3600 * 1e4;  %  J/cm^2 to W/m^2 
data0 = data;
data15 = data;
data30 = data;
data45 = data;
data15.minute = ones(height(data), 1) * 15;
data30.minute = ones(height(data), 1) * 30;
data45.minute = ones(height(data), 1) * 45;
data = [data0; data15; data30; data45];
data = sortrows(data, [1, 2, 3]);