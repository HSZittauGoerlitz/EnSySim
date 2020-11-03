%% Parameter
startTime = datetime("01.01.2020 00:00:00");
endTime = datetime("31.12.2020 23:45:00");

load BoundaryConditions.mat

% agents
nBAgents = [500, 1000, 4000, 4500];
nBSLsepAgents = 1000;
nBuildings = [505, 1010, 680, 100];
pPHHagents = [0.8, 0.8, 0.6, 0.9];
pAgriculture = 0.2;
% agents - COC
BSL_COC.function = BSL_COC_distribution;
BSL_COC.min = 1;
BSL_COC.scale = 1;
PHH_COC.function = PHH_COC_distribution;
PHH_COC.min = 1;
PHH_COC.scale = 5;
% district heating and PV
pThermal = [0.07, 0.07, 0.14, 0.14];
pCHPplants = [0, 0, 0, 0];
pPVplants = 0.4;
% buildings
FSH.Class = [0.2587, 0.383, 0.1767, 0.1816, 0.0];
FSH.Modern = [0.4704, 0.4712, 0.2897, 0.0485, 0.0];
FSH.AirMech = [0.02, 0.05, 0.05, 0.1, 0.0];
REH.Class = [0.2409, 0.3788, 0.2032, 0.1771, 0.0];
REH.Modern = [0.4758, 0.4712, 0.2928, 0.0492, 0.0];
REH.AirMech = [0.02, 0.05, 0.05, 0.1, 0.0];   
SAH.Class = [0.2589, 0.4371, 0.1443, 0.1597, 0.0];
SAH.Modern = [0.4797, 0.4815, 0.3798, 0.1363, 0.0];
SAH.AirMech = [0.02, 0.05, 0.05, 0.1, 0.0];
BAH.Class = [0.0681, 0.6185, 0.3134];
BAH.Modern = [0.4842, 0.4799, 0.3683];
BAH.AirMech = [0.02, 0.05, 0.05];
pBTypes.FSH = FSH;
pBTypes.REH = REH;
pBTypes.SAH = SAH;
pBTypes.BAH = BAH;
% environment
region = "East";

%% Init
time = getTime(startTime, endTime);
normSLP = getNormSLPs(startTime, endTime);

weatherBC = getWeatherBCcurves(startTime, endTime, Weather.(region));

TestCell = CellManager.initDefaultCell(time, nBAgents, nBSLsepAgents, ...
                                       nBuildings, pPHHagents, pAgriculture, ...
                                       pThermal, pCHPplants, pPVplants, pBTypes, ...
                                       normSLP, ...
                                       Weather.dimensioning.(region).Eg, ...
                                       Weather.dimensioning.(region).T, ...
                                       ReferenceBuilding, ...
                                       HotWaterDayProfile.fProportion, ...
                                       BSL_COC, PHH_COC, ...
                                       BSL_PV_AuxPowDemand_dist, ...
                                       PHH_PV_AuxPowDemand_dist);

%% Simulate
idx = 0;
Balance_e = zeros(1, length(time));
Generation_e = zeros(1, length(time));
Balance_t = zeros(1, length(time));
Generation_t = zeros(1, length(time));

for t = time
    idx = idx + 1;
    TestCell.update(idx, weatherBC.Eg(idx), weatherBC.T(idx));
    Balance_e(idx) = TestCell.currentEnergyBalance_e;
    Generation_e(idx) = (sum(horzcat(TestCell.SUBs.Generation_e)) + ...
                         sum(horzcat(TestCell.MUBs.Generation_e)) + ...
                         sum(horzcat(TestCell.BSLsepAgents.Generation_e))) * 0.25;
    Balance_t(idx) = TestCell.currentEnergyBalance_t;
    
end

%% show results
figure('Position', [200, 100, 1500, 800])

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