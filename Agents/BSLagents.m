classdef BSLagents < AbstractAgent
    %BSLCONSUMER_E Agents simulationg business with standard load profile

    properties
        COCfactor
        nAgents
        LoadProfile_e
        LoadProfile_t
        Generation_e
        Generation_t
        Storage_e
        Storage_t
        currentEnergyBalance_e
        currentEnergyBalance_t
        % Agent specific properties
        staticEnergyBalance_e
        startIdxAgri
        nG0Agents
        nL0Agents
    end

    methods
        function self = BSLagents(nAgents, pAgriculture, ...
                                  normSLP, BSL_COC_dist)
            %BSLconsumer_e Create manager for business agents with standard
            %   load profiles
            %
            % Inputs:
            %   nAgents - Number of Agents
            %   pAgriculture - Proportion factor of agriculture agents (0 to 1)
            %   normSLP - timetable with all normalised load profiles
            %   BSL_COC_dist - Distribution function for generating 
            %                  COC values of BSL agents
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
            % deactivate unused properties
            self.LoadProfile_t = [];
            self.Generation_e = [];
            self.Generation_t = [];
            self.Storage_e = [];
            self.Storage_t = [];
            % set thermal Balance to 0
            self.currentEnergyBalance_t = 0;
            % get static electrical bilance
            self.staticEnergyBalance_e = sum(self.LoadProfile_e * 0.25, 2);
            self.currentEnergyBalance_e = 0;
        end

        function self = update(self, timeIdx)
           self.currentEnergyBalance_e = self.staticEnergyBalance_e(timeIdx);
        end
    end
end

