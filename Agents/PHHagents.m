classdef PHHagents < AbstractAgent
    %PHHCONSUMER_E Agents simulationg private househoulds

    properties
        % Common
        COCfactor
        nAgents
        % Load
        LoadProfile_e
        LoadProfile_t
        % Generation
        Generation_e
        Generation_t
        nPV
        APV  % PV area in m^2
        % Storage
        Storage_e
        Storage_t
        % Results
        staticEnergyBalance_e
        currentEnergyBalance_e
        currentEnergyBalance_t
        % selection masks
        maskPV
        
    end

    methods
        function self = PHHagents(nAgents, pPVplants, normSLP, ...
                                  Eg, ...
                                  PHH_COC_dist, PHH_PV_dist, BSL_PV_dist)
            self.nAgents = nAgents;
            % get random coc from given distribution
            self.getCOC(PHH_COC_dist, 1, 5);
            self.LoadProfile_e = normSLP.PHH .* self.COCfactor .* ...
                                 (0.8 + rand(height(normSLP), self.nAgents));
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
            % get static electrical bilance
            self.staticEnergyBalance_e = self.LoadProfile_e * 0.25;
            self.currentEnergyBalance_e = 0;
        end

        function self = update(self, timeIdx, Eg)
            self.Generation_e(self.maskPV) = self.APV * Eg * 0.25;
            self.currentEnergyBalance_e = sum(self.staticEnergyBalance_e(timeIdx, :) - ...
                                              self.Generation_e);
        end
    end
end

