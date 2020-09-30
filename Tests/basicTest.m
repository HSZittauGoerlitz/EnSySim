%% Parameter
startTime = datetime("01.01.2020 00:00:00");
endTime = datetime("31.12.2020 23:45:00");

load BoundaryConditions.mat

%% Init
time = getTime(startTime, endTime);
normSLP = getNormSLPs(startTime, endTime);

globalRad = getGlobalRadiation(startTime, endTime, Weather.East);

meanEG = sum(Weather.East.Eg)*0.25*1e-3;

TestCell = cellManager(5000, 0.25, 0.75, 0.2, 0.2, normSLP, meanEG, ...
                       BSL_COC_distribution, PHH_COC_distribution, ...
                       BSL_PV_AuxPowDemand_dist, PHH_PV_AuxPowDemand_dist);

%% Simulate
idx = 0;
Consumption_e = zeros(1, length(time));
Generation_e = zeros(1, length(time));
for t = time
    idx = idx + 1;
    TestCell.update(idx, globalRad.Eg(idx));
    Consumption_e(idx) = TestCell.currentEnergyBalance_e;
    Generation_e(idx) = sum(TestCell.PHHagents.Generation_e) + ...
                        sum(TestCell.BSLagents.Generation_e);
end

%% show results
figure('Position', [500, 200, 1000, 800])

subplot(2, 1, 1)
plot(time, Generation_e*1e-3, time, Consumption_e*1e-3)
grid on
ylabel("Electrical Energy in kWh")

legend("Generation", "Consumption", 'Location', 'northoutside', ...
       'Orientation', 'horizontal')

subplot(2, 1, 2)
plot(time, cumsum(Generation_e*1e-6), time, cumsum(Consumption_e*1e-6))
grid on
xlabel("Time")
ylabel("Cumulative Electrical Energy in MWh")