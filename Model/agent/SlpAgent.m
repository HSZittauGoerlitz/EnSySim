classdef SlpAgent < AbstractSimulationAgent
    %% Agents with loads based on standard load profiles
    % for generation of profiles see
    % Model.agent.AgentSimulator.createLoadProfiles
    % agents will have 
    properties
        % type of agent
        agentType
        % COC value used to scale loads
        coc

        
    end
    
    methods
        function obj = SlpAgent(agentType) 
            obj.agentType = agentType;
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