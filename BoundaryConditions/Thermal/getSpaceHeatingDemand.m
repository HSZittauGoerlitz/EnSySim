function E_SHD = getSpaceHeatingDemand(Q_HLN, ToutN, Tout)
%getSpaceHeatingDemand Calculate space heating demand in kW
%   The space heating demand is calculated in relation to outside
%   temperature and a building specific heating load.
%   Based on a linear regression model the mean daily heating power is
%   calculated. The space heating energy demand is determined by
%   multiplicating this power with 24h.
% Inputs:
%   Q_HLN - Normed heat load of building in kW (double)
%   ToutN - Normed outside temperature for specific region in °C (double)
%   Tout - Current (daily mean) outside temperature in °C (double or vector)

    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Input paramter handling %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%
    p = inputParser;
    addRequired(p, 'QsHL', @isnumeric);
    addRequired(p, 'ToutN', @isnumeric);
    addRequired(p, 'Tout', @isnumeric);

    if Q_HLN <= 0
        error('Specific building heat load must be greater than 0.');
    end
    
    nTout = length(Tout);
    if nTout > 1
        E_SHD = zeros(1, nTout);
        mask = Tout < 15;
        E_SHD(mask) = -Q_HLN/(15-ToutN) * (Tout(mask)-ToutN) + Q_HLN;
    else
        if Tout < 15
            E_SHD = -Q_HLN/(15-ToutN) * (Tout-ToutN) + Q_HLN;
        else
            E_SHD = 0;
        end
    end
end

