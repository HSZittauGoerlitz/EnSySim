function Q_HLN = getBuildingNormHeatingLoad(Ubasement, Uwall, Uroof, ...
                                            Uwindow, Udoor, DeltaU, ...
                                            Abasement, Awall, Aroof, ...
                                            Awindow, Adoor, ...
                                            V, nInfiltration, nVentilation, ...
                                            ToutN)
%getBuildingNormHeatingLoad Calculate normed heating load of a building
%                           
%   The calculation is done in reference to the simplified method 
%   of DIN EN 12831-1:2017-09
%   Modifications / Simplifications:
%       - Consideration of the whole building:
%           o normed room temperature is set to 20°C
%           o temperature matching coefficient is set to 1
%       - Normed air heat losses include infiltration losses
%
% Inputs:
%   Ubasement - U-Value of building basement area [W/(m^2 K)]
%   Uwall - U-Value of building wall area [W/(m^2 K)]
%   Uroof - U-Value of building roof area [W/(m^2 K)]
%   Uwindow - U-Value of building window area [W/(m^2 K)]
%   Udoor - U-Value of building door area [W/(m^2 K)]
%   DeltaU - Flat U-Value for thermal bridges [W/(m^2 K)]
%   Abasement - Building basement area [m^2]
%   Awall - Building wall area [m^2]
%   Aroof - Building roof area [m^2]
%   Awindow - Building window area [m^2]
%   Adoor - Building door area [m^2]
%   V - Building room volume [m^3]
%   nInfiltration - Air renewal rate due infiltration [1/h]
%   nVentilation - Air renewal rate due ventilation [1/h]
%   ToutN - Normed outside temperature for specific region in °C (double)
    % Temperature Difference
    dT = (20 - ToutN);
    % Transmission losses
    PhiT = (Abasement * (Ubasement + DeltaU) + ...
            Awall * (Uwall + DeltaU) + Aroof * (Uroof + DeltaU) + ...
            Awindow * (Uwindow + DeltaU) + Adoor * (Udoor + DeltaU)) * dT;
    % Air renewal losses
    PhiA = V * (nInfiltration + nVentilation) * 0.3378 * dT;
    
    Q_HLN = PhiT + PhiA;
end

