classdef AbstractSimulationAgent < AbstractSimulationElement
    properties 
        hasElements bool
        elements AbstractSimulationElement
    end

    methods 
        function obj = AbstractAgent(friendlyName)
          obj.friendlyName = friendlyName
        end

        function addElement(element)

        end
    end
end