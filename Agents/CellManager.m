classdef CellManager < handle
    %CELLMANAGER Manages all agent types of his cell
    %   The cellular approach divides the energy system into several energy cells.
    %   According to this approach the energy system of ensysim is build up. The
    %   cell manager agent represents such an energy cell and registers the energy
    %   loads of all agents attached to his cell.
    %
    % eeb: electrical energy bilance
    % dhn: district heating network
    % teb: thermal energy bilance

    properties
        % buildings and agents
        % -------------------------
        
        SUBs % List of single user building manager
        MUBs % List of multi user building manager
        BSLsepAgents % List of manager for seperate BSL agents
        
        % resulting balance
        % -----------------
        
        currentEnergyBalance_e % Resulting eeb in current time step [Wh]
        currentEnergyBalance_t % Resulting teb in current time step [Wh]
    end

    methods
        function self = CellManager(SUB, MUB, BSLsepAgents)
        %CellManager Create manager for agents in a specific area (cell)
        %
        % Inputs:
        %   SUB - List of single user building manager
        %   MUB - List of multi user building manager
        %   BSLsepAgents - List of manager for seperate BSL agents
            self.SUBs = SUB;
            self.MUBs = MUB;
            self.BSLsepAgents = BSLsepAgents;
        end
        
        function self = initDefaultCell(nAgents, pBSLagents, pPHHagents, ...
                                    pAgriculture, pThermal, ...
                                    pPVplants, pBType, pBClass, pBModern, ...
                                    normSLP, ...
                                    Eg, HotWaterProfilePHH, ...
                                    BSL_COC_distribution, PHH_COC_distribution, ...
                                    BSL_PV_APDdist, PHH_PV_APDdist)
            %cellManager Create manager for default cell
            %
            % Inputs:
            %   nAgents - Number of all Agents (resulting number can differ
            %             slightly due rounding)
            %   pBSLagents - Proportion factor of busines agents with
            %                standard load profile (0 to 1)
            %   pPHHagents - Proportion factor of private household agents
            %                (0 to 1)
            %   pAgriculture - Factor for propotion of agriculture agents on
            %                  BSL agents (0 to 1)
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
            %   normSLP - timetable with all normalised load profiles
            %   Eg - Mean annual global irradiation for simulated region
            %        [kWh/m^2]
            %   HotWaterProfilePHH - Hourly day Profile of hot water demand
            %                        for PHH agents (array of factors - 0 to 1)
            %   BSL_COC_dist - Distribution function for generating 
            %   BSL_PV_APDdist - Distribution for generating PV auxilary
            %                    demand factors of BSL agents
            %   PHH_PV_APDdist - Distribution for generating PV auxilary
            %                    demand factors of PHH agents

        end

        function self = update(self, timeIdx, Eg, Tout)
            % reset energy balances
            self.currentEnergyBalance_e = 0;
            self.currentEnergyBalance_t = 0;
            % go threw single user buildings
            for sub = self.SUBs
               sub.update(timeIdx, Eg, Tout);
               self.currentEnergyBalance_e = self.currentEnergyBalance_e + ...
                                             sub.currentEnergyBalance_e; 
               self.currentEnergyBalance_t = self.currentEnergyBalance_t + ...
                                             sub.currentEnergyBalance_t;
            end
            % go threw multi user buildings
            for mub = self.MUBs
               mub.update(timeIdx, Eg, Tout);
               self.currentEnergyBalance_e = self.currentEnergyBalance_e + ...
                                             mub.currentEnergyBalance_e; 
               self.currentEnergyBalance_t = self.currentEnergyBalance_t + ...
                                             mub.currentEnergyBalance_t;
            end
            % go threw seperate BSL agents
            for BSLsep = self.BSLsepAgents
               BSLsep.update(timeIdx, Eg);
               self.currentEnergyBalance_e = self.currentEnergyBalance_e + ...
                                             BSLsep.currentEnergyBalance_e; 
            end
        end
    end
end

