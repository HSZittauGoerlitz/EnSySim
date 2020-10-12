function globRad = getGlobalRadiation(startDate, endDate, regionProfile)
%getGlobalRadiation Provide curve for global radiation data
%   A global radiation data curve is generated for a given time period and
%   a characteristic profile for a specific region. The caracteristic data
%   is modified by an uniformly distributed random number in range from 0.8
%   to 1.2.
%
% Inputs:
%   startDate - First date of SLP curve, complete day is considered (datetime)
%   endDate   - Last date of SLP curve, complete day is considered (datetime)
%   regionProfile - Standard global radiation data table [W/m^2] with
%                   yearless time information (columns: doy, hour, minute).
%                   Leap day data is stored in doy=0 rows, doy=1 is equal
%                   to first january and doy=365 to last december of a year.

    %%%%%%%%%%%%%%%%%%%%%%%%%
    % Create glob rad curve %
    %%%%%%%%%%%%%%%%%%%%%%%%%
    % leap day is 60th day of a leap year
    time = getTime(startDate, endDate);
    globRad = table(time', zeros(length(time), 1), ...
                    'VariableNames', ["time", "Eg"]);
    % Split up Eg data generation into linked doy sequences
    doy = day(globRad.time, 'dayofyear');
    for year = min(globRad.time.Year):max(globRad.time.Year)
        maskY = globRad.time.Year == year;
        if day(datetime(year, 12, 31), 'dayofyear') == 365  % no leap year
            % get indices in region profile
            dayStart = min(doy(maskY));
            idxStart = find(regionProfile.doy == dayStart, 1);
            dayStop = max(doy(maskY));
            idxStop = find(regionProfile.doy == dayStop, 1, 'last');
            % fill up data for actual year
            globRad.Eg(maskY) = regionProfile.Eg(idxStart:idxStop);
        else
            % get indices in region profile
            % additional split at leap day
            % all days after leap day must be subtracted by one to fit to
            % region profile doy
            dayStart = min(doy(maskY));
            if dayStart > 60  % no leap day to consider
                dayStart = dayStart - 1;
                idxStart = find(regionProfile.doy == dayStart, 1);
                dayStop = max(doy(maskY)) - 1;
                idxStop = find(regionProfile.doy == dayStop, 1, 'last');
                % fill up data for actual year
                globRad.Eg(maskY) = regionProfile.Eg(idxStart:idxStop);               
            elseif dayStart == 60
                % leap day
                idxStart = find(regionProfile.doy == 0, 1);
                idxStop = find(regionProfile.doy == 0, 1, 'last');
                mask = maskY & ...
                       globRad.time.Month == 2 & globRad.time.Day == 29;
                globRad.Eg(mask) = regionProfile.Eg(idxStart:idxStop);
                % rest
                idxStart = find(regionProfile.doy == dayStart, 1);
                dayStop = max(doy(maskY)) - 1;
                idxStop = find(regionProfile.doy == dayStop, 1, 'last');
                globRad.Eg(maskY) = regionProfile.Eg(idxStart:idxStop);
            else
                % time before leap day, no subtraction necessary
                idxStart = find(regionProfile.doy == dayStart, 1);
                idxStop = find(regionProfile.doy == 59, 1, 'last');
                mask = maskY & ...
                       (globRad.time.Month == 1 | ... 
                        (globRad.time.Month == 2 & globRad.time.Day < 29));
                globRad.Eg(mask) = regionProfile.Eg(idxStart:idxStop);
                % leap day
                idxStart = find(regionProfile.doy == 0, 1);
                idxStop = find(regionProfile.doy == 0, 1, 'last');
                mask = maskY & ...
                       globRad.time.Month == 2 & globRad.time.Day == 29;
                globRad.Eg(mask) = regionProfile.Eg(idxStart:idxStop);
                % rest
                dayStart = 60; % inclusive subtraction
                idxStart = find(regionProfile.doy == dayStart, 1);
                dayStop = max(doy(maskY)) - 1;
                idxStop = find(regionProfile.doy == dayStop, 1, 'last');
                mask = maskY & doy > 60; % exclude 60, since leapday
                globRad.Eg(mask) = regionProfile.Eg(idxStart:idxStop);
            end
        end
    end
    globRad.Eg = globRad.Eg .* (0.8 + rand(height(globRad), 1)*0.4);
end

