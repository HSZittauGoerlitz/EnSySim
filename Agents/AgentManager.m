classdef AgentManager < handle
    %AgentManager Definition of the Basic Agent Manager
    
    properties
        % Common Parameter
        
        COCfactor  % Coefficient of Consumer
        nAgents  % Number of Agents in manager
        
        % Load
        
        LoadProfile_e  % Electrical load profile [W]
        LoadProfile_t  % Thermal load profile [W]
        
    end
    
    methods
        function self = AgentManager(time, nAgents, ...
                                     COC_dist, minCOC, scaleCOC, ...
                                     SLP, HotWaterProfile)
            %AgentManager Create object to manage basic agents
            %   The specific agent type is defined by the parameters of the
            %   agent managers constructor.
            %
            % Inputs:
            %   time - Vector of all time values for simulation as daytime
            %   nAgents - Number of Agents
            %   COC_dist - Distribution function used 
            %              for generation of random COC values
            %   minCOC - Min. possible COC factor
            %   scaleCOC - Max. possible COC factor
            %   SLP - Electrical standard load profile over complete 
            %         simulation time [W]
            %   HotWaterProfile - Hourly day Profile of hot water demand,
            %                     starting at hour 0 and ending at hour 23
            %                     (array of factors - 0 to 1)
            
            %%%%%%%%%%%%%%%%%%%%%
            % Common Parameters %
            %%%%%%%%%%%%%%%%%%%%%
            self.nAgents = nAgents;
            % get random coc from given distribution
            self.getCOC(COC_dist, minCOC, scaleCOC);
            %%%%%%%%%%%%%%%%%%%
            % Electrical Load %
            %%%%%%%%%%%%%%%%%%%
            self.LoadProfile_e = SLP .* self.COCfactor .* ...
                                 (0.8 + rand(length(time), self.nAgents));
            %%%%%%%%%%%%%%%%
            % Thermal Load %
            %%%%%%%%%%%%%%%%                            
            self.getHotWaterDemand(time, HotWaterProfile);
        end
                             
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
        
        function self = getHotWaterDemand(self, time, HotWaterProfile)
            %getHotWaterDemand Calculate hot water demand in W
            %   The hot water demand is calculated in relation to the Agents 
            %   COC value. For the calculation a regression model, 
            %   deviated off destatis data, is used.
            %   All load values are modified by a daily profile given in
            %   HotWaterProfile and a random factor between 0.8 and 1.2.
            %
            % Inputs:
            %   time - Vector of all time values for simulation as daytime
            %   HotWaterProfile - Hourly day Profile of hot water demand,
            %                     starting at hour 0 and ending at hour 23
            %                     (array of factors - 0 to 1)
            self.LoadProfile_t = (684.7 * self.COCfactor + 314.4) * ...
                                 1e3 / 8760 ...  % kW -> W; 8760h = 1 year
                                 .* length(time) .* ...
                                 (0.8 + rand(length(time), self.nAgents)) .* ...
                                 HotWaterProfile(time.Hour+1);
        end
    end
end
