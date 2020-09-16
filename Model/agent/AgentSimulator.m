classdef AgentSimulator < AbstractSimulationModule
    properties 
        agentArray AbstractSimulationAgent
        tblLoadProfiles % data type timetable https://de.mathworks.com/help/matlab/ref/timetable.html
        tblPhhProfile
    end
    methods 
        function obj = AgentSimulator()

        end

        function addAgent(obj, agent)
            % adds agent to agentArray
            obj.agentArray = [obj.agentArray agent];
        end

        function calculate(obj, time, deltaTime)
            % nothing to calculate yet

        end

        function update(obj, time, deltaTime)
            for each=obj.agentArray
                each.update()
            end
        end

        function obj = createLoadProfiles(obj, startDate, endDate)
            % for each agent type present a load profile is calculated once
            % ist es möglich auf Basis des Typs der agentArray-Objekte zu 
            % arbeiten, etwa
            %
            % for type in agentArray:
            %   slp = profileData(type)
            %   slp.loadProfileData(startDate, endDate)
            %   slp.createSimulationProfile(timeStep)
            %   profilesArray(agentType) = slp
            obj.tblLoadProfiles = getNormSLPs(startDate, endDate);
        end
        function obj = getPHH(obj)
            if isempty(obj.tblPhhProfile)
                obj = timetable(obj.tblLoadProfiles.Time,obj.tblLoadProfiles.PHH, 'VariableNames',["PHH"]);
            else
                obj = obj.tblPhhProfile;
            end
        end
    end
  
end