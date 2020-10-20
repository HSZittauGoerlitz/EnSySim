classdef MUBmanager < AbstractBuildingManager
    %MUBmanager Manager for multi user buildings
    
    properties
        % Common
        %-------
        nMaxAgents  % max. possible number of agents
        
        
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
                                   pThermal, pPVplants, Eg, PV_dist, ...
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
                 
            %%%%%%%%%%%%%%%%%%%%%%%%%%
            % general initialisation %
            %%%%%%%%%%%%%%%%%%%%%%%%%%
            self = self@AbstractBuildingManager(nBuildings, ...
                                                pThermal, pPVplants, Eg, ...
                                                pBClass, pBModern, ...
                                                pBAirMech, ...
                                                refData, ToutN);
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
        end
        
        function self = update(self, timeIdx, Eg, Tout)
            self.Generation_e(self.maskPV) = self.APV .* Eg;
            self.currentEnergyBalance_e = ...
                (sum(self.PHHagents.LoadProfile_e(timeIdx, :)) + ...
                 sum(self.BSLhhlCagents.LoadProfile_e(timeIdx, :)) - ...
                 sum(self.Generation_e)) * 0.25;  % 1/4 hour steps
            % TODO: add generation_t
            self.getSpaceHeatingDemand(Tout);
            self.currentEnergyBalance_t = ...
                (sum(self.PHHagents.LoadProfile_t(timeIdx, :)) + ...
                 sum(self.BSLhhlCagents.LoadProfile_t(timeIdx, :)) + ...
                 sum(self.currentHeatingLoad) - ...
                 sum(self.Generation_t)) * 0.25;  % 1/4 hour steps
        end

        
    end
end

