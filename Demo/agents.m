%% create simulation and register modules
sim = Simulator();
asim = sim.registerSimulator(AgentSimulator);
esim = sim.registerSimulator(ElectricalSimulator);

%% times
startDate = datetime('2020-01-01 00:00:00');
endDate = datetime('2020-01-01 23:45:00');
set(sim, 'startDate', startDate);
set(sim, 'endDate', endDate);

u = symunit;
timeStep = minutes(15);

%% agents
% 1. festlegen Gesamtagentenzahl
% 2. über Anteile Typen festlegen
% 3. COC-Werte generieren
% 4. Lastprofile generieren
% 5. Agenten mit spezifischen Lastprofilen generieren

% number of agents
noPhhAgents = 100;

%% Following should be packaged in ElectricalSimulator
% generate COC values from scaled distribution
load('BoundaryConditions.mat',  'PHH_COC_distribution')
upperLimit = 5; % upper coc limit
lowerLimit = 1; % lower coc limit
coc = PHH_COC_distribution.random([noPhhAgents, 1])*upperLimit;

% rerandom all values below 1
idx = 0;
while idx < 10
    coc(coc<lowerLimit) = PHH_COC_distribution.random([sum(coc<lowerLimit), 1])*upperLimit;
    idx = idx + 1;
end

% generate load profiles
asim.createLoadProfiles(startDate, endDate);

%% create and add all agents with their respective load profiles
for i=1:noPhhAgents
    agent = GenericAgent('PHH');
    electricalSlpLoad = ElectricalSlpSimulationElement(coc(i), asim.getPHH());
    esim.addElement(electricalSlpLoad);
    agent.addElement(electricalSlpLoad);
    asim.addAgent(agent);
end

%% initialize and run simulation
sim.initialize(startDate, endDate, timeStep)
sim.run(startDate, endDate, timeStep);