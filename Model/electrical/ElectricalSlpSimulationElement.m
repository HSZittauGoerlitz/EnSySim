classdef ElectricalSlpSimulationElement < ElectricalSimulationElement

    properties
        simulationTime
        loadProfile
        currentLoad
    end
    methods
        function obj = ElectricalSlpSimulationElement(coc, loadProfile)
            % scale load profile with coc, slp type gets defined by given
            % pr
            data = loadProfile.Data;
            data = data * coc;
            obj.loadProfile = timetable(loadProfile.Time, data);
        end

        function calculate(obj, simulationTime, timeStep)
            % get current load from profile
            % Todo: interpolation for smaller time steps
            obj.simulationTime = simulationTime;
            obj.currentLoad = obj.loadProfile.Var1(obj.simulationTime);
        end

        function update(obj, args)
            % unused at the moment
        end


    end
end