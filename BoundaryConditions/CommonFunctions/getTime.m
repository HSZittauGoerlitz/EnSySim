function time = getTime(startDate, endDate)
%getTime Create time curve
%
% Inputs:
%   startDate - First date of SLP curve, complete day is considered (datetime)
%   endDate   - Last date of SLP curve, complete day is considered (datetime)
    % get time values
    time = startDate:minutes(15):endDate;
end

