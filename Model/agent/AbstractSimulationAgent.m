classdef (Abstract) AbstractSimulationAgent < AbstractSimulationElement
    properties 
        hasElements bool
        elementArray AbstractSimulationElement
        internalDeltaEnergy
        deltaEnergy
        
    end
    methods (Abstract)
        calculate(obj)
        update(obj)
    end
    
    methods 
        function obj = AbstractAgent(friendlyName)
          obj.friendlyName = friendlyName
        end

        function addElement(element)

        end

    end
end