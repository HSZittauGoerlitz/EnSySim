classdef AgentSimulator < AbstractSimulationModule
    properties 
        agentArray AbstractSimulationAgent
        tblLoadProfiles % data type timetable https://de.mathworks.com/help/matlab/ref/timetable.html
        tblPhhProfile % only the PHH profile
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
            % agents use update step to do their balancing
            for each=obj.agentArray
                each.update()
            end
        end

        function obj = createLoadProfiles(obj, startDate, endDate)
            % for each agent type present a load profile is calculated once
            obj.tblLoadProfiles = getNormSLPs(startDate, endDate);
        end
        
        function obj = getPHH(obj)
            % create PHH profile if not yet seperated, helper for
            % ElectricalSlpSimulationElement initialization
            if isempty(obj.tblPhhProfile)
                obj = timetable(obj.tblLoadProfiles.Time,obj.tblLoadProfiles.PHH, 'VariableNames',["Data"]);
            else
                obj = obj.tblPhhProfile;
            end
        end
    end
  
end