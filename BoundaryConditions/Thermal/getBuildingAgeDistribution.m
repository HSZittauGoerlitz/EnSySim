% import destatis data: https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Wohnen/Tabellen/wohneinheiten-nach-baujahr.html
% building age distribution in saxony
buildingAgeCat(1:1155) = 1;  % before 1948
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