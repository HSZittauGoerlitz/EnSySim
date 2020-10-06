function P_HWD = getHotWaterDemand(COC)
%getHotWaterDemand Calculate hot water demand in W
%   The hot water demand is calculated in relation to the Agents COC value.
%   For the calculation a regression model, deviated off destatis data, is
%   used.
% Inputs:
%   COC - Agents electrical COC factor (double)
    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Input paramter handling %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    p = inputParser;
    addRequired(p, 'COC', @isnumeric);

    if COC < 1
        warning('Only COC Values in range of 1 to 5 are supported. COC is set to one.');
        COC = 1;
    elseif COC > 5
        warning('Only COC Values in range of 1 to 5 are supported. COC is set to five.');
        COC = 5;
    end

    P_HWD = (684.7 * COC + 314.4) * 1e3 / 8760;  % kW -> W; 8760h = 1 year
end

