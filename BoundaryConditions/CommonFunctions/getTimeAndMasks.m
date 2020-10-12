function [time, maskWinter, maskIntermediate, maskSummer, ...
          maskWeek, maskSat, maskSun] = getTimeAndMasks(startDate, endDate)
%getTimeAndMasks Create time curve and selection masks for specific periods
%   All SLPs have a common time curve. Since the time values well as the
%   corresponding selection masks are created centralised by this function.
%   In the selection masks the public holidays for Saxony are already
%   considered.
%
% Inputs:
%   startDate - First date of SLP curve, complete day is considered (datetime)
%   endDate   - Last date of SLP curve, complete day is considered (datetime)

    % get time values
    time = getTime(startDate, endDate);
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
    if idxCE
        if maskWeek(idxCE(1))
            maskWeek(idxCE) = false;
            maskSat(idxCE) = true;
            if idxNYE
                % if CE is on week day NYE is also
                maskWeek(idxNYE) = false;
                maskSat(idxNYE) = true;
            end
        end
    end
    % find public holydays and set them to sunday
    load('BoundaryConditions.mat', 'holydaysSN');
    dates = datevec(time);
    dates = datetime(dates(:, 1:3));
    pubHD = ismember(dates, holydaysSN.date);
    maskWeek(pubHD) = false;
    maskSat(pubHD) = false;
    maskSun(pubHD) = true;
end

