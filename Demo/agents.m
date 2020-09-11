sim = Simulator();
asim = sim.registerSimulator(AgentSimulator);

startDate = datetime('2020-01-01 00:00:00');
endDate = datetime('2020-12-31 23:45:00');
set(sim, 'startDate', startDate);
set(sim, 'endDate', endDate);

u = symunit;
timeStep = minutes(15);

% 1. festlegen Gesamtagentenzahl
% 2. über Anteile Typen festlegen
% 3. COC-Werte generieren
% 4. Lastprofile generieren
% 5. Agenten mit spezifischen Lastprofilen generieren

% number of agents
noPhhAgents = 100;
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

% create and add all agents
for i=1:noPhhAgents
    agent = SlpAgent('PHH', asim.tblLoadProfiles.PHH, coc);
    asim.addAgent(agent)
end

% initialize and run simulation
sim.initialize(startDate, endDate, timeStep)
sim.run();