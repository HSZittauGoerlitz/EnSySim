% initialize simulation object
sim = Simulator;
sim.registerSimulationModule(ElectricalSimulator)

% define simulation times
sim.timeStep = 60
sim.startDate = datetime(2020,1,1,0,0,0)
sim.endDate = datetime(2020,1,2,0,0,0)

% add agents
asim.add(HouseholdAgent('Agent 1'))



simulation.run()
