classdef (Abstract) AbstractAgent
    %ABSTRACTAGENT Definition of the Basic Agent structure
    
    properties (Abstract)
        % Common Parameter
        COCfactor
        % Load
        LoadProfile_e
        LoadProfile_t
        % Generation
        Generation_e
        Generation_t
        % Storage
        Storage_e
        Storage_t
        % Bilance
        % resulting Load at given time step
        % positive: Energy is consumed
        % negative: Energy is generated
        currentLoad_e  
        cuurentLoad_t
    end
    
    methods (Abstract)
        update(self)
    end
end

