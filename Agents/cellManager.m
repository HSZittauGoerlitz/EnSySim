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
                                    pAgriculture, ...
                                    pPVplants, ...
                                    normSLP, ...
                                    Eg, ...
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
            %   pPVplants - Propotion of agents with PV-Plants (0 to 1)
            %   normSLP - timetable with all normalised load profiles
            %   Eg - Mean annual global irradiation for simulated region
            %        [kWh/m^2]
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
                error("pBSLagents must be a number between 0 and 1!");
            end
            if pPHHagents < 0 || pPHHagents > 1
                error("pPHHagents must be a number between 0 and 1!");
            end
            if pBSLagents + pPHHagents ~= 1
                error("Sum of propotions for PHH and BSL agents must be equal to 1!");
            end
            if pPVplants < 0 || pPVplants > 1
                error("pProsumer must be a number between 0 and 1!");
            end
            if pAgriculture < 0 || pAgriculture > 1
               error("pAgriculture must be a number between 0 and 1!");
            end
            % calculate agent numbers                    
            self.nBSLagents= round(nAgents * pBSLagents);
            self.nPHHagents = round(nAgents * pPHHagents);
            % initialise agent managers
            self.BSLagents = BSLagents(self.nBSLagents, ...
                                       pAgriculture, pPVplants, ...
                                       Eg, normSLP, ...
                                       BSL_COC_distribution, BSL_PV_APDdist);
            self.PHHagents = PHHagents(self.nPHHagents, pPVplants,...
                                       Eg, normSLP, ...
                                       PHH_COC_distribution, ...
                                       PHH_PV_APDdist, BSL_PV_APDdist);
            self.currentEnergyBalance_e = 0;
        end

        function self = update(self, timeIdx, Eg)
            self.BSLagents.update(timeIdx, Eg);
            self.PHHagents.update(timeIdx, Eg);
            self.currentEnergyBalance_e = self.BSLagents.currentEnergyBalance_e + ...
                                          self.PHHagents.currentEnergyBalance_e;
        end
    end
end

