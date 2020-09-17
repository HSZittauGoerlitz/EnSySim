classdef ElectricalSlpSimulationElement < ElectricalSimulationElement

    properties
        time
        loadProfile
        internalLoad
        load
    end
    methods
        function obj = ElectricalSlpSimulationElement(coc, loadProfile)
            %scale = @(x) x * coc;
            %obj.loadProfile = varfun(scale,loadProfile);% ?
            data = loadProfile.PHH;
            data = data * coc;
            obj.loadProfile = timetable(loadProfile.Time, data);
        end

        function calculate(obj, time, timeStep)
            % get current load from profile
            obj.time = time;
            obj.internalLoad = obj.loadProfile.Var1(obj.time);
        end

        function update(obj, args)
            % write current load to public property
        end


    end
end