classdef AgentSimulator < AbstractSimulationModule
    properties 
        agents = []       
    end
    methods 
        function obj = AgentSimulator()

        end

        function obj = add(obj, agent)
            % soll Elemente hinzufügen
            if ~isempty(obj.agents)
                obj.agents(end+1) = agent;
            else
                obj.agents = agent;
            end
            obj = agent
        end

        function calculate(time, deltaTime)
            % soll alle Elemente aufrufen und berechnen
        end

        function update(time, deltaTime)
            % soll die Daten in jeden Element aktualisieren
        end
    end
  
end