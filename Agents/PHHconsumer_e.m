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
        currentLoad_e
        cuurentLoad_t
    end

    methods
        function self = PHHconsumer_e()
            getCOC();
            self.LoadProfile_e = SLP.PHH * COC .* ...
                                 (0.8 + rand(1, lenght(SLP.PHH)));
            % deactivate unused properties
            self.LoadProfile_t = [];
            self.Generation_e = [];
            self.Generation_t = [];
            self.Storage_e = [];
            self.Storage_t = [];
            self.currentLoad_t = [];
        end

        function getCOC(self)
            iter = 0;
            while iter < 10
                COC = PHH_COC_distribution.random();
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
        
        function update(self, timeStep)
           self.currentLoad_e = self.LoadProfile_e(timeStep) * 0.25;
        end
    end
end

