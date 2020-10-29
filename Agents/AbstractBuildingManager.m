classdef (Abstract) AbstractBuildingManager < handle
    %AbstractBuildingManager Basic formulation of a building manager
    %
    % eeb: electrical energy bilance
    % dhn: district heating network
    % teb: thermal energy bilance

        
    properties
        % Common Parameter
        %-----------------
        
        nBuildings  % Number of buildings represented of manager
        nThermal  % Number of builings with connection to dhn
        Q_HLN  % Normed heat load of each building [W]
        ToutN  % Normed outside temperature for region of building [°C]
        
        % Bilance
        %--------
        % resulting Energy load bilance at given time step
        % positive: Energy is consumed
        % negative: Energy is generated
        
        currentEnergyBalance_e  % Resulting eeb in current time step [Wh]
        currentEnergyBalance_t  % Resulting teb in current time step [Wh]

        % Load
        %-----
        
        % Heating load of buildings with connection to dhn or to other
        % energy sector
        currentHeatingLoad  % [W]
        
        % Generation
        %-----------
        
        Generation_e  % Electrical generation [W]
        Generation_t  % Thermal generation [W]
        nPV  % Number of buildings with PV-Plants
        APV  % PV area [m^2]
        
        % Storage
        %--------
        
        Storage_e  % Electrical power from or to storages [W]
        Storage_t  % Thermal power from or to storages [W]


        % selection masks
        %----------------
        
        maskPV  % Mask for selecting all buildings with PV-Plants
        maskThermal  % Mask for selecting all buildings with connection to dhn

    end
    
    methods
        function self = AbstractBuildingManager(nBuildings, pThermal, ...
                                                pPVplants, Eg, ...
                                                pBClass, pBModern, ...
                                                pBAirMech, refData, ...
                                                ToutN)
            %AbstractBuildingManager Create manager for buildings
            %
            % Inputs:
            %   nBuildings - Number of buildings represented by manager
            %   pThermal - Propotion of buildings with connection to the
            %              district heating network (0 to 1)
            %   pPVplants - Propotion of buildings with PV-Plants (0 to 1)
            %   Eg - Mean annual global irradiation for 
            %        simulated region [kWh/m^2]
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
            
            %%%%%%%%%%%%%%%%%%%%%%%%%
            % check input parameter %
            %%%%%%%%%%%%%%%%%%%%%%%%%
            if nBuildings <= 0
                error("Number of buildings must be a positive integer value");
            end
            if pThermal < 0 || pThermal > 1
               error("pThermal must be a number between 0 and 1");
            end
            if pPVplants < 0 || pPVplants > 1
                error("pPVplants must be a number between 0 and 1");
            end
            if Eg < 0
               error("Mean annual global irradiation must be a number greater 0"); 
            end
            nClass = length(pBClass);
            if nClass <= 0
                error("The building class proportions must have min. 1 value")
            end
            if min(pBClass) < 0 || max(pBClass) > 1
                error("Each building class proportion must be in range from 0 to 1")
            end
            if sum(pBClass) < 0.995 || sum(pBClass) > 1.005 % allow slight deviation
                error("The sum of building class proportions must be 1")
            end
            if length(pBModern) ~= nClass
                error("The building modernisation proportions must fit to number of class proportions")
            end
            if min(pBModern) < 0 || max(pBModern) > 1
                error("Each building modernisation proportion must be in range from 0 to 1")
            end
            if length(pBAirMech) ~= nClass
                error("The building air renewing proportions fit to number of class proportions")
            end
            if min(pBAirMech) < 0 || max(pBAirMech) > 1
                error("Each building air renewal proportion must be in range from 0 to 1")
            end
        
            %%%%%%%%%%%%%%%%%%%%%
            % Common Parameters %
            %%%%%%%%%%%%%%%%%%%%%
            self.nBuildings = nBuildings;
            
            %%%%%%%%%%%%%%%%%%%%
            % Electrical Model %
            %%%%%%%%%%%%%%%%%%%%
            self.Generation_e = zeros(1, self.nBuildings);
            % PV
            %%%%
            % generate selection mask for PV generation
            self.maskPV = rand(1, self.nBuildings) <= pPVplants;
            self.nPV = sum(self.maskPV);
            % init PV areas -> final managers have to scale it by COC
            self.APV = (rand(1, self.nPV) * 0.4 + 0.8) * 1e3 / Eg;
            
            %%%%%%%%%%%%%%%%%
            % Thermal Model %
            %%%%%%%%%%%%%%%%%
            self.Generation_t = zeros(1, self.nBuildings);
            % Normed heating load
            %%%%%%%%%%%%%%%%%%%%%
            self.Q_HLN = zeros(1, nBuildings);
            self.ToutN = ToutN;
            % get and init specific buildings
            CA = rand(1, nBuildings); % class arrangement
            pStart = 0.0; % offset of proportions

            for classIdx = 1:length(fieldnames(refData.Uvalues))
                % create local varibles to get all fieldnames needed
                pClass = pBClass(classIdx);
                className = "class_" + num2str(classIdx);
                stateNames = fieldnames(refData.Uvalues.(className));
                newBuildings = ~any(strcmp(stateNames, 'original'));
                
                % get specific buildings
                pEnd = pStart + pClass;
                maskC = CA >= pStart & CA < pEnd;
                % get modernisation status and air renewal method
                maskM = maskC & (rand(1, length(maskC)) <= pBModern(classIdx));
                maskAMech = maskC & (rand(1, length(maskC)) <= pBAirMech(classIdx));
                % get normed heat loads
                % differ stock and new buildings
                if newBuildings
                    % Eff 1
                    % free air renewal
                    self.Q_HLN(maskC & ~maskM & ~maskAMech) = ...
                        self.getBuildingNormHeatingLoad(...
                            refData.Uvalues.(className).Eff1, ...
                            refData.GeometryParameters, ...
                            refData.n.new.Infiltration, ...
                            refData.n.new.VentilationFree);
                    % enforced air renewal
                    self.Q_HLN(maskC & ~maskM & maskAMech) = ...
                        self.getBuildingNormHeatingLoad(...
                            refData.Uvalues.(className).Eff1, ...
                            refData.GeometryParameters, ...
                            refData.n.new.Infiltration, ...
                            refData.n.new.VentilationMech);
                    % Eff 2
                    % free air renewal
                    self.Q_HLN(maskC & maskM & ~maskAMech) = ...
                        self.getBuildingNormHeatingLoad(...
                            refData.Uvalues.(className).Eff2, ...
                            refData.GeometryParameters, ...
                            refData.n.new.Infiltration, ...
                            refData.n.new.VentilationFree);
                    % enforced air renewal
                    self.Q_HLN(maskC & maskM & maskAMech) = ...
                        self.getBuildingNormHeatingLoad(...
                            refData.Uvalues.(className).Eff2, ...
                            refData.GeometryParameters, ...
                            refData.n.new.Infiltration, ...
                            refData.n.new.VentilationMech);                    
                else
                    % not modernised
                    % free air renewal
                    self.Q_HLN(maskC & ~maskM & ~maskAMech) = ...
                        self.getBuildingNormHeatingLoad(...
                            refData.Uvalues.(className).original, ...
                            refData.GeometryParameters, ...
                            refData.n.original.Infiltration, ...
                            refData.n.original.VentilationFree);
                    % enforced air renewal
                    self.Q_HLN(maskC & ~maskM & maskAMech) = ...
                        self.getBuildingNormHeatingLoad(...
                            refData.Uvalues.(className).original, ...
                            refData.GeometryParameters, ...
                            refData.n.original.Infiltration, ...
                            refData.n.original.VentilationMech);
                    % modernised
                    % free air renewal
                    self.Q_HLN(maskC & maskM & ~maskAMech) = ...
                        self.getBuildingNormHeatingLoad(...
                            refData.Uvalues.(className).modernised, ...
                            refData.GeometryParameters, ...
                            refData.n.modernised.Infiltration, ...
                            refData.n.modernised.VentilationFree);
                    % enforced air renewal
                    self.Q_HLN(maskC & maskM & maskAMech) = ...
                        self.getBuildingNormHeatingLoad(...
                            refData.Uvalues.(className).modernised, ...
                            refData.GeometryParameters, ...
                            refData.n.modernised.Infiltration, ...
                            refData.n.modernised.VentilationMech);
                end
                % update pStart
                pStart = pEnd;
            end

           % add slight randomisation to heating load
           self.Q_HLN = self.Q_HLN .* ...
                       (0.8 + rand(1, self.nBuildings) * 0.4);
                
           % dhn
           %%%%%
           self.maskThermal = rand(1, self.nBuildings) <= pThermal;
           self.nThermal = sum(self.maskThermal);
           
           self.currentHeatingLoad = zeros(1, self.nThermal);
        end
        
        function Q_HLN = getBuildingNormHeatingLoad(self, U, Geo, ...
                                                    nInfiltration, ...
                                                    nVentilation)
        %getBuildingNormHeatingLoad Calculate normed heating load of a building
        %                           
        %   The calculation is done in reference to the simplified method 
        %   of DIN EN 12831-1:2017-09
        %   Modifications / Simplifications:
        %       - Consideration of the whole building:
        %           o normed room temperature is set to 20°C
        %           o temperature matching coefficient is set to 1
        %       - Normed air heat losses include infiltration losses
        %
        % Inputs:
        %   U - Struct of U-Values [W/(m^2 K)]
        %       Contents: Roof, Wall, Window, Basement, Door, Delta
        %   Geo - Struct of buildings geometry data [m^2], [m^3]
        %       Contents: Aliving, Awall, Awindow, Adoor, Abasement, Aroof, V
        %   nInfiltration - Air renewal rate due infiltration [1/h]
        %   nVentilation - Air renewal rate due ventilation [1/h]
        %   ToutN - Normed outside temperature for specific region in °C (double)
        % Returns:
        %   Q_HLN - Normed heating load [W]
        
            % Temperature Difference
            dT = (20 - self.ToutN);
            % Transmission losses
            PhiT = (Geo.Abasement * (U.Basement + U.Delta) + ...
                    Geo.Awall * (U.Wall + U.Delta) + ...
                    Geo.Aroof * (U.Roof + U.Delta) + ...
                    Geo.Awindow * (U.Window + U.Delta) + ...
                    Geo.Adoor * (U.Door + U.Delta)) * dT;
            % Air renewal losses
            PhiA = Geo.V * (nInfiltration + nVentilation) * 0.3378 * dT;

            Q_HLN = PhiT + PhiA;
        end
    
        function self = getSpaceHeatingDemand(self, Tout)
        %getSpaceHeatingDemand Calculate space heating demand in W
        %   The space heating demand is calculated in relation to outside
        %   temperature and a building specific heating load.
        %   Based on a linear regression model the mean daily heating power is
        %   calculated. The space heating energy demand is determined by
        %   multiplicating this power with 24h.
        % Inputs:
        %   Tout - Current (daily mean) outside temperature in °C (double or vector)

            if min(self.Q_HLN(self.maskThermal)) <= 0
                error('Specific building heat load must be greater than 0.');
            end

            if Tout < 15
                self.currentHeatingLoad = -self.Q_HLN(self.nThermal) /...
                                          (15-self.ToutN) * ...
                                          (Tout-self.ToutN) + ...
                                          self.Q_HLN(self.nThermal);
            else
                self.currentHeatingLoad = self.currentHeatingLoad .* 0;
            end
        end
    end
    
    methods (Abstract)
        update(self) 
    end
end

