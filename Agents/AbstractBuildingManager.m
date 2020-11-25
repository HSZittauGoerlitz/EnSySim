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
        
        currentEnergyBalance_e  % Resulting eeb in current time step [Wh]
        currentEnergyBalance_t  % Resulting teb in current time step [Wh]

        % Load
        %-----
        
        Load_e  % resulting electrical load for each agent [W]
        Load_t  % resulting thermal load for each agent [W]
        
        % Generation
        %-----------
        
        Generation_e  % resulting electrical generation for each agent [W]
        Generation_t  % resulting thermal generation for each agent [W]
        
        nCHP  % Number of buildings with CHP-plants
        PCHP_t  % installed CHP power (thermal) [W]
        PCHP_e  % installed CHP power (electrical)
        maskWasOn  % logical array describing wether CHP was on last time step
        
        nPV  % Number of buildings with PV-Plants
        APV  % PV area [m^2]
        
        nStorage_t   % number of storages
        CStorage_t  % capacity of thermal storage [Wh]
        pStorage_t  % loading percentage of storage
        
        % Storage
        %--------
        
        Storage_e  % Electrical power from or to storages [W]
        Storage_t  % Thermal power from or to storages [W]


        % selection masks
        %----------------
        
        maskPV  % Mask for selecting all buildings with PV-Plants
        maskThermal  % Mask for selecting all buildings with connection to dhn
        maskStorage_t  % Mask for selecting all buildings with thermal storage
        maskCHP  % Mask for selecting all buildings with CHP-plants
        maskSelfSupply  % Mask for selecting all buildings with thermal self supply

    end
    
    methods
        function self = AbstractBuildingManager(nBuildings, pThermal, ...
                                                pCHPplants, ...
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
            %   pCHPplants - Portion of buildings with combined heat and
            %                power generation plants (0 to 1 each)
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
            if nBuildings < 0
                error("Number of buildings must be a positive integer value");
            end
            if pThermal < 0 || pThermal > 1
               error("pThermal must be a number between 0 and 1");
            end
            if pCHPplants < 0 || pCHPplants > 1
                error("pCHPplants must be a number between 0 and 1");
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
            self.Load_e = zeros(1, self.nBuildings);
            self.Generation_e = zeros(1, self.nBuildings);
            
            %%%%%%
            % PV %
            %%%%%%
            % generate selection mask for PV generation
            self.maskPV = rand(1, self.nBuildings) <= pPVplants;
            self.nPV = sum(self.maskPV);
            % init PV areas -> final managers have to scale it by COC
            self.APV = (rand(1, self.nPV) * 0.4 + 0.8) * 1e3 / Eg;
            
            %%%%%%%%%%%%%%%%%
            % Thermal Model %
            %%%%%%%%%%%%%%%%%
            self.Load_t = zeros(1, self.nBuildings);
            self.Generation_t = zeros(1, self.nBuildings);

            
            %%%%%%%%%%%%%%%%%%%%%%%
            % Normed heating load %
            %%%%%%%%%%%%%%%%%%%%%%%
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
                       (0.8 + rand(1, self.nBuildings));
            %%%%%%%
            % dhn %
            %%%%%%%
            self.maskThermal = rand(1, self.nBuildings) <= pThermal;
            self.nThermal = sum(self.maskThermal);
            
            %%%%%%%%%%%%%%%%%%%%%%%%%%%
            % Combined heat and power %
            %%%%%%%%%%%%%%%%%%%%%%%%%%% 
            self.maskCHP = rand(1, self.nBuildings);
            % generate CHP by portion of buildings
            self.maskCHP = self.maskCHP <= pCHPplants;
            % if bulding has dhn it can´t have a CHP plant 
            self.maskCHP(self.maskThermal) = false;
            self.nCHP = sum(self.maskCHP);
            % take 30% normalized heating load as installed power
            % round to full kW, result in W
            self.PCHP_t = zeros(1, self.nCHP);
            self.PCHP_t = round(self.Q_HLN(self.maskCHP)/1000)*1000*0.3;
            % 30% electrical efficiency
            self.PCHP_e = 0.3 * self.PCHP_t;
            self.maskWasOn = zeros(1, self.nBuildings);
            
            %%%%%%%%%%%%%%%%%%%
            % Thermal Storage %
            %%%%%%%%%%%%%%%%%%%
            
            %every building with CHP has thermal storage (except the ones on dhn)
            self.maskStorage_t = ~self.maskThermal & self.maskCHP;
            self.nStorage_t = sum(self.maskStorage_t);
            self.CStorage_t = zeros(1, self.nStorage_t);
            % 75l~kg per kW generation, 40K difference -> 60°C
            % c_Wasser = 4,184kJ/(kg*K)
            models = [0,200,300,400,500,600,750,950,1500,2000,3000,5000,99999999];
            volume = interp1(models,models,self.PCHP_t/1000*75,'next');
            self.CStorage_t = volume*4.184*40/3600*1000; % [Wh]
            % randomly load all storages
            self.pStorage_t = rand(1,self.nStorage_t);
            
            % get all buildings with self supply
            self.maskSelfSupply = ~(self.maskThermal | self.maskCHP);
            
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
        
        function self = getPVGeneration(self, Eg)
            self.Generation_e(self.maskPV) = self.Generation_e(self.maskPV) + ...
                                             self.APV .* Eg;
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

            if min(self.Q_HLN) <= 0
                error('Specific building heat load must be greater than 0.');
            end

            if Tout < 15
                self.Load_t = self.Load_t + ...
                              -self.Q_HLN / (15-self.ToutN) * ...
                              (Tout-self.ToutN) + self.Q_HLN;
            end
        end
        
        function self = getCHPGeneration(self, histLoad_t)

        %getCHPGeneration decides wether or not CHP is running and
        %   calculates thermal and electrical output.
        %   CHP gets switched on if current heating load could not be met from 
        %   storage content in this time step.
        %   If switched on it runs till storage is full.
        %   For now no modulation is implemented.
           
            % mask for switched on CHP
            IsOn = zeros(1, self.nBuildings);
            % On beacause storage nearly empty
            IsOn(self.maskCHP) = histLoad_t(self.maskCHP) * 0.25 ... % time step
                       > 0.5 * self.pStorage_t .* self.CStorage_t;
            % also On because was on last time step and still fills storage
            IsOn(self.maskCHP) = IsOn(self.maskCHP) | (self.maskWasOn(self.maskCHP) & (histLoad_t(self.maskCHP)*0.25 + ...
                         (1-self.pStorage_t) .* self.CStorage_t ...
                         > 0.25 * self.PCHP_t));
            % for now all heat demand gets supplied
            self.Generation_t(self.maskCHP) = self.Generation_t(self.maskCHP) + IsOn(self.maskCHP).*self.PCHP_t;
            % rest of thermal load gets supplied by Spitzenlastkessel (only
            % possible because load is known)
            spitzenlast = self.Generation_t(self.maskCHP)<self.Load_t(self.maskCHP);
            self.Generation_t(spitzenlast) = self.Load_t(spitzenlast);
            
            self.Generation_e(self.maskCHP) = self.Generation_e(self.maskCHP) + IsOn(self.maskCHP).*self.PCHP_e;
            
            self.maskWasOn = IsOn;
        end
        
        function self = updateCHPStorage_t(self)
            
        % getStorage_t calculate storage utilization 
        % The updated storage utiliztion gets calculated from a difference
        % between generation and load. 
            % store everything in exess
            toStore = self.Generation_t(self.maskCHP)-self.Load_t(self.maskCHP);
            self.pStorage_t = self.pStorage_t + ...
                              toStore./self.CStorage_t;
            % maximum charge 100% rest gets deleted for now
            self.pStorage_t(self.pStorage_t>1) = 1;
            
            self.Generation_t(self.maskCHP) = self.Generation_t(self.maskCHP) - toStore;
        end
        
        function self = getThermalSelfSupply(self)
           % Buildings with thermal self supply will just cover it's demand
            self.Generation_t(self.maskSelfSupply) = self.Load_t(self.maskSelfSupply); 
        end
       
        function self = update(self, Eg, Tout)
            % Reset current Load and Generation
            histLoad_t = self.Load_t;
            histLoad_e = self.Load_e;
            
            self.Load_t = self.Load_t * 0;
            self.Load_e = self.Load_e * 0;
            
            self.Generation_t = self.Generation_t * 0;
            self.Generation_e = self.Generation_e * 0;
                      
            self.getPVGeneration(Eg);
            self.getSpaceHeatingDemand(Tout); 
            self.getCHPGeneration(histLoad_t);
            self.getThermalSelfSupply();
        end
       
    end
    
end

