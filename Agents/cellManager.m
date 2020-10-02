classdef cellManager < handle
    %CELLMANAGER Manages all agent types of his cell
    %   The cellular approach divides the energy system into several energy cells.
    %   According to this approach the energy system of ensysim is build up. The
    %   cell manager agent represents such an energy cell and registers the energy
    %   loads of all agents attached to his cell.

    properties
        % number of specific agents
        % -------------------------
        
        nBSLagents % number of busines agents with SLP
        nPHHagents % number of private household agents
        
        % agent objects
        % -------------
        
        BSLagents % object managing BSL angents
        PHHagents % object managing PHH angents
        
        % resulting balance
        % -----------------
        
        currentEnergyBalance_e % Wh
        currentEnergyBalance_t % Wh
    end

    methods
        function self = cellManager(nAgents, pBSLagents, pPHHagents, ...
                                    pAgriculture, pThermal, ...
                                    pPVplants, pBClass, pBModern, ...
                                    normSLP, ...
                                    Eg, HotWaterProfilePHH, ...
                                    BSL_COC_distribution, PHH_COC_distribution, ...
                                    BSL_PV_APDdist, PHH_PV_APDdist)
            %cellManager Create manager for agents in a specific area (cell)
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
            %             (0 to 1 each)         
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
            % check input parameter
            if nAgents <= 0
                error("Number of agents must be a positive integer value");
            end
            if pBSLagents < 0 || pBSLagents > 1
                error("pBSLagents must be a number between 0 and 1");
            end
            if pPHHagents < 0 || pPHHagents > 1
                error("pPHHagents must be a number between 0 and 1");
            end
            if pBSLagents + pPHHagents ~= 1
                error("Sum of propotions for PHH and BSL agents must be equal to 1");
            end
            if pPVplants < 0 || pPVplants > 1
                error("pProsumer must be a number between 0 and 1");
            end
            if pAgriculture < 0 || pAgriculture > 1
               error("pAgriculture must be a number between 0 and 1");
            end
            if pThermal < 0 || pThermal > 1
               error("pThermal must be a number between 0 and 1");
            end
            if length(HotWaterProfilePHH) ~= 24
                error("The Hot Water profile must have 24 values (Hourly)")
            end
            if min(HotWaterProfilePHH) < 0 || max(HotWaterProfilePHH) > 1
                error("The Hot Water profile factors must be in range from 0 to 1")
            end
            if sum(HotWaterProfilePHH) < 0.995 || sum(HotWaterProfilePHH) > 1.005
                error("The sum of Hot Water profile factors must be 1")
            end
            if length(pBClass) ~= 5
                error("The building class proportions must have 5 values")
            end
            if min(pBClass) < 0 || max(pBClass) > 1
                error("Each building class proportion must be in range from 0 to 1")
            end
            if sum(pBClass) < 0.995 || sum(pBClass) > 1.005
                error("The sum of building class proportions must be 1")
            end
            if length(pBModern) ~= 5
                error("The building modernisation proportions must have 5 values")
            end
            if min(pBModern) < 0 || max(pBModern) > 1
                error("Each building modernisation proportion must be in range from 0 to 1")
            end
            
            % calculate agent numbers                    
            self.nBSLagents= round(nAgents * pBSLagents);
            self.nPHHagents = round(nAgents * pPHHagents);
            % initialise agent managers
            self.BSLagents = BSLagents(self.nBSLagents, ...
                                       pAgriculture, pPVplants, ...
                                       Eg, normSLP, ...
                                       BSL_COC_distribution, BSL_PV_APDdist);
            self.PHHagents = PHHagents(self.nPHHagents, pPVplants, pThermal, ...
                                       Eg, normSLP, HotWaterProfilePHH, ...
                                       PHH_COC_distribution, ...
                                       PHH_PV_APDdist, BSL_PV_APDdist);
            self.currentEnergyBalance_e = 0;
            self.currentEnergyBalance_t = 0;
        end

        function self = update(self, timeIdx, hour, Eg)
            self.BSLagents.update(timeIdx, Eg);
            self.PHHagents.update(timeIdx, hour, Eg);
            self.currentEnergyBalance_e = self.BSLagents.currentEnergyBalance_e + ...
                                          self.PHHagents.currentEnergyBalance_e;
            self.currentEnergyBalance_t = self.PHHagents.currentEnergyBalance_t;
        end
    end
end

