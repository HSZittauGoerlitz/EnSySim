function out = getPHH_SLP(startDate, endDate)
%GETPHH_SLP Provide standard load profile for PHH agent
%   The SLP is calculatet for the time frame beginning at startDate and
%   ending at endDate (inclusive). For each day a curve with 15min steps is
%   calculated, based on the SLP PHH data from BDEW. The SLP differes
%   betwenn Summer, Winter, intermediate periods and Weekdays, Weekend,
%   Holydays as well. Additionally the BDEW dynamisation function is used
%   and each quarter of an hour value is ranomised in range of 0.8 to 1.2.
%
% Inputs:
%   startDate - First date of SLP curve (datetime)
%   endDate   - Last date of SLP curve (datetime)
    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Input paramter handling %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    p = inputParser;
    addRequired(p, 'startDate', @isdatetime);
    addRequired(p, 'endDate', @isdatetime);
    
    % Validate inputs
    if startDate >= endDate
       error("endDate must be after startDate"); 
    end
    
    % get time values
    time = startDate:minutes(15):endDate;
    % masks for selection of characteristic periods
    maskWinter = time.Month >= 11 | time.Month < 3 | ...
                 (time.Month == 3 & time.Day <= 20);
    maskSummer = time.Month > 5 & time.Month < 9 | ...
                 (time.Month == 5 & time.Day >= 15) | ...
                 (time.Month == 9 & time.Day <= 14);
    maskIntermediate = ~(maskWinter | maskSummer);
    % get masks for week days
    % 1 Sunday; % 2 Monday; % 3 Tuesday; % 4 Wednesday;
    % 5 Thursday; % 6 Friday; % 7 Saturday
    days = weekday(time);
    maskWeek = days > 1 & days < 7;
    maskSat = days == 7;
    maskSun = days == 1;
    % add Christmas Eve and New Years Eve to Sat if Week
    idxCE = find(time.Month == 12 & time.Day == 24);
    idxNYE = find(time.Month == 12 & time.Day == 31);
    if maskWeek(idxCE(1))
        maskWeek(idxCE) = false;
        maskSat(idxCE) = true;
        % if CE is on week day NYE is also
        maskWeek(idxNYE) = false;
        maskSat(idxNYE) = true;
    end
    

end

