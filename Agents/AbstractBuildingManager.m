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
        
        % Bilance
        %--------
        % resulting Energy load bilance at given time step
        % positive: Energy is consumed
        % negative: Energy is generated
        
        currentEnergyBalance_e  % Resulting eeb in current time step [Wh]
        currentEnergyBalance_t  % Resulting teb in current time step [Wh]

        % Generation
        %-----------
        
        Generation_e  % Electrical generation [W]
        Generation_t  % Thermal generation [W]
        nPV  % Number of buildings with PV-Plants
        
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
                                                pPVplants, ...
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
            %   refDate - Data of reference Building as Struct
            %             Contents: Geometry, U-Values for each age class
            %                       and modernisation status, air renewal rates
            %             (See ReferenceBuilding of BoundaryConditions for
            %              example)
            %   ToutN - Normed outside temperature for specific region
            %           in °C (double)
            
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
            
            %%%%%%%%%%%%%%%%%
            % Thermal Model %
            %%%%%%%%%%%%%%%%%
            self.Generation_t = zeros(1, self.nBuildings);
            % Normed heating load
            %%%%%%%%%%%%%%%%%%%%%
            self.Q_HLN = zeros(1, nBuildings);
            % get and init specific buildings
            CA = rand(1, nBuildings); % class arrangement
            pStart = 0.0; % offset of proportions
            idx = 1;
            classNr = 0;
            for pClass = pBClass(1:end-1)
                % get specific buildings
                pEnd = pStart + pClass;
                maskC = CA >= pStart & CA < pEnd;
                % get modernisation status and air renewal method
                maskM = rand(1, sum(maskC)) <= pBModern(idx);
                maskAMech = rand(1, sum(maskC)) <= pBAirMech(idx);
                % get normed heat loads
                % not modernised
                % free air renewal
                self.Q_HLN(maskC & ~maskM & ~maskAMech) = ...
                    self.getBuildingNormHeatingLoad(...
                        refData.Uvalues.("class" + classNr).original, ...
                        refData.GeometryParameters, ...
                        refData.n.original.Infiltration, ...
                        refData.n.original.VentilationFree, ToutN);
                % enforced air renewal
                self.Q_HLN(maskC & ~maskM & maskAMech) = ...
                    self.getBuildingNormHeatingLoad(...
                        refData.Uvalues.("class" + classNr).original, ...
                        refData.GeometryParameters, ...
                        refData.n.original.Infiltration, ...
                        refData.n.original.VentilationMech, ToutN);
                % modernised
                % free air renewal
                self.Q_HLN(maskC & maskM & ~maskAMech) = ...
                    self.getBuildingNormHeatingLoad(...
                        refData.Uvalues.("class" + classNr).modernised, ...
                        refData.GeometryParameters, ...
                        refData.n.modernised.Infiltration, ...
                        refData.n.modernised.VentilationFree, ToutN);
                % enforced air renewal
                self.Q_HLN(maskC & maskM & maskAMech) = ...
                    self.getBuildingNormHeatingLoad(...
                        refData.Uvalues.("class" + classNr).modernised, ...
                        refData.GeometryParameters, ...
                        refData.n.modernised.Infiltration, ...
                        refData.n.modernised.VentilationMech, ToutN);
                
                % update pStart, index and classNr
                pStart = pEnd;
                idx = idx + 1;
                classNr = classNr + 1;
            end
            % calculate new buildings extra
            % get specific buildings
            pEnd = pStart + pBClass(idx);
            maskC = CA >= pStart & CA < pEnd;
            % get modernisation status and air renewal method
            maskM = rand(1, sum(maskC)) <= pBModern(idx);
            maskAMech = rand(1, sum(maskC)) <= pBAirMech(idx);
            % get normed heat loads
            % not modernised
            % free air renewal
            self.Q_HLN(maskC & ~maskM & ~maskAMech) = ...
                self.getBuildingNormHeatingLoad(...
                    refData.Uvalues.("class" + classNr).Eff1, ...
                    refData.GeometryParameters, ...
                    refData.n.new.Infiltration, ...
                    refData.n.new.VentilationFree, ToutN);
            % enforced air renewal
            self.Q_HLN(maskC & ~maskM & maskAMech) = ...
                self.getBuildingNormHeatingLoad(...
                    refData.Uvalues.("class" + classNr).Eff1, ...
                    refData.GeometryParameters, ...
                    refData.n.new.Infiltration, ...
                    refData.n.new.VentilationMech, ToutN);
            % modernised
            % free air renewal
            self.Q_HLN(maskC & maskM & ~maskAMech) = ...
                self.getBuildingNormHeatingLoad(...
                    refData.Uvalues.("class" + classNr).Eff2, ...
                    refData.GeometryParameters, ...
                    refData.n.new.Infiltration, ...
                    refData.n.new.VentilationFree, ToutN);
            % enforced air renewal
            self.Q_HLN(maskC & maskM & maskAMech) = ...
                self.getBuildingNormHeatingLoad(...
                    refData.Uvalues.("class" + classNr).Eff2, ...
                    refData.GeometryParameters, ...
                    refData.n.new.Infiltration, ...
                    refData.n.new.VentilationMech, ToutN);
           % dhn
           %%%%%
           self.maskThermal = rand(1, self.nBuildings) <= pThermal;
           self.nThermal = sum(self.maskThermal);    
        end
        
        function self = getBuildingNormHeatingLoad(self, U, Geo, ...
                                                   nInfiltration, ...
                                                   nVentilation, ...
                                                   ToutN)
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
            % Temperature Difference
            dT = (20 - ToutN);
            % Transmission losses
            PhiT = (Geo.Abasement * (U.Basement + U.Delta) + ...
                    Geo.Awall * (U.Wall + U.Delta) + ...
                    Geo.Aroof * (U.Roof + U.Delta) + ...
                    Geo.Awindow * (U.Window + U.Delta) + ...
                    Geo.Adoor * (U.Door + U.Delta)) * dT;
            % Air renewal losses
            PhiA = Geo.V * (nInfiltration + nVentilation) * 0.3378 * dT;

            self.Q_HLN = PhiT + PhiA;
        end
    end
end

