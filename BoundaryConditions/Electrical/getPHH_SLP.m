function PHH_SLP = getPHH_SLP(startDate, endDate)
%getPHH_SLP Provide standard load profile for PHH agents
%   The SLP is calculatet for the time frame beginning at startDate and
%   ending at endDate (inclusive). For each day a curve with 15min steps is
%   calculated, based on the SLP PHH data from BDEW. The SLP differes
%   between Summer, Winter, intermediate periods and Weekdays, Weekend,
%   Holydays as well. Additionaly the profile is modyfied by a dynamic
%   sampling profile.
%
% Inputs:
%   startDate - First date of SLP curve, complete day is considered (datetime)
%   endDate   - Last date of SLP curve, complete day is considered (datetime)
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
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Prepare Time data and selection %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    [time, ...
     maskWinter, maskIntermediate, maskSummer, ...
     maskWeek, maskSat, maskSun] = getTimeAndMasks(startDate, endDate);
    
    %%%%%%%%%%%%%%%%%%%%%%%
    % Create Laod Profile %
    %%%%%%%%%%%%%%%%%%%%%%%
    load('BoundaryConditions.mat', 'SLP_PHH');
    PHH_SLP = getSLP(SLP_PHH, time, ...
                     maskWinter, maskIntermediate, maskSummer, ...
                     maskWeek, maskSat, maskSun);
    % Dynamic sampling of profile
    doy = day(PHH_SLP.Time, 'dayofyear');
    PHH_SLP.load = (- 3.92*1e-10*doy.^4 + 3.2*1e-7*doy.^3 - 7.02*1e-5*doy.^2 ...
                    + 2.1*1e-3*doy + 1.24) .* PHH_SLP.load; 
end

