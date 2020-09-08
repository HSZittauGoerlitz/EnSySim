classdef AgentSimulator < AbstractSimulationModule
    properties 
        agentArray AbstractSimulationAgent
        profilesArray % data type timetable https://de.mathworks.com/help/matlab/ref/timetable.html
    end
    methods 
        function obj = AgentSimulator()

        end

        function addAgent(agent)
            % adds agent to agentArray
            obj.agentArray = [obj.agentArray agent];
        end

        function calculate(time, deltaTime)
            % calls all agents
        end

        function update(time, deltaTime)
            % updates all agents
        end

        function createLoadProfiles(startDate, endDate, timeStep)
            % for each agent type present a load profile is calculated once
            % ist es möglich auf Basis des Typs der agentArray-Objekte zu 
            % arbeiten, etwa
            %
            % for type in agentArray:
            %   slp = profileData(type)
            %   slp.loadProfileData(startDate, endDate)
            %   slp.createSimulationProfile(timeStep)
            %   profilesArray(agentType) = slp
        end

    end
  
end