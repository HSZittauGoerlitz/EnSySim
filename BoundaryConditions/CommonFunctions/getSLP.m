function SLP = getSLP(SLPdata, time, ...
                      maskWinter, maskIntermediate, maskSummer, ...
                      maskWeek, maskSat, maskSun)
%getSLP Calculate SLP-Timetable of for given time and SLP data
%   Create SLP curve for given time period, selection masks and SLPdata
%   (households or commercial / agricultural).
% Inputs:
%   SLPdata - Table with static SLP data for all periods / weekdays
%   time   - Array of datetime with time period for which the SLP profile
%            shall be generated
%   maskWinter - Array of bool for selecting Winter days in time array
%   maskIntermediate - Array of bool for selecting Intermediate days in time array
%   maskSummer - Array of bool for selecting Summer days in time array
%   maskWeek - Array of bool for selecting Week days in time array
%   maskSat - Array of bool for selecting Saturdays in time array
%   maskSun - Array of bool for selecting Sundays in time array
    % create table
    SLP = timetable(time', zeros([length(time), 1]), 'VariableNames', "load");
    % winter
    tempMask = maskWinter & maskWeek;
    nDays = sum(tempMask) / 96;
    SLP.load(tempMask) = repmat(SLPdata.Winter.WorkDay, [nDays, 1]);
    tempMask = maskWinter & maskSat;
    nDays = sum(tempMask) / 96;
    SLP.load(tempMask) = repmat(SLPdata.Winter.Saturday, [nDays, 1]);
    tempMask = maskWinter & maskSun;
    nDays = sum(tempMask) / 96;
    SLP.load(tempMask) = repmat(SLPdata.Winter.Sunday, [nDays, 1]);
    % intermediate
    tempMask = maskIntermediate & maskWeek;
    nDays = sum(tempMask) / 96;
    SLP.load(tempMask) = repmat(SLPdata.InterimPeriod.WorkDay, [nDays, 1]);
    tempMask = maskIntermediate & maskSat;
    nDays = sum(tempMask) / 96;
    SLP.load(tempMask) = repmat(SLPdata.InterimPeriod.Saturday, [nDays, 1]);
    tempMask = maskIntermediate & maskSun;
    nDays = sum(tempMask) / 96;
    SLP.load(tempMask) = repmat(SLPdata.InterimPeriod.Sunday, [nDays, 1]);    
    % summer
    tempMask = maskSummer & maskWeek;
    nDays = sum(tempMask) / 96;
    SLP.load(tempMask) = repmat(SLPdata.Summer.WorkDay, [nDays, 1]);
    tempMask = maskSummer & maskSat;
    nDays = sum(tempMask) / 96;
    SLP.load(tempMask) = repmat(SLPdata.Summer.Saturday, [nDays, 1]);
    tempMask = maskSummer & maskSun;
    nDays = sum(tempMask) / 96;
    SLP.load(tempMask) = repmat(SLPdata.Summer.Sunday, [nDays, 1]);
end

