classdef AbstractAgent
    properties 
      friendlyName string
    end

    methods 
      function obj = AbstractAgent(friendlyName)
          obj.friendlyName = friendlyName
      end

    end
end