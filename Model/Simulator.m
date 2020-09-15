classdef Simulator < matlab.mixin.SetGet
    %% Set up a simulation with ensysim.
    % Provides the main simulation class where modules are registered
    % and progression of time is managed.
    properties
        % Array holding the simulation modules
        simulationModules AbstractSimulationModule 
        % pre- and postprocessing defined here
        executionManager 
        % simulations can run over specific datetime intervalls for
        % utilization of standardized load profiles 
        startDate datetime
        endDate datetime
        % time step in which the simulation progresses
        timeStep int32 % in seconds
        % array holding all simulation steps, maybe better suited for running?
        simulationSteps
        % actual simulation time
        time
    end
    
    methods
        function obj = Simulator(executionManager)
            if nargin == 0
                obj.executionManager = DefaultExecutionManager();
            else
                obj.executionManager = executionManager;
            end
        end

        function module = registerSimulator(obj, moduleClass)
            obj.simulationModules = [obj.simulationModules moduleClass];
            module = moduleClass;
        end

        function n = getModulesCount(obj)
            % gets the number of registered modules
            n = size(obj.simulationModules);
        end
        
        function set.startDate(obj, startDate)
            obj.startDate = startDate;
        end
            
        function set.endDate(obj, endDate)
            obj.endDate = endDate;
        end
        
        function initialize(obj, startDate, endDate, timeStep)
            obj.simulationSteps = startDate:timeStep:endDate;
        end
            
        function reset()
          
        end

        function run(obj, startDate, endDate, timeStep)
            % runs the simulation according to choosen execution manager via calling step()
            time = startDate;

            while time < endDate
                for each=obj.simulationModules
                    each.calculate(time, timeStep);
                    each.update();
                    time = time + timeStep
                end
            end
        end
        
        function elements = findElements(varargin)
            % test https://de.mathworks.com/help/matlab/ref/inputparser.html
            
            defaultModule = AbstractSimulationModule
            defaultName = ''
            defaultClass = AbstractSimulationElement
            defaultProperty = ''
            
            p = inputParser;
            addOptional(p,'simulationModule', defaultModule);
            addOptional(p,'friendlyName', defaultName, @isstring);
            addOptional(p,'elementClass', defaultClass);
            addOptional(p,'elementProperty', defaultProperty, @isstring);
            parse(p,varargin{:});
            
            % do actual search of relevant elements
        end
        
    end
    
end
