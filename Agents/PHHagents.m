classdef PHHagents < AbstractAgent
    %PHHCONSUMER_E Agents simulationg private househoulds
    properties
    end
    
    methods
        function self = PHHagents(nAgents, pPVplants, pThermal, ...
                                  Eg, normSLP, ...
                                  PHH_COC_dist, PHH_PV_dist, BSL_PV_dist)
            %PHHagents Create manager for private household agents
            %
            % Inputs:
            %   nAgents - Number of Agents
            %   pPVplants - Propotion of agents with PV-Plants (0 to 1)
            %   pThermal - Propotion of agents with connection to the
            %              district heating network (0 to 1)
            %   Eg - Mean annual global irradiation for simulated region
            %        [kWh/m^2]
            %   normSLP - timetable with all normalised load profiles
            %   PHH_COC_dist - Distribution function for generating 
            %                  COC values of PHH agents
            %   PHH_PV_dist - Distribution for generating PV auxilary
            %                 demand factors of PHH agents
            %   BSL_PV_dist - Distribution for generating PV auxilary
            %                 demand factors of BSL agents
            %%%%%%%%%%%%%%%%%%%%%
            % Common Parameters %
            %%%%%%%%%%%%%%%%%%%%%
            self.nAgents = nAgents;
            % get random coc from given distribution
            self.getCOC(PHH_COC_dist, 1, 5);
            % init current balances with 0
            self.currentEnergyBalance_e = 0;
            self.currentEnergyBalance_t = 0;
            %%%%%%%%%%%%%%%%%%%%
            % Electrical Model %
            %%%%%%%%%%%%%%%%%%%%
            % Load
            %%%%%%
            self.LoadProfile_e = normSLP.PHH .* self.COCfactor .* ...
                                 (0.8 + rand(height(normSLP), self.nAgents));
            % get static electrical bilance
            self.staticEnergyBalance_e = self.LoadProfile_e * 0.25;
            % Generation
            %%%%%%%%%%%%
            % init generation array 
            % only for one time step, since it is dynamic
            self.Generation_e = zeros(1, nAgents);
            % PV
            %%%%
            % generate selection mask for PV generation
            self.maskPV = rand(1, self.nAgents) <= pPVplants;
            self.nPV = sum(self.maskPV);
            self.APV = self.COCfactor(self.maskPV) * 1e3 / Eg;
            % temp mask for agents with 30% aux power demand normal dist.
            % (the other agents get the 40% aux power demand distribution)
            maskAD = rand(1, self.nPV) <= 0.7;
            n_maskAD = sum(maskAD);
            self.APV(maskAD) = self.APV(maskAD) .* ...
                               PHH_PV_dist.random(1, n_maskAD) .* ...
                               (rand(1, n_maskAD) .* 0.4 + 0.8);
            maskAD = ~maskAD;               
            n_maskAD = sum(maskAD);
            self.APV(maskAD) = self.APV(maskAD) .* ...
                               BSL_PV_dist.random(n_maskAD) .* ...
                               (rand(1, n_maskAD) .* 0.4 + 0.8);

            % deactivate unused properties
            self.LoadProfile_t = [];
            self.Generation_t = [];
            self.Storage_e = [];
            self.Storage_t = [];        
        end
    end
end

