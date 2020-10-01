function E_SHD = getSpaceHeatingDemand(QsHL, Tout)
%getSpaceHeatingDemand> Calculate space heating demand in kW
%   The space heating demand is calculated in relation to outside
%   temperature and a building specific heating load.
%   Based on a linear regression model the mean daily heating power is
%   calculated. The space heating energy demand is determined by
%   multiplicating this power with 24h.
% Inputs:
%   QsHL - specific heat load of building in kW (double)
%   Tout - daily mean outside temperature in °C (double)
    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Input paramter handling %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    p = inputParser;
    addRequired(p, 'QsHL', @isnumeric);
    addRequired(p, 'Tout', @isnumeric);

    if QsHL <= 0
        error('Specific building heat load must be greater than 0.');
    end

    if Tout < 15
        E_SHD = -QsHL/25 * Tout + 0.6*QsHL;
    else
        E_SHD = 0;
    end
end

