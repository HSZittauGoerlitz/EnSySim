classdef ExecutionManager
  
end

classdef RealTimeExecutionManager < ExecutionManager
    methods 
        function init(time)
            obj._time = time
            obj._start = 0
            obj._elapsed = 0
        end

        function reset()
            obj._start = 0 % ???
            obj._elapsed = 0
        end

    end
  
end