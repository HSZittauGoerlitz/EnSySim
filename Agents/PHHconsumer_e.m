classdef PHHconsumer_e < AbstractAgent
    %PHHCONSUMER_E Agents simulationg private househoulds
    %   This agents have only an electrical consumption

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
    end

    methods
        function self = PHHconsumer_e(nAgents, normSLP, PHH_COC_dist)
            self.nAgents = nAgents;
            % get random coc from given distribution
            self.getCOC(PHH_COC_dist, 1, 5);
            self.LoadProfile_e = normSLP.PHH .* self.COCfactor .* ...
                                 (0.8 + rand(height(normSLP), self.nAgents));
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

