classdef (Abstract) AbstractSimulationModule < matlab.mixin.Heterogeneous & matlab.mixin.SetGet
    % find, reset, update, calculate, end

    methods (Abstract)
        calculate(obj)
    end
end

