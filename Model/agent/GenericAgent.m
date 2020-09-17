classdef GenericAgent < AbstractSimulationAgent

    properties
        % type of agent
        agentType
        % coc value
        coc
        % array of elements
        agentElements
        % balance
        power
       
    end
    
    methods
        function obj = GenericAgent(agentType)
            % is it neccessary to call superclass constructor?
            % do we need name or ID of elements? What for?
            % obj@AbstractSimulationAgent(friendlyName, elementID)
            obj.agentType = agentType;
        end
        function calculate(obj, time, timeStep)
            % for whatever there is to calculate

        end
        
        function update(obj)
            % balance all calculated elements
            electricalPower = 0;
            for each=obj.agentElements
                electricalPower = electricalPower + each.currentLoad;
            end
            obj.power = electricalPower;
        end
           
        function addElement(obj, element)
            obj.agentElements = [obj.agentElements element];
        end
    end
    
end