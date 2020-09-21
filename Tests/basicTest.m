%% Parameter
startTime = datetime("01.01.2020 00:00:00");
endTime = datetime("31.01.2020 23:45:00");

%% Init
time = startTime:minutes(15):endTime;
normSLP = getNormSLPs(startTime, endTime);

agent = PHHconsumer_e(normSLP, PHH_COC_distribution);

%% Simulate
idx = 0;
for t = time
    idx = idx + 1;
    agent.update(idx);
end