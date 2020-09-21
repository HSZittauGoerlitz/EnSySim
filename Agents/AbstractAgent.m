classdef (Abstract) AbstractAgent < handle
    %ABSTRACTAGENT Definition of the Basic Agent structure
    
    properties (Abstract)
        % Common Parameter
        COCfactor
        % Load
        LoadProfile_e  % [W]
        LoadProfile_t  % [W]
        % Generation
        Generation_e  % [W]
        Generation_t  % [W]
        % Storage
        Storage_e  % [W]
        Storage_t  % [W]
        % Bilance
        % resulting Energy bilance at given time step
        % positive: Energy is consumed
        % negative: Energy is generated
        currentEnergyBilance_e  % [Wh]
        currentEnergyBilance_t  % [Wh]
    end
    
    methods (Abstract)
        update(self)
    end
end

