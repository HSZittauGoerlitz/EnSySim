classdef ElectricalSimulator < AbstractSimulationModule
    properties
        % Array holding all electrical elements
        arrayElements AbstractSimulationElement
    end
    methods 
        function obj = ElectricalSimulator()

        end

        function addElement(obj, element)
            % soll Elemente hinzufügen
            obj.arrayElements = [obj.arrayElements element];
        end

        function calculate(obj, time, timeStep)
            % soll alle Elemente aufrufen und berechnen
            for each=obj.arrayElements
                each.calculate(time, timeStep);
            end
        end

        function update(obj, time, timeStep)
            % soll die Daten in jeden Element aktualisieren
        end
        
        function createSolarInput(startDate, endDate, timeStep)
            % PV needs solar input for each timeStep. If present,
            % this gets calculated upfront.
            % Vielleicht kommt hier auch noch die Ortsabhängigkeit 
            % der PV ins Spiel.
        end
        
    end
  
end