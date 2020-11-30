%% Parameter
startTime = datetime("01.01.2020 00:00:00");
endTime = datetime("31.12.2020 23:45:00");

load BoundaryConditions.mat

% agents [Free Standing, Row End, Small, Big Multi User]
nBAgents = [10, 0, 0, 0]; %agents per building class
nBSLsepAgents = 1000;
nBuildings = [10, 0, 0, 0]; %number of buildings
pPHHagents = [1, 0, 0, 0];
pAgriculture = 0.2;
% agents - COC
BSL_COC.function = BSL_COC_distribution;
BSL_COC.min = 1;
BSL_COC.scale = 1;
PHH_COC.function = PHH_COC_distribution;
PHH_COC.min = 1;
PHH_COC.scale = 5;
% district heating, CHP and PV
pThermal = [0.0, 0.07, 0.14, 0.14]; % percentage from all with district heating
pCHPplants = [1, 0, 0, 0]; % percentage from not with district heating with CHP
pPVplants = 0;
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
% Results Electrical
Balance_e = zeros(1, length(time));
Load_e = zeros(1, length(time));
Generation_e = zeros(1, length(time));
% Results thermal
Balance_t = zeros(1, length(time));
Load_t = zeros(1, length(time));
Generation_t = zeros(1, length(time));
% dhn
Load_dhn = zeros(1, length(time));
% CPH
CHP_state = zeros(sum(horzcat(TestCell.SUBs.nCHP)), length(time));
% Storage
Storage_t = zeros(sum(horzcat(TestCell.SUBs.nStorage_t)), length(time));

for t = time
    idx = idx + 1;
    TestCell.update(idx, weatherBC.Eg(idx), weatherBC.T(idx));
    Balance_e(idx) = TestCell.currentEnergyBalance_e;
    Load_e(idx) = (sum(horzcat(TestCell.SUBs.Load_e)) + ...
                   sum(horzcat(TestCell.MUBs.Load_e)) + ...
                   sum(horzcat(TestCell.BSLsepAgents.Load_e))) * 0.25;
    Generation_e(idx) = (sum(horzcat(TestCell.SUBs.Generation_e)) + ...
                         sum(horzcat(TestCell.MUBs.Generation_e)) + ...
                         sum(horzcat(TestCell.BSLsepAgents.Generation_e))) * 0.25;
    
    Balance_t(idx) = TestCell.currentEnergyBalance_t;
    Load_t(idx) = (sum(horzcat(TestCell.SUBs.Load_t)) + ...
                   sum(horzcat(TestCell.MUBs.Load_t)) ) * 0.25;
    Generation_t(idx) = (sum(horzcat(TestCell.SUBs.Generation_t)) + ...
                         sum(horzcat(TestCell.MUBs.Generation_t))) * 0.25;          
                     
                     
                     
    temp = horzcat(TestCell.SUBs.maskWasOn);
    CHP_state(:,idx) = temp(horzcat(TestCell.SUBs.maskCHP));
    Storage_t(:,idx) = horzcat(TestCell.SUBs.pStorage_t);
end

%% show results
red = [1, 0.3294, 0.3098];
green = [0.1059, 0.7765, 0.1843];

figure('Position', [200, 100, 1500, 800])

s1 = subplot(2, 2, 1);
hold on
plot(time, Load_e*1e-3, 'Color', red)
plot(time, Generation_e*1e-3, 'Color', green)
plot(time, Balance_e*1e-3, 'Color', [0, 0, 0])
hold off
grid on
ylabel("Energy in kWh")
title("Electrical")

legend("Load", "Generation", "Balance", 'Orientation', 'horizontal', ...
       'Position', [0.4, 0.95, 0.2, 0.025])

s3 = subplot(2, 2, 3);
hold on
plot(time, cumsum(Load_e*1e-6), 'Color', red)
plot(time, cumsum(Generation_e*1e-6), 'Color', green)
plot(time, cumsum(Balance_e*1e-6), 'Color', [0, 0, 0])
hold off
grid on
xlabel("Time")
ylabel("Cumulative Energy in MWh")

s2 = subplot(2, 2, 2);
hold on
plot(time, Load_t*1e-3, 'Color', red)
plot(time, Generation_t*1e-3, 'Color', green)
plot(time, Balance_t*1e-3, 'Color', [0, 0, 0])
hold off
grid on
ylabel("Energy in kWh")
title("Thermal")

s4 = subplot(2, 2, 4);
hold on
plot(time, cumsum(Load_t*1e-6), 'Color', red)
plot(time, cumsum(Generation_t*1e-6), 'Color', green)
plot(time, cumsum(Balance_t*1e-6), 'Color', [0, 0, 0])
hold off
grid on
xlabel("Time")
ylabel("Cumulative Energy in MWh")
linkaxes([s1 s2 s3 s4],'x');

f = figure();
nStorage = size(Storage_t);
nStorage = nStorage(1);
s1 = subplot(3, 1, 1);
surface(time, 1:nStorage, Storage_t, 'EdgeColor', 'none');
ylim([1 nStorage]);
set(gca,'XColor', 'none')
s2 = subplot(3, 1, 2);
surface(time, 1:nStorage, CHP_state, 'EdgeColor', 'none');
ylim([1 nStorage]);
set(gca,'XColor', 'none');
s3 = subplot(3,1,3);
plot(time, weatherBC.T, 'Color', [0, 0, 0]);
 
linkaxes([s1 s2 s3],'x');
