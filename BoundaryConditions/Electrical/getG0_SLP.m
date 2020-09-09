function G0_SLP = getG0_SLP(startDate, endDate)
%getG0_SLP Provide standard load profile for business agents (commercial)
%   The SLP is calculatet for the time frame beginning at startDate and
%   ending at endDate (inclusive). For each day a curve with 15min steps is
%   calculated, based on the SLP G0 data from BDEW. The SLP differes
%   between Summer, Winter, intermediate periods and Weekdays, Weekend,
%   Holydays as well.
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
    load('BoundaryConditions.mat', 'SLP_G0');
    G0_SLP = getSLP(SLP_G0, time, ...
                    maskWinter, maskIntermediate, maskSummer, ...
                    maskWeek, maskSat, maskSun);
end

