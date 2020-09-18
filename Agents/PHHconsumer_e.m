classdef PHHconsumer_e < AbstractAgent
    %PHHCONSUMER Agent simulationg an private househould
    %   This agent has only an electrical consumption

    properties
        COCfactor
        LoadProfile_e
        LoadProfile_t
        Generation_e
        Generation_t
        Storage_e
        Storage_t
        currentEnergyBilance_e
        currentEnergyBilance_t
    end

    methods
        function self = PHHconsumer_e(normSLP, PHH_COC_dist)
            self.getCOC(PHH_COC_dist);
            self.LoadProfile_e = normSLP .* self.COCfactor .* ...
                                 (0.8 + rand(1, lenght(normSLP)));
            % deactivate unused properties
            self.LoadProfile_t = [];
            self.Generation_e = [];
            self.Generation_t = [];
            self.Storage_e = [];
            self.Storage_t = [];
            self.currentEnergyBilance_t = [];
        end

        function self = getCOC(self, PHH_COC_dist)
            iter = 0;
            while iter < 10
                COC = PHH_COC_dist.random() * 5;
                if COC >= 1
                    break;
                end
                iter = iter + 1;
            end
            if COC < 1
                self.COCfactor = 1;
            else
                self.COCfactor = COC;
            end
        end
        
        function self = update(self, timeStep)
           self.currentEnergyBilance_e = self.LoadProfile_e(timeStep) * 0.25;
        end
    end
end

