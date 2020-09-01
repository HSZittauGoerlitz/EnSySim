classdef Simulation
    properties
        simulationModules = []
        startDate datetime
        endDate datetime
        timeStep int32
    end
    methods
        function registerSimulationModule(moduleClass)
            obj.simulationModules(1,obj.getModulesCount()+1) = moduleClass;
        end

        function n = getModulesCount()
            n = size(obj.simulationModules)
        end

        function reset()
          
        end
        
        function r = run()

        end
    end
end
