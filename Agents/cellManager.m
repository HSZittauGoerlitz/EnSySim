classdef cellManager < handle
    %CELLMANAGER Manages all agent types of his cell
    %   The cellular approach divides the energy system into several energy cells.
    %   According to this approach the energy system of ensysim is build up. The
    %   cell manager agent represents such an energy cell and registers the energy
    %   loads of all agents attached to his cell.

    properties
        % number of specific agents
        % -------------------------
        
        nBSLconsumer_e % number of busines agents with SLP with electric consumption
        nPHHconsumer_e % number of private household agents with electric consumption
        
        % agent objects
        % -------------
        
        BSLconsumer_e % object managing BSL angents with electric consumption
        PHHconsumer_e % object managing PHH angents with electric consumption
        
        % resulting balance
        % -----------------
        
        currentEnergyBalance_e % Wh
        currentEnergyBalance_t % Wh
    end

    methods
        function self = cellManager(nAgents, pBSLagents, pPHHagents, ...
                                    pProsumer, pAgriculture, ...
                                    normSLP, ...
                                    BSL_COC_distribution, PHH_COC_distribution)
            %cellManager Create manager for agents in a specific area (cell)
            %
            % Inputs:
            %   nAgents - Number of all Agents (resulting number can differ
            %             slightly due rounding)
            %   pBSLagents - Proportion factor of busines agents with
            %                standard load profile (0 to 1)
            %   pPHHagents - Proportion factor of private household agents
            %                (0 to 1)
            %   pProsumer - Propotion of Prosumer agents (0 to 1)
            %   pAgriculture - Factor for propotion of agriculture agents on
            %                  BSL agents (0 to 1)
            %   normSLP - timetable with all normalised load profiles
            %   BSL_COC_dist - Distribution function for generating 
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
            if pProsumer < 0 || pProsumer > 1
                error("pProsumer must be a number between 0 and 1!");
            end
            if pAgriculture < 0 || pAgriculture > 1
               error("pAgriculture must be a number between 0 and 1!");
            end
            % calculate agent numbers                    
            self.nBSLconsumer_e = round(nAgents * pBSLagents);
            self.nPHHconsumer_e = round(nAgents * pPHHagents);
            % initialise agent managers
            self.BSLconsumer_e = BSLconsumer_e(self.nBSLconsumer_e, pAgriculture, ...
                                               normSLP, BSL_COC_distribution);
            self.PHHconsumer_e = PHHconsumer_e(self.nPHHconsumer_e, ...
                                               normSLP, PHH_COC_distribution);
            self.currentEnergyBalance_e = 0;
        end

        function self = update(self, timeIdx)
            self.BSLconsumer_e.update(timeIdx);
            self.PHHconsumer_e.update(timeIdx);
            self.currentEnergyBalance_e = self.BSLconsumer_e.currentEnergyBalance_e + ...
                                          self.PHHconsumer_e.currentEnergyBalance_e;
        end
    end
end

