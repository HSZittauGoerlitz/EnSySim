sim = Simulator();
asim = sim.registerSimulator(AgentSimulator);

startDate = datetime('2020-01-01 00:00:00');
endDate = datetime('2020-01-02 00:00:00');
set(sim, 'startDate', startDate);
set(sim, 'endDate', endDate);

u = symunit;
timeStep = 15*u.min;

nAgents = 100;
agentsType = 'Household';

for i=1:nAgents
    agent = SlpAgent(agentsType);
    asim.addAgent(agent)
    
end
asim.createLoadProfiles()


sim.run(startDate, endDate, timeStep);