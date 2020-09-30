classdef (Abstract) AbstractAgent < handle
    %ABSTRACTAGENT Definition of the Basic Agent Manager
    %
    % eeb: electrical energy bilance
    % dhn: district heating network
    % teb: thermal energy bilance
    
    properties
        % Common Parameter
        
        COCfactor  % Coefficient of Consumer
        nAgents  % Number of Agents in manager
        nThermal  % Number of Agents with connection to dhn
        
        % Load
        
        LoadProfile_e  % Electrical load profile [W]
        LoadProfile_t  % Thermal load profile [W]
        
        % Generation
        
        Generation_e  % Electrical generation [W]
        Generation_t  % Thermal generation [W]
        nPV  % Number of angents with PV-Plants
        APV  % PV area [m^2]
        
        % Storage
        
        Storage_e  % Electrical power from or to storages [W]
        Storage_t  % Thermal power from or to storages [W]
        
        % Bilance
        % resulting Energy load bilance at given time step
        % positive: Energy is consumed
        % negative: Energy is generated
        
        currentEnergyBalance_e  % Resulting eeb in current time step [Wh]
        currentEnergyBalance_t  % Resulting teb in current time step [Wh]
        
        % selection masks
        
        maskPV  % Mask for selecting all agents with PV-Plants
        maskThermal  % Mask for selecting all agents with connection to dhn
    end
    
    methods
        function self = getCOC(self, COC_dist, minCOC, scaleCOC)
            %getCOC Generate COC factors for all agents
            %
            % Inputs:
            %   COC_dist - Distribution used for random numer generation
            %   minCOC - Min. possible COC factor
            %   scaleCOC - Max. possible COC factor
            iter = 0;
            self.COCfactor = -ones(1, self.nAgents);
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
        
        function self = update(self, timeIdx, Eg)
            self.Generation_e(self.maskPV) = self.APV * Eg * 0.25;
            self.currentEnergyBalance_e = sum(self.LoadProfile_e(timeIdx, :) .* ...
                                              0.25 - self.Generation_e);
        end
        
    end
end

