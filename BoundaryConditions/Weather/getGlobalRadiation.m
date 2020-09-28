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
    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Input paramter handling %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    p = inputParser;
    addRequired(p, 'startDate', @isdatetime);
    addRequired(p, 'endDate', @isdatetime);

    % set first day clock to 0:00:00
    startDate.Hour = 0;
    startDate.Minute = 0;
    startDate.Second = 0;
    % set last day clock to 23:45:00
    endDate.Hour = 23;
    endDate.Minute = 45;
    endDate.Second = 0;
    
    % Validate inputs
    if startDate >= endDate
       error("endDate must be after startDate"); 
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%
    % Create glob rad curve %
    %%%%%%%%%%%%%%%%%%%%%%%%%
    leapDay = 60;  % save number of each leap day
    globRad.time = getTime(startDate, endDate);
    % Split up Eg data generation into linked doy sequences
    for year = min(globRad.time.Year):max(globRad.time.Year)
        mask = Entsprechender Jahresabschnitt, beachten doy Korrektur, wenn Schaltjahr
        globRad.Eg(mask) = regionProfile.Eg(mask);
    end
end

