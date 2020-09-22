classdef (Abstract) AbstractAgent < handle
    %ABSTRACTAGENT Definition of the Basic Agent structure
    
    properties (Abstract)
        % Common Parameter
        COCfactor
        nAgents
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
        currentEnergyBalance_e  % [Wh]
        currentEnergyBalance_t  % [Wh]
    end
    
    methods (Abstract)
        update(self)
    end
    
    methods
        function self = getCOC(self, COC_dist, minCOC, scaleCOC)
            iter = 0;
            self.COCfactor = zeros(1, self.nAgents);
            while iter < 10
                mask = self.COCfactor < minCOC;
                sumNew = sum(mask);
                if sumNew > 0
                    self.COCfactor(mask) = COC_dist.random([1, sumNew]) * ...
                                           scaleCOC;
                    iter = iter + 1;
                else
                    break;
                end
            end
            mask = self.COCfactor < minCOC;
            self.COCfactor(mask) = minCOC;
        end
    end
end

