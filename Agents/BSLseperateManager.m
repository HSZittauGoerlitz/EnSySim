classdef BSLseperateManager < AgentManager
    %BSLseperateManager Business agents with electrical profile only

    properties
        % Bilance
        %--------
        % resulting Energy load bilance at given time step
        % positive: Energy is consumed
        % negative: Energy is generated
        
        currentEnergyBalance_e  % Resulting eeb in current time step [Wh]
        
        % Generation
        %-----------
        
        Generation_e  % Electrical generation [W]
        nPV  % Number of agents with PV-Plants
        APV  % PV area [m^2]
        
        % Storage
        %--------
        
        Storage_e  % Electrical power from or to storages [W]
        
        % selection masks
        %----------------
        
        maskPV  % Mask for selecting all agents with PV-Plants
    end

    methods
        function self = BSLseperateManager(time, nAgents, ...
                                           COC_dist, minCOC, scaleCOC, SLP, ...
                                           pPVplants, Eg, BSL_PV_dist)
            %BSLseperateManager Create manager for business agents with 
            %                   standard load profiles
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
            %   pPVplants - Propotion of agents with PV-Plants (0 to 1)
            %   Eg - Mean annual global irradiation for simulated region
            %        [kWh/m^2]
            %   normSLP - timetable with all normalised load profiles
            %   BSL_PV_dist - Distribution for generating PV auxilary
            %                 demand factors of BSL agents

            % init superclass
            self = self@AgentManager(time, nAgents, ...
                                     COC_dist, minCOC, scaleCOC, ...
                                     SLP);
            
            %%%%%%%%%%%%%%%%%%%%
            % Electrical Model %
            %%%%%%%%%%%%%%%%%%%%
            self.Generation_e = zeros(1, self.nAgents);
            % PV
            %%%%
            % generate selection mask for PV generation
            self.maskPV = rand(1, self.nAgents) <= pPVplants;
            self.nPV = sum(self.maskPV);
            self.APV = (rand(1, self.nPV) * 0.4 + 0.8) * 1e3 / Eg .* ...
                       self.COCfactor(self.maskPV) .* ... % scale by COC
                       BSL_PV_dist.random(self.nPV); % scale by aux. demand

        end
        
        function self = update(self, timeIdx, Eg)
            self.Generation_e(self.maskPV) = self.APV .* Eg;
            self.currentEnergyBalance_e = ...
                (sum(self.LoadProfile_e(timeIdx, :)) - ...
                 sum(self.Generation_e)) * 0.25;  % 1/4 hour steps
        end
    end
end

