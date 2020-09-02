classdef Simulator
    properties
        _simulationModules = []
        startDate datetime
        endDate datetime
        timeStep int32
    end
    methods
        function obj = Simulator(executionManager)
            
            if nargin == 0
                obj._executionManager = DefaultExecutionManager()
            else
                obj._executionManager = executionManager
            end

            obj._modules = []
            for each=obj._simulationModules
                module = each()
                module.simulator = obj
                obj._modules
        end

        function registerSimulationModule(moduleClass)
            % gets called by each module holding the different elements
            obj._simulationModules(1,obj.getModulesCount()+1) = moduleClass;
        end

        function n = getModulesCount()
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
