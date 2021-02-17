classdef MUBmanager < AbstractBuildingManager
    %MUBmanager Manager for multi user buildings
    
    properties
        % Common
        %-------
        
        nMaxAgents  % max. possible number of agents
        nUnits  % Number of usable units per house
        
        tempLoad  % Helper for load calculation
        
        % All agents in building manager
        %-------------------------------
        
        PHHagents  % private households
        BSLhhlCagents  % common buisiness with household like profile
        
        % selection masks
        %----------------
        
        maskPHH  % mapping of phh agents and buildings
        maskBSLhhlC  % mapping of BSL hhl common agents and buildings
    end
    
    methods
        function self = MUBmanager(nBuildings, nUnits, ...
                                   pThermal, pCHPplants, pPVplants, Eg, PV_dist, ...
                                   pBClass, pBModern, pBAirMech, refData, ...
                                   ToutN, ...
                                   PHHmanager, BSLhhlCmanager)
            % SUBmanager create manager for single user buildings
            %
            % Inputs:
            %   nBuildings - Number of buildings represented by manager
            %   nUnits - Number of usable units per house
            %   pThermal - Propotion of buildings with connection to the
            %              district heating network (0 to 1)
            %   pCHPplants - Portion of buildings with combined heat and
            %                power generation plants (0 to 1 each)
            %   pPVplants - Propotion of buildings with PV-Plants (0 to 1)
            %   Eg - Mean annual global irradiation for 
            %        simulated region [kWh/m^2]
            %   PV_dist - Distribution for generating PV auxiliary
            %             demand factors of each building
            %             The random function of bsl distribution has a
            %             vector as result
            %   pBClass - Proportions of building age classes
            %             (0 to 1 each, 
            %              the sum of all proportions must be equal 1)
            %             Class 1: Before 1948
            %             Class 2: 1948 - 1978
            %             Class 3: 1979 - 1994
            %             Class 4: 1995 - 2009
            %             Class 5: new building
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
                 
            %%%%%%%%%%%%%%%%%%%%%%%%%%
            % general initialisation %
            %%%%%%%%%%%%%%%%%%%%%%%%%%
            self = self@AbstractBuildingManager(nBuildings, ...
                                                pThermal, pCHPplants, pPVplants, Eg, ...
                                                pBClass, pBModern, ...
                                                pBAirMech, ...
                                                refData, ToutN);
            
            self.nUnits = nUnits;                                
            % set max. agents possible
            self.nMaxAgents = nBuildings * nUnits;
            % check input parameter
            % enough buildings for all agents
            if self.nMaxAgents < PHHmanager.nAgents + BSLhhlCmanager.nAgents
                error("Number of agents must be equal or less than all available units in the buildings");
            end
                                            
            %%%%%%%%%%
            % agents %
            %%%%%%%%%%
            self.PHHagents = PHHmanager;
            self.BSLhhlCagents = BSLhhlCmanager;
                                       
            % map agents to buildings
            self.maskPHH = zeros(1, self.nMaxAgents, 'logical');
            self.maskBSLhhlC = zeros(1, self.nMaxAgents, 'logical');
            idx = randperm(self.nMaxAgents);
            % PHH
            start = 1;
            stop = self.PHHagents.nAgents;
            self.maskPHH(idx(start:stop)) = true;
            % BSL common
            start = stop + 1;
            stop = stop + self.BSLhhlCagents.nAgents;
            self.maskBSLhhlC(idx(start:stop)) = true;
            
            %%%%%%%%%%%%%%%%%%%%
            % Electrical Model %
            %%%%%%%%%%%%%%%%%%%%
            % PV
            %%%%
            % buildings COCs
            BuildingsCOC = zeros(1, self.nBuildings*nUnits);
            BuildingsCOC(self.maskPHH) = self.PHHagents.COCfactor;
            BuildingsCOC(self.maskBSLhhlC) = self.BSLhhlCagents.COCfactor;
            BuildingsCOC = reshape(BuildingsCOC, [nUnits, self.nBuildings]);
            BuildingsCOC = sum(BuildingsCOC, 1);
            % get APV
            self.APV = self.APV .* BuildingsCOC(self.maskPV) .* PV_dist.random(self.nPV);

            % init helper array
            self.tempLoad = zeros(1, self.nBuildings*nUnits);
        end
        
        function self = update(self, timeIdx, Eg, Tout)
            update@AbstractBuildingManager(self, Eg, Tout);
            
            % Balances
            % Electrical
            % Load
            self.tempLoad(self.maskPHH) = self.PHHagents.LoadProfile_e(timeIdx, :);
            self.tempLoad(self.maskBSLhhlC) = self.BSLhhlCagents.LoadProfile_e(timeIdx, :);
            self.Load_e = self.Load_e + sum(reshape(self.tempLoad, ...
                                                    [self.nUnits, self.nBuildings]), ...
                                            1);
            % Generation
            % is calculated by AbstractBuildingManager
            % Balance
            self.currentEnergyBalance_e = (sum(self.Generation_e) - ...
                                           sum(self.Load_e)) *...
                                           0.25;  % 1/4 hour steps
            % Thermal
            % Load
            self.tempLoad(self.maskPHH) = self.PHHagents.LoadProfile_t(timeIdx, :);
            self.tempLoad(self.maskBSLhhlC) = self.BSLhhlCagents.LoadProfile_t(timeIdx, :);
            self.Load_t = self.Load_t + sum(reshape(self.tempLoad, ...
                                                    [self.nUnits, self.nBuildings]), ...
                                            1);
            % Generation
            self.getThermalSelfSupply();
            % Balance
            self.currentEnergyBalance_t = (sum(self.Generation_t) - ...
                                           sum(self.Load_t)) *...
                                           0.25;  % 1/4 hour steps
            
        end
    end
end

