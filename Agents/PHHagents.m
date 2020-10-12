classdef PHHagents < AbstractAgent
    %PHHCONSUMER_E Agents simulationg private househoulds
    properties
        HotWaterProfile  % Hourly day Profile of hot water demand (factors)
    end
    
    methods
        function self = PHHagents(nAgents, pThermal, pPVplants, ...
                                  pBType, pBClass, pBModern, ...
                                  Eg, normSLP, ...
                                  HotWaterProfile, ...
                                  PHH_COC_dist, PHH_PV_dist, BSL_PV_dist)
            %PHHagents Create manager for private household agents
            %
            % Inputs:
            %   nAgents - Number of Agents
            %   pThermal - Propotion of agents with connection to the
            %              district heating network (0 to 1)
            %   pPVplants - Propotion of agents with PV-Plants (0 to 1)
            %   pBType - Proportions of building types (0 to 1)
            %            [SFH, REH, SAH, BAH]
            %   pBClass - Proportions of building age classes
            %             (0 to 1 each, 
            %              the sum of all proportions must be equal 1)
            %             Class 0: Before 1948
            %             Class 1: 1948 - 1978
            %             Class 2: 1979 - 1994
            %             Class 3: 1995 - 2009
            %             Class 4: new building
            %   pBModern - Proportions of modernised buildings in each class
            %              Each position in PBModern corresponds to the
            %              class in PBClass
            %              Modernised in Class4 means new building with
            %              higher energy standard
            %              (0 to 1 each) 
            %   Eg - Mean annual global irradiation for simulated region
            %        [kWh/m^2]
            %   normSLP - timetable with all normalised load profiles
            %   HotWaterProfile - Hourly day Profile of hot water demand
            %                     (array of factors - 0 to 1)
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
            %%%%%%%%%%%%%%%%%
            % Thermal Model %
            %%%%%%%%%%%%%%%%%
            self.HotWaterProfile = HotWaterProfile;
            self.maskThermal = rand(1, self.nAgents) <= pThermal;
            self.nThermal = sum(self.maskThermal);            
            % static load profile -> hot water demand
            self.LoadProfile_t = getHotWaterDemand(self.COCfactor(...
                                     self.maskThermal)) ;
             
            % deactivate unused properties
            self.Generation_t = [];
            self.Storage_e = [];
            self.Storage_t = [];        
        end
        
        function self = update(self, timeIdx, hour, Eg)
            self = update@AbstractAgent(self, timeIdx, Eg);
            self.currentEnergyBalance_t = ...
                sum(self.LoadProfile_t .* (rand(1, self.nThermal) .* ...
                                           0.4 + 0.8) .* ...
                    self.HotWaterProfile(hour+1) .* ...
                    0.25);
        end
    end
end

