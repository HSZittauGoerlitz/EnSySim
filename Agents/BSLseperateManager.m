classdef BSLseperateManager < AgentManager
    %BSLseperateManager Business agents with electrical profile only

    properties
        % Bilance
        %--------
        % resulting Energy load bilance at given time step
        
        currentEnergyBalance_e  % Resulting eeb in current time step [Wh]

        % Load
        %-----
        
        Load_e  % resulting electrical load for each building [W]
        
        % Generation
        %-----------
        
        Generation_e  % resulting electrical generation for each building [W]
        
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
            %   BSL_PV_dist - Distribution for generating PV auxilary
            %                 demand factors of BSL agents

            % init superclass
            self = self@AgentManager(time, nAgents, ...
                                     COC_dist, minCOC, scaleCOC, ...
                                     SLP);
            
            if pPVplants < 0 || pPVplants > 1
                error("pPVplants must be a number between 0 and 1");
            end
            if Eg < 0
               error("Mean annual global irradiation must be a number greater 0"); 
            end    
                                 
            %%%%%%%%%%%%%%%%%%%%
            % Electrical Model %
            %%%%%%%%%%%%%%%%%%%%
            self.Load_e = zeros(1, self.nAgents);
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
            % Reset current Load and Generation
            self.Load_e = self.Load_e * 0;
            self.Generation_e = self.Generation_e * 0;
            
            % Balances
            % Electrical
            % Load
            self.Load_e = self.Load_e + self.LoadProfile_e(timeIdx, :);
            
            % Generation
            self.Generation_e(self.maskPV) = self.Generation_e(self.maskPV) + ...
                                             self.APV .* Eg;
            % Balance
            self.currentEnergyBalance_e = (sum(self.Generation_e) - ...
                                           sum(self.Load_e)) *...
                                           0.25;  % 1/4 hour steps
        end
    end
end

