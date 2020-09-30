classdef BSLagents < AbstractAgent
    %BSLCONSUMER_E Agents simulationg business with standard load profile

    properties
        % Additional Common
        nG0Agents
        nL0Agents
        startIdxAgri
    end

    methods
        function self = BSLagents(nAgents, pAgriculture, pPVplants, ...
                                  Eg, normSLP, ...
                                  BSL_COC_dist, BSL_PV_dist)
            %BSLagents Create manager for business agents with 
            %          standard load profiles
            %
            % Inputs:
            %   nAgents - Number of Agents
            %   pAgriculture - Proportion factor of agriculture agents (0 to 1)
            %   pPVplants - Propotion of agents with PV-Plants (0 to 1)
            %   Eg - Mean annual global irradiation for simulated region
            %        [kWh/m^2]
            %   normSLP - timetable with all normalised load profiles
            %   BSL_COC_dist - Distribution function for generating 
            %                  COC values of BSL agents
            %   BSL_PV_dist - Distribution for generating PV auxilary
            %                 demand factors of BSL agents
            self.nAgents = nAgents;
            self.nL0Agents = round(self.nAgents * pAgriculture);
            self.nG0Agents = nAgents - self.nL0Agents;
            % get random coc from given distribution
            self.getCOC(BSL_COC_dist, 1, 1);
            self.LoadProfile_e = zeros(height(normSLP), self.nAgents);
            self.LoadProfile_e(:, 1:self.nG0Agents) = normSLP.G0 .* ...
                self.COCfactor(1:self.nG0Agents) .* ...
                (0.8 + rand(height(normSLP), self.nG0Agents));
            self.LoadProfile_e(:, self.nG0Agents+1:end) = normSLP.L0 .* ...
                self.COCfactor(self.nG0Agents+1) .* ...
                (0.8 + rand(height(normSLP), self.nL0Agents));
            % generate selection mask and data for PV generation
            self.maskPV = rand(1, self.nAgents) <= pPVplants;
            self.nPV = sum(self.maskPV);
            self.APV = self.COCfactor(self.maskPV) * 1e3 / Eg .* ...
                       BSL_PV_dist.random(self.nPV) .* ...
                       (rand(1, self.nPV) .* 0.4 + 0.8);
            % init generation array 
            % only for one time step, since it is dynamic
            self.Generation_e = zeros(1, nAgents);
            % deactivate unused properties
            self.LoadProfile_t = [];
            self.Generation_t = [];
            self.Storage_e = [];
            self.Storage_t = [];
            % set thermal Balance to 0
            self.currentEnergyBalance_t = 0;
            self.currentEnergyBalance_e = 0;
        end
    end
end

