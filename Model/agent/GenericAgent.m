classdef GenericAgent < AbstractSimulationAgent

    properties
        % type of agent
        agentType
        % coc value
        coc
        % array of elements
        agentElements
       
    end
    
    methods
        function obj = GenericAgent(agentType)
            % is it neccessary to call superclass constructor?
            % do we need name or ID of elements? What for?
            % obj@AbstractSimulationAgent(friendlyName, elementID)
            obj.agentType = agentType;
        end
        function calculate(obj, time, timeStep)
            % calculate next time step load
            % obj.internalDeltaEnergy = load * timeStep
        end
        
        function update(obj)
            % write resulting load to 
        end
           
        function addElement(obj, element)
            obj.agentElements = [obj.agentElements element];
        end
    end
    
end