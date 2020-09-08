% initialize simulation object
sim = Simulator();
esim = sim.registerSimulator(ElectricalSimulator);
asim = sim.registerSimulator(AgentSimulator);

% add agents
for each = COCarray
    agent = HouseholdAgent('Familie Maier')
    agent.COC = each
    asim.add(agent)
end


% define simulation times
sim.timeStep = 60
sim.startDate = datetime(2020,1,1,0,0,0)
sim.endDate = datetime(2020,1,2,0,0,0)

sim.run()
