% import destatis data: https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Wohnen/Tabellen/wohneinheiten-nach-baujahr.html
% building age distribution in saxony
buildingAge(1:1155) = 1;  % before 1948
buildingAge(1156:1702) = 2;  % 1949 bis 1978
buildingAge(1703:1951) = 3;  % 1979 bis 1990
buildingAge(1952:2300) = 4;  % 1991 bis 2010
buildingAge(2301:2332) = 5;  % 2011 and later

weibFit = fitdist(buildingAge', 'weibul');

NewData = weibFit.random([50000, 1]);
% split values smaller 1 to 1 or 5
maskNewSmallerOne = NewData < 1;
nNewSmallerOne = sum(maskNewSmallerOne);
newValues = rand([nNewSmallerOne, 1]);
maskNewValues = newValues <= 0.65;
newValues(maskNewValues) = 1;
newValues(~maskNewValues) = 5;
NewData(maskNewSmallerOne) = newValues;
% set data to int values
NewData = floor(NewData);
% set values greater than 5 to 5
NewData(NewData > 5) = 5;
% shift a small part of cat 2 - 4 to cat 5


OrigPlot = histogram(buildingAge, 'Normalization', 'pdf', 'EdgeColor', [0.1 0.1 0.1], 'BinWidth', 1, ...
                     'DisplayStyle', 'stairs', 'DisplayName', 'original Data', 'LineWidth', 1);
hold on
NewPlot = histogram(NewData, 'Normalization', 'pdf', 'EdgeColor', [0.1 0.1 0.7], 'BinWidth', 1, ...
                    'DisplayStyle', 'stairs', 'DisplayName', 'modeled Data', 'LineWidth', 1);
grid on
xlabel('Building Category')
ylabel('Probability')
legend([OrigPlot, NewPlot])
hold off