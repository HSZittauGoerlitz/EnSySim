classdef SlpAgent < AbstractSimulationAgent
    %% Agents with loads based on standard load profiles
    % for generation of profiles see
    % Model.agent.AgentSimulator.createLoadProfiles
    % agents will have 
    properties
        % type of agent
        agentType
        % coc value
        coc
        % scaled load profile
        loadProfile

        
    end
    
    methods
        function obj = SlpAgent(agentType, coc, loadProfile)
            % is it neccessary to call superclass constructor?
            % do we need name or ID of elements? What for?
            % obj@AbstractSimulationAgent(friendlyName, elementID)
            obj.agentType = agentType;
            obj.loadProfile = loadProfile;
            obj.coc = coc;
        end
        function calculate(obj, time, timeStep)
            % calculate next time step load
            % obj.internalDeltaEnergy = load * timeStep
        end
        
        function update(obj)
            % write resulting load to 
        end
           
    end
    
end