% Examine hot water demand of PHH in destatis data
% data from https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Umwelt/UGR/private-haushalte/Tabellen/energieverbrauch-haushalte.html
year = [2010, 2015, 2016, 2017, 2018];
SpaceHeatingDemand = [525, 513, 530, 515, 544];  % 10^9kWh
HotWaterDemand = [85, 93, 93, 98, 102];  % 10^9kWh

ratio = HotWaterDemand ./ SpaceHeatingDemand;
r_mean = ones(length(year), 1) .* mean(ratio);
r_mean_15_18 = ones(length(year), 1) .* mean(ratio(2:end));

% show data
figure
hold on
yyaxis left
ylabel('Heat in 10^9 kWh')
plot(year, SpaceHeatingDemand, year, HotWaterDemand, year, ratio)
yyaxis right
ylabel('ratio')
plot(year, ratio, year, r_mean, year, r_mean_15_18)
grid on
xlabel('Year')
legend('Space Heating', 'Hot Water', 'ratio', 'mean complete', 'mean 2015-2018')
hold off