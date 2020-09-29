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
    leapDay = 60;  % save number of each leap day
    globRad.time = getTime(startDate, endDate);
    globRad.Eg = zeros(height(globRad), 1);
    % Split up Eg data generation into linked doy sequences
    doy = day(globRad.time, 'dayofyear');
    for year = min(globRad.time.Year):max(globRad.time.Year)
        if day(datetime(year, 12, 31)) == 365  % no leap year
            mask = globRad.time.Year == year;
            globRad.Eg(mask) = regionProfile.Eg(mask);
        end
    end
end

