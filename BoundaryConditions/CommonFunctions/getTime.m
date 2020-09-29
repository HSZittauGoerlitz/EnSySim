function time = getTime(startDate, endDate)
%getTime Create time curve
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
        
    % get time values
    time = startDate:minutes(15):endDate;
end

