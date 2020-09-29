function SLP = getNormSLPs(startDate, endDate)
%getNormSLPs Provide standard load profile for different agents
%   The SLP is calculated for the time frame beginning at startDate 
%   and ending at endDate (inclusive). For each day a curve with 
%   15min steps is calculated, based on the SLP data (H0 for PHH, 
%   G0/L0 for business) from BDEW. The SLP differes between Summer, 
%   Winter, intermediate periods and Weekdays, Weekend, Holydays as well. 
%     The PHH SLP is additionally modyfied according to BDEW 
%   by a dynamic sampling profile.
%
% Inputs:
%   startDate - First date of SLP curve, complete day is considered (datetime)
%   endDate   - Last date of SLP curve, complete day is considered (datetime)  
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Prepare Time data and selection %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    [time, ...
     maskWinter, maskIntermediate, maskSummer, ...
     maskWeek, maskSat, maskSun] = getTimeAndMasks(startDate, endDate);
    
    %%%%%%%%%%%%%%%%%%%%%%%%
    % Create Laod Profiles %
    %%%%%%%%%%%%%%%%%%%%%%%%
    % Load profile data
    load('BoundaryConditions.mat', 'SLP_G0', 'SLP_L0', 'SLP_PHH');
    % create table
    SLP = timetable(time', zeros([length(time), 1]), ...
                    zeros([length(time), 1]), ...
                    zeros([length(time), 1]), ...
                    'VariableNames', ["G0", "L0", "PHH"]);
    % assign loads
    % winter
    tempMask = maskWinter & maskWeek;
    nDays = sum(tempMask) / 96;
    SLP.G0(tempMask) = repmat(SLP_G0.Winter.WorkDay, [nDays, 1]);
    SLP.L0(tempMask) = repmat(SLP_L0.Winter.WorkDay, [nDays, 1]);
    SLP.PHH(tempMask) = repmat(SLP_PHH.Winter.WorkDay, [nDays, 1]);
    tempMask = maskWinter & maskSat;
    nDays = sum(tempMask) / 96;
    SLP.G0(tempMask) = repmat(SLP_G0.Winter.Saturday, [nDays, 1]);
    SLP.L0(tempMask) = repmat(SLP_L0.Winter.Saturday, [nDays, 1]);
    SLP.PHH(tempMask) = repmat(SLP_PHH.Winter.Saturday, [nDays, 1]);
    tempMask = maskWinter & maskSun;
    nDays = sum(tempMask) / 96;
    SLP.G0(tempMask) = repmat(SLP_G0.Winter.Sunday, [nDays, 1]);
    SLP.L0(tempMask) = repmat(SLP_L0.Winter.Sunday, [nDays, 1]);
    SLP.PHH(tempMask) = repmat(SLP_PHH.Winter.Sunday, [nDays, 1]);
    % intermediate
    tempMask = maskIntermediate & maskWeek;
    nDays = sum(tempMask) / 96;
    SLP.G0(tempMask) = repmat(SLP_G0.InterimPeriod.WorkDay, [nDays, 1]);
    SLP.L0(tempMask) = repmat(SLP_L0.InterimPeriod.WorkDay, [nDays, 1]);
    SLP.PHH(tempMask) = repmat(SLP_PHH.InterimPeriod.WorkDay, [nDays, 1]);
    tempMask = maskIntermediate & maskSat;
    nDays = sum(tempMask) / 96;
    SLP.G0(tempMask) = repmat(SLP_G0.InterimPeriod.Saturday, [nDays, 1]);
    SLP.L0(tempMask) = repmat(SLP_L0.InterimPeriod.Saturday, [nDays, 1]);
    SLP.PHH(tempMask) = repmat(SLP_PHH.InterimPeriod.Saturday, [nDays, 1]);
    tempMask = maskIntermediate & maskSun;
    nDays = sum(tempMask) / 96;
    SLP.G0(tempMask) = repmat(SLP_G0.InterimPeriod.Sunday, [nDays, 1]);
    SLP.L0(tempMask) = repmat(SLP_L0.InterimPeriod.Sunday, [nDays, 1]);
    SLP.PHH(tempMask) = repmat(SLP_PHH.InterimPeriod.Sunday, [nDays, 1]);
    % summer
    tempMask = maskSummer & maskWeek;
    nDays = sum(tempMask) / 96;
    SLP.G0(tempMask) = repmat(SLP_G0.Summer.WorkDay, [nDays, 1]);
    SLP.L0(tempMask) = repmat(SLP_L0.Summer.WorkDay, [nDays, 1]);
    SLP.PHH(tempMask) = repmat(SLP_PHH.Summer.WorkDay, [nDays, 1]);
    tempMask = maskSummer & maskSat;
    nDays = sum(tempMask) / 96;
    SLP.G0(tempMask) = repmat(SLP_G0.Summer.Saturday, [nDays, 1]);
    SLP.L0(tempMask) = repmat(SLP_L0.Summer.Saturday, [nDays, 1]);
    SLP.PHH(tempMask) = repmat(SLP_PHH.Summer.Saturday, [nDays, 1]);
    tempMask = maskSummer & maskSun;
    nDays = sum(tempMask) / 96;
    SLP.G0(tempMask) = repmat(SLP_G0.Summer.Sunday, [nDays, 1]);
    SLP.L0(tempMask) = repmat(SLP_L0.Summer.Sunday, [nDays, 1]);
    SLP.PHH(tempMask) = repmat(SLP_PHH.Summer.Sunday, [nDays, 1]);
    
    % Dynamic sampling of PHH profile
    doy = day(SLP.Time, 'dayofyear');
    SLP.PHH = (- 3.92*1e-10*doy.^4 + 3.2*1e-7*doy.^3 - 7.02*1e-5*doy.^2 ...
               + 2.1*1e-3*doy + 1.24) .* SLP.PHH; 
end

