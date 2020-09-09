classdef (Abstract) AbstractSimulationAgent < AbstractSimulationElement
    properties 
        hasElements logical
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