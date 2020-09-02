classdef AbstractSimulationElement
    % reset, calculate, update
    properties
        elementID
        friendlyName
    end
    methods
        function obj = InitilizeElement(friendlyName, elementID)
            obj.friendlyName = friendlyName
            obj.elementID = elementID
        end
    end
end