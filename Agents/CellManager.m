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
    
    methods(Static)
        function Cell = initDefaultCell(time, nBAgents, nBSLsepAgents, ...
                                        nBuildings, pPHHagents, pAgriculture, ...
                                        pThermal, pPVplants, pBTypes, ...
                                        normSLP, Eg, ToutN, refBuildingData, ...
                                        HotWaterProfilePHH, ...
                                        BSL_COC, PHH_COC, ...
                                        BSL_PV_APDdist, PHH_PV_APDdist)
            %cellManager Create manager for default cell
            %
            %   The default cell consists of the 4 ref. building types free
            %   standong house, row end house as well as smal and big multi
            %   user house. Additionally there are seperate BSL agents
            %   with inherent buildings (the themal load is neglected for
            %   those). The cell composition for agents / buildings can be
            %   adjusted by the proportions accordingly.
            %   For BSL agents located in buildings a phh like thermal
            %   profile is assumed.
            %
            % Inputs:
            %   time - Vector of all time values for simulation as daytime
            %   nBAgents - Number of all Agents in each Building class
            %              [Free Standing, Row End, Small, Big Multi User]
            %              (resulting number can differ slightly due rounding)
            %   nBSLsepAgents - Number of seperate BSL Agents
            %   nBuildings - Number of buildings represented by cell
            %                [Free Standing, Row End, Small, Big Multi User]
            %   pPHHagents - Proportion factor of private household agents
            %                (0 to 1, one number for all building types or
            %                 array with number for each type)
            %   pAgriculture - Factor for propotion of agriculture agents on
            %                  BSL agents (0 to 1)
            %   pThermal - Propotions of buildings with connection to the
            %              district heating network (0 to 1 each)
            %              [Free Standing, Row End, Small, Big Multi User]
            %   pPVplants - Propotion of buildings with PV-Plants (0 to 1)
            %   pBTypes - Structure of proportions for all reference building
            %             types (0 to 1 each, Types: FSH, REH, SAH, BAH)
            %               . class for age classes
            %               . modern for modernisation state
            %               . airMech for enforced air renewal
            %   normSLP - timetable with all normalised load profiles [W]
            %               Columns: PHH, G0, L0
            %   Eg - Mean annual global irradiation for simulated region
            %        [kWh/m^2]
            %   ToutN - Normed outside temperature for specific region
            %           in °C (double)
            %   refBuildingData - Struct with all ref. Building types
            %   HotWaterProfilePHH - Hourly day Profile of hot water demand
            %                        for PHH agents (array of factors - 0 to 1)
            %   BSL_COC - Struct for generating COC values of BSL agents
            %               . function (Distribution)
            %               . min (Min. possible COC factor)
            %               . scale (Max. possible COC factor)
            %   PHH_COC - Struct for generating COC values of PHH agents
            %               . function (Distribution)
            %               . min (Min. possible COC factor)
            %               . scale (Max. possible COC factor)
            %   BSL_PV_APDdist - Distribution for generating PV auxilary
            %                    demand factors of BSL agents
            %   PHH_PV_APDdist - Distribution for generating PV auxilary
            %                    demand factors of PHH agents

            % check probabilities, which are not checekd by agent /
            % building classes
            if min(pPHHagents) < 0 || max(pPHHagents) > 1
               error("pPHHagents must be a number between 0 and 1");
            end
            if pAgriculture < 0 || pAgriculture > 1
               error("pAgriculture must be a number between 0 and 1");
            end
            
            if length(pPHHagents) == 1
                pPHHagents = ones(1, 4) * pPHHagents; 
            elseif length(pPHHagents) ~= 4
                error("Length of pPHHagents must be 1 or 4");
            end
            
            % free standing houses %
            %----------------------%
            PHHfree = AgentManager(time, round(nBAgents(1)*pPHHagents(1)), ...
                                   PHH_COC.function, PHH_COC.min, ...
                                   PHH_COC.scale, normSLP.PHH, ...
                                   HotWaterProfilePHH);
            pBSL = 1 - pPHHagents(1);
            BSLaFree = AgentManager(time, round(nBAgents(1)*pBSL*...
                                                pAgriculture), ...
                                    BSL_COC.function, BSL_COC.min, ...
                                    BSL_COC.scale, normSLP.L0, ...
                                    HotWaterProfilePHH);
            BSLcFree = AgentManager(time, round(nBAgents(1)*pBSL*...
                                               (1-pAgriculture)), ...
                                    BSL_COC.function, BSL_COC.min, ...
                                    BSL_COC.scale, normSLP.G0, ...
                                    HotWaterProfilePHH);
            FSH = SUBmanager(nBuildings(1), pThermal(1), pPVplants, Eg, ...
                             PHH_PV_APDdist, BSL_PV_APDdist, ...
                             pBTypes.FSH.pBClass, pBTypes.FSH.pBModern, ...
                             pBTypes.FSH.pBAirMech, ...
                             refBuildingData.FSH, ToutN, ...
                             PHHfree, BSLaFree, BSLcFree);
            % row end houses %
            %----------------%
            PHHre = AgentManager(time, round(nBAgents(2)*pPHHagents(2)), ...
                                 PHH_COC.function, PHH_COC.min, ...
                                 PHH_COC.scale, normSLP.PHH, ...
                                 HotWaterProfilePHH);
            pBSL = 1 - pPHHagents(2);
            BSLaRE = AgentManager(time, round(nBAgents(2)*pBSL*...
                                              pAgriculture), ...
                                  BSL_COC.function, BSL_COC.min, ...
                                  BSL_COC.scale, normSLP.L0, ...
                                  HotWaterProfilePHH);
           BSLcRE = AgentManager(time, round(nBAgents(2)*pBSL*...
                                             (1-pAgriculture)), ...
                                 BSL_COC.function, BSL_COC.min, ...
                                 BSL_COC.scale, normSLP.G0, ...
                                 HotWaterProfilePHH);
           REH = SUBmanager(nBuildings(2), pThermal(2), pPVplants, Eg, ...
                            PHH_PV_APDdist, BSL_PV_APDdist, ...
                            pBTypes.REH.pBClass, pBTypes.REH.pBModern, ...
                            pBTypes.REH.pBAirMech, ...
                            refBuildingData.REH, ToutN, ...
                            PHHre, BSLaRE, BSLcRE);
           % small apartment houses %
           %------------------------%
           PHHsah = AgentManager(time, round(nBAgents(3)*pPHHagents(3)), ...
                                 PHH_COC.function, PHH_COC.min, ...
                                 PHH_COC.scale, normSLP.PHH, ...
                                 HotWaterProfilePHH);
           pBSL = 1 - pPHHagents(3);
           BSLcSAH = AgentManager(time, round(nBAgents(3)*pBSL), ...
                                  BSL_COC.function, BSL_COC.min, ...
                                  BSL_COC.scale, normSLP.G0, ...
                                  HotWaterProfilePHH);
           SAH = MUBmanager(nBuildings(3), 6, pThermal(3), pPVplants, Eg, ...
                            PHH_PV_APDdist, BSL_PV_APDdist, ...
                            pBTypes.SAH.pBClass, pBTypes.SAH.pBModern, ...
                            pBTypes.SAH.pBAirMech, ...
                            refBuildingData.SAH, ToutN, ...
                            PHHsah, BSLcSAH);
           % big apartment houses %
           %----------------------%
           PHHbah = AgentManager(time, round(nBAgents(4)*pPHHagents(4)), ...
                                 PHH_COC.function, PHH_COC.min, ...
                                 PHH_COC.scale, normSLP.PHH, ...
                                 HotWaterProfilePHH);
           pBSL = 1 - pPHHagents(4);
           BSLcBAH = AgentManager(time, round(nBAgents(4)*pBSL), ...
                                  BSL_COC.function, BSL_COC.min, ...
                                  BSL_COC.scale, normSLP.G0, ...
                                  HotWaterProfilePHH);
           BAH = MUBmanager(nBuildings(4), 48, pThermal(4), pPVplants, Eg, ...
                            PHH_PV_APDdist, BSL_PV_APDdist, ...
                            pBTypes.BAH.pBClass, pBTypes.BAH.pBModern, ...
                            pBTypes.BAH.pBAirMech, ...
                            refBuildingData.BAH, ToutN, ...
                            PHHbah, BSLcBAH);                            
           % seperate BSL agents %
           %---------------------%
           BSLsepA = BSLseperateManager(time, round(nBSLsepAgents * ...
                                                    pAgriculture), ...
                                        BSL_COC.function, BSL_COC.min, ...
                                        BSL_COC.scale, normSLP.L0, ...
                                        pPVplants, Eg, BSL_PV_APDdist);
           BSLsepC = BSLseperateManager(time, round(nBSLsepAgents * ...
                                                    (1-pAgriculture)), ...
                                        BSL_COC.function, BSL_COC.min, ...
                                        BSL_COC.scale, normSLP.G0, ...
                                        pPVplants, Eg, BSL_PV_APDdist);
                                    
            % init cell
            Cell = CellManager([FSH, REH], [SAH, BAH], [BSLsepA, BSLsepC]);
        end
    end
end

