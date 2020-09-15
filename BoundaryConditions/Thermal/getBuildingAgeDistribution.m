% import destatis data: https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Wohnen/Tabellen/wohneinheiten-nach-baujahr.html
% building age distribution in saxony
buildingAgeCat(1:1155) = 1;  % 1948 and before
buildingAgeCat(1156:1702) = 2;  % 1949 bis 1978
buildingAgeCat(1703:1951) = 3;  % 1979 bis 1990
buildingAgeCat(1952:2300) = 4;  % 1991 bis 2010
buildingAgeCat(2301:2332) = 5;  % 2011 and later

% probabilities of each category
pAgeCat = [0.4952, 0.2346, 0.1068, 0.1497, 0.0137];
% generate new Data
nExamples = 50000;
pNewData = rand([nExamples, 1]);
NewData = zeros([nExamples, 1]);
pRight = pAgeCat(1);
NewData(pNewData < pRight) = 1;
for cat = 2:4
    pLeft = pRight;
    pRight = pRight + pAgeCat(cat);
    NewData(pNewData >= pLeft & pNewData < pRight) = cat;
end
pLeft = pRight;
NewData(pNewData >= pLeft) = cat+1;

OrigPlot = histogram(buildingAgeCat, 'Normalization', 'pdf', 'EdgeColor', [0.1 0.1 0.1], 'BinWidth', 1, ...
                     'DisplayStyle', 'stairs', 'DisplayName', 'original Data', 'LineWidth', 1);
hold on
NewPlot = histogram(NewData, 'Normalization', 'pdf', 'EdgeColor', [0.1 0.1 0.7], 'BinWidth', 1, ...
                    'DisplayStyle', 'stairs', 'DisplayName', 'modeled Data', 'LineWidth', 1);
grid on
xlabel('Building Category')
ylabel('Probability')
legend([OrigPlot, NewPlot])
hold off;

% generate building age data
buildingAge = zeros([nExamples, 1]);
% flatten the first cat by using also a year range
buildingAge(NewData == 1) = randi([1920, 1948], ...
                                  [sum(NewData == 1), 1]);
buildingAge(NewData == 2) = randi([1949, 1978], ...
                                  [sum(NewData == 2), 1]);
buildingAge(NewData == 3) = randi([1979, 1990], ...
                                  [sum(NewData == 3), 1]);
buildingAge(NewData == 4) = randi([1991, 2010], ...
                                  [sum(NewData == 4), 1]);
buildingAge(NewData == 5) = randi([2010, 2018], ...
                                  [sum(NewData == 5), 1]);
                                     
figure
histogram(buildingAge, 'Normalization', 'pdf');