classdef SUBmanager < AbstractBuildingManager
    %SUBmanager Manager for single user buildings
    
    properties
        % All agents in building manager
        %-------------------------------
        
        PHHagents  % private households
        BSLhhlCagents  % common buisiness with household like profile
        BSLhhlAagents  % agricultural buisiness with household like profile
        
        % selection masks
        %----------------
        
        maskPHH  % mapping of phh agents and buildings
        maskBSLhhlC  % mapping of BSL hhl common agents and buildings
        maskBSLhhlA  % mapping of BSL hhl agricultural agents and buildings
    end
    
    methods
        function self = SUBmanager(nBuildings, pThermal, pPVplants, Eg, ...
                                   PHH_PV_dist, BSL_PV_dist, ...
                                   pBClass, pBModern, pBAirMech, refData, ...
                                   ToutN, ...
                                   PHHmanager, BSLhhlCmanager, BSLhhlAmanager)
            % SUBmanager create manager for single user buildings
            %
            % Inputs:
            %   nBuildings - Number of buildings represented by manager
            %   pThermal - Propotion of buildings with connection to the
            %              district heating network (0 to 1)
            %   pPVplants - Propotion of buildings with PV-Plants (0 to 1)
            %   Eg - Mean annual global irradiation for 
            %        simulated region [kWh/m^2]
            %   PHH_PV_dist - Distribution for generating PV auxiliary
            %                 demand factors of PHH agents
            %   BSL_PV_dist - Distribution for generating PV auxiliary
            %                 demand factors of BSL agents
            %                 The random function of bsl distribution has a
            %                 vector as result
            %   pBClass - Proportions of building age classes
            %             (0 to 1 each, 
            %              the sum of all proportions must be equal 1)
            %             Class 0: Before 1948
            %             Class 1: 1948 - 1978
            %             Class 2: 1979 - 1994
            %             Class 3: 1995 - 2009
            %             Class 4: new building
            %   pBModern - Proportions of modernised buildings in each class.
            %              Each position in PBModern corresponds to the
            %              class in PBClass
            %              Modernised in Class4 means new building with
            %              higher energy standard
            %              (0 to 1 each)
            %   pBAirMech - Proportions of buildings with enforced air
            %               renewal. Each position in pBAirMech corresponds 
            %               to the class in PBClass.
            %               (0 to 1 each)
            %   refData - Data of reference Building as Struct
            %             Contents: Geometry, U-Values for each age class
            %                       and modernisation status, air renewal rates
            %             (See ReferenceBuilding of BoundaryConditions for
            %              example)
            %   ToutN - Normed outside temperature for specific region
            %           in °C (double)
            %   PHHmanager - Manager of phh agents
            %   BSLhhlCmanager - Manager of BSL hhl common agents
            %   BSLhhlAmanager - Manager of BSL hhl agricultural agents
            
            % check input parameter
            % enough buildings for all agents
            if nBuildings < PHHmanager.nAgents + BSLhhlCmanager.nAgents + ...
                            BSLhhlAmanager.nAgents    
                error("Number of agents must be equal or less than number of buildings");
            end
            
            %%%%%%%%%%%%%%%%%%%%%%%%%%
            % general initialisation %
            %%%%%%%%%%%%%%%%%%%%%%%%%%
            self = self@AbstractBuildingManager(nBuildings, ...
                                                pThermal, pPVplants, Eg, ...
                                                pBClass, pBModern, ...
                                                pBAirMech, ...
                                                refData, ToutN);
            %%%%%%%%%%
            % agents %
            %%%%%%%%%%
            self.PHHagents = PHHmanager;
            self.BSLhhlCagents = BSLhhlCmanager;
            self.BSLhhlAagents = BSLhhlAmanager;
                                       
            % map agents to buildings
            self.maskPHH = zeros(1, self.nBuildings, 'logical');
            self.maskBSLhhlC = zeros(1, self.nBuildings, 'logical');
            self.maskBSLhhlA = zeros(1, self.nBuildings, 'logical');
            idx = randperm(self.nBuildings);
            % PHH
            start = 1;
            stop = self.PHHagents.nAgents;
            self.maskPHH(idx(start:stop)) = true;
            % BSL common
            start = stop + 1;
            stop = stop + self.BSLhhlCagents.nAgents;
            self.maskBSLhhlC(idx(start:stop)) = true;
            % BSL agricultural
            start = stop + 1;
            stop = stop + self.BSLhhlAagents.nAgents;
            self.maskBSLhhlA(idx(start:stop)) = true;
            
            %%%%%%%%%%%%%%%%%%%%
            % Electrical Model %
            %%%%%%%%%%%%%%%%%%%%
            % PV
            %%%%
            % PHH
            tempMaskAPV = self.maskPHH(self.maskPV);
            self.APV(tempMaskAPV) = self.APV(tempMaskAPV) .* ...
                                    self.PHHagents.COCfactor(...
                                        self.maskPV(self.maskPHH));
            % BSL C
            tempMaskAPV = self.maskBSLhhlC(self.maskPV);
            self.APV(tempMaskAPV) = self.APV(tempMaskAPV) .* ...
                                    self.BSLhhlCagents.COCfactor(...
                                        self.maskPV(self.maskBSLhhlC));
            % BSL A
            tempMaskAPV = self.maskBSLhhlA(self.maskPV);
            self.APV(tempMaskAPV) = self.APV(tempMaskAPV) .* ...
                                    self.BSLhhlAagents.COCfactor(...
                                        self.maskPV(self.maskBSLhhlA));
           % auxilary demand
           % 70% of all phh agents use phh distribution
           % rest of all agents use bsl distribution
           tempMaskAPV = self.maskPHH(self.maskPV) & ...
                                      rand(1, self.nPV) <= 0.7;
           self.APV(tempMaskAPV) = self.APV(tempMaskAPV) .* ...
                                   PHH_PV_dist.random(1, sum(tempMaskAPV));
           % get selection of rest
           tempMaskAPV = ~tempMaskAPV;
           self.APV(tempMaskAPV) = self.APV(tempMaskAPV) .* ...
                                   BSL_PV_dist.random(sum(tempMaskAPV));
        end
        
        function self = update(self, timeIdx, Eg)
            self.Generation_e(self.maskPV) = self.APV * Eg * 0.25;
            self.currentEnergyBalance_e = ...
                (sum(self.PHHagents.LoadProfile_e(timeIdx, :)) + ...
                 sum(self.BSLhhlCagents.LoadProfile_e(timeIdx, :)) + ...
                 sum(self.BSLhhlAagents.LoadProfile_e(timeIdx, :))) * ...
                0.25 - sum(self.Generation_e);
            % TODO: add generation_t
            self.currentEnergyBalance_t = ...
                (sum(self.PHHagents.LoadProfile_t(timeIdx, :)) + ...
                 sum(self.BSLhhlCagents.LoadProfile_t(timeIdx, :)) + ...
                 sum(self.BSLhhlAagents.LoadProfile_t(timeIdx, :))) * ...
                0.25 - sum(self.Generation_t);
        end

        
    end
end

