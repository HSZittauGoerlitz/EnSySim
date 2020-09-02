classdef ElectricalConsumerSimulationElement < ElectricalSimulationElement
    properties
        Power
        deltaEnergy
    end
    methods
        function obj = calculate(obj, deltaTime)
            obj.deltaEnergy = obj.power * deltaTime;
        end
    end
end    
