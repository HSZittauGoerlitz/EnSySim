classdef AbstractSimulationAgent < AbstractSimulationElement
    properties 
        hasElements bool
        elementArray AbstractSimulationElement
    end

    methods 
        function obj = AbstractAgent(friendlyName)
          obj.friendlyName = friendlyName
        end

        function addElement(element)

        end

        function calculate(time, timeStep)
            % gets current standard load from parent obejct (profiles Array) und scales with COC
        end
    end
end