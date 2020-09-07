classdef RealTimeExecutionManager < AbstractExecutionManager
    % hier soll mal das Zeitmanagement hin, damit wir online mit THERESA-Einbindung simulieren können.
    methods 
        function init(time)
            obj.time = time
            obj.start = 0
            obj.elapsed = 0
        end

        function reset()
            obj.start = 0 % ???
            obj.elapsed = 0
        end

    end
  
end