classdef ElectricalSimulator < AbstractSimulationModule
    properties
        % Array holding all electrical elements
        electricalElements AbstractSimulationElement
    end
    methods 
        function obj = ElectricalSimulator()

        end

        function add(element)
            % soll Elemente hinzufügen
        end

        function calculate(time, deltaTime)
            % soll alle Elemente aufrufen und berechnen
        end

        function update(time, deltaTime)
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