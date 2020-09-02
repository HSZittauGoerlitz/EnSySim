classdef Simulator
    properties
        simulationModules = [];
        executionManager
        startDate datetime
        endDate datetime
        timeStep int32
    end
    methods
        function obj = Simulator(executionManager)
            
            if nargin == 0
                obj.executionManager = DefaultExecutionManager()
            else
                obj.executionManager = executionManager
            end

            modules = []
            for each=obj.simulationModules
                module = each()
                module.simulator = obj
                obj.modules
            end
        end

        function obj = registerSimulationModule(obj, moduleClass)
            % gets called by each module holding the different elements
            if ~isempty(obj.simulationModules)
                obj.simulationModules(end+1) = moduleClass;
            else
                obj.simulationModules = moduleClass;
            end
        end

        function n = getModulesCount(obj)
            % gets the number of registered modules
            n = size(obj.simulationModules)
        end

        function reset()
          
        end

        function run()
            % runs the simulation according to choosen execution manager via calling step()
        end
    end
end
