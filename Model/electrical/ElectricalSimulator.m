classdef ElectricalSimulator < AbstractSimulationModule
    properties
        elements = []
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
    end
  
end