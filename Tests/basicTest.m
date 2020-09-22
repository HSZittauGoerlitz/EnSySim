%% Parameter
startTime = datetime("01.01.2020 00:00:00");
endTime = datetime("31.12.2020 23:45:00");

load BoundaryConditions.mat

%% Init
time = startTime:minutes(15):endTime;
normSLP = getNormSLPs(startTime, endTime);

TestCell = cellManager(5000, 0.25, 0.75, 0.2, normSLP, ...
                       BSL_COC_distribution, PHH_COC_distribution);

%% Simulate
idx = 0;
resBilance_e = zeros(1, 5000);
for t = time
    idx = idx + 1;
    TestCell.update(idx);
    resBilance_e(idx) = TestCell.currentEnergyBalance_e;
end

%% show results
figure;
subplot(2, 1, 1)
plot(time, resBilance_e*1e-3)
grid on
xlabel("Time")
ylabel("Electrical Energy consumption in kWh")

subplot(2, 1, 2)
plot(time, cumsum(resBilance_e*1e-6))
grid on
xlabel("Time")
ylabel("Cumulative Electrical Energy consumption in MWh")