classdef Simulator < handle
    properties
        simulationModules AbstractSimulationModule
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

%             modules = []
%             for each=obj.simulationModules
%                 module = each()
%                 module.simulator = obj
%                 obj.modules
%             end
        end

        function module = registerSimulator(obj, moduleClass)
            obj.simulationModules = [obj.simulationModules moduleClass];
            module = moduleClass;
        end

        function n = getModulesCount(obj)
            % gets the number of registered modules
            n = size(obj.simulationModules);
        end

        function reset()
          
        end

        function run()
            % runs the simulation according to choosen execution manager via calling step()
        end
    end
end
