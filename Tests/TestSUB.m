startTime = datetime("01.01.2020 00:00:00");
endTime = datetime("31.12.2020 23:45:00");
load BoundaryConditions.mat
%% Init
time = getTime(startTime, endTime);
normSLP = getNormSLPs(startTime, endTime);
weatherBC = getWeatherBCcurves(startTime, endTime, Weather.East);

PHHs = AgentManager(time, 100, PHH_COC_distribution, 1, 5, ...
                    normSLP.PHH, HotWaterDayProfile.fProportion);
BSLcs = AgentManager(time, 50, BSL_COC_distribution, 1, 1, ...
                     normSLP.G0, HotWaterDayProfile.fProportion);
BSLas = AgentManager(time, 25, BSL_COC_distribution, 1, 1, ...
                     normSLP.L0, HotWaterDayProfile.fProportion);

SUBs = SUBmanager(180, 0.2, 0.3, Weather.dimensioning.East.Eg, ...
                  PHH_PV_AuxPowDemand_dist, ...
                  BSL_PV_AuxPowDemand_dist, [0.4, 0.2, 0.1, 0.1, 0.2], ...
                  [0.5, 0.5, 0.6, 0.6, 0.2], [0.2, 0.2, 0.2, 0.4, 0.5], ...
                  ReferenceBuilding.SAH, Weather.dimensioning.East.T, ...
                  PHHs, BSLcs, BSLas);
              
%% Simulate
idx = 0;
Balance_e = zeros(1, length(time));
Generation_e = zeros(1, length(time));
Balance_t = zeros(1, length(time));
Generation_t = zeros(1, length(time));
HeatingLoad = zeros(1, length(time));
for t = time
    idx = idx + 1;
    SUBs.update(idx, weatherBC.Eg(idx), weatherBC.T(idx));
    Balance_e(idx) = SUBs.currentEnergyBalance_e;
    Generation_e(idx) = sum(SUBs.Generation_e) * 0.25;
    Balance_t(idx) = SUBs.currentEnergyBalance_t;
    HeatingLoad(idx) = SUBs.currentHeatingLoad;
end

%% show results
figure('Position', [500, 200, 1500, 800])

subplot(2, 2, 1)
plot(time, Generation_e*1e-3, time, Balance_e*1e-3)
grid on
ylabel("Electrical Energy in kWh")

legend("Generation", "Balance", 'Orientation', 'horizontal', ...
       'Position', [0.4, 0.95, 0.2, 0.025])

subplot(2, 2, 3)
plot(time, cumsum(Generation_e*1e-6), time, cumsum(Balance_e*1e-6))
grid on
xlabel("Time")
ylabel("Cumulative Electrical Energy in MWh")

subplot(2, 2, 2)
plot(time, Generation_t*1e-3, time, Balance_t*1e-3)
grid on
ylabel("Thermal Energy in kWh")

subplot(2, 2, 4)
plot(time, cumsum(Generation_t*1e-6), time, cumsum(Balance_t*1e-6))
grid on
xlabel("Time")
ylabel("Cumulative Thermal Energy in MWh")