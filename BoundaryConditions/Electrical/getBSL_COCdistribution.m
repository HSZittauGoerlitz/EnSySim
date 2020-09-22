%% load Fraunhofer ISI data
load BSL_ISIdata.mat

%% parameter
fData = 100;  % Multiplicator for number of points in new data set

%% create bigger data sets with equal share
nDataConstruction = nConstruction * fData;
dataConstruction = ones(1, nDataConstruction);

idxStart = 1;
for row = 1:height(Construction)
   idxStop = round(Construction.Percentage(row) / 100 * nDataConstruction) + idxStart;
   dataConstruction(idxStart:idxStop) = Construction.COC(row);
   idxStart = idxStop + 1;
end

nDataOffice = nOffice * fData;
dataOffice = ones(1, nDataOffice);

idxStart = 1;
for row = 1:height(Office)
   idxStop = round(Office.Percentage(row) / 100 * nDataOffice) + idxStart;
   dataOffice(idxStart:idxStop) = Office.COC(row);
   idxStart = idxStop + 1;
end

nDataProduction = nProduction * fData;
dataProduction = ones(1, nDataProduction);

idxStart = 1;
for row = 1:height(Production)
   idxStop = round(Production.Percentage(row) / 100 * nDataProduction) + idxStart;
   dataProduction(idxStart:idxStop) = Production.COC(row);
   idxStart = idxStop + 1;
end

nDataRetailMarket = nRetailMarket * fData;
dataRetailMarket = ones(1, nDataRetailMarket);

idxStart = 1;
for row = 1:height(RetailMarket)
   idxStop = round(RetailMarket.Percentage(row) / 100 * nDataRetailMarket) + idxStart;
   dataRetailMarket(idxStart:idxStop) = RetailMarket.COC(row);
   idxStart = idxStop + 1;
end

%% Create complete data set and dist fits
data = [dataConstruction, dataOffice, dataProduction, dataRetailMarket]';

gammaFit = fitdist(data, 'gamma');
weibFit = fitdist(data, 'weibul');
lognormFit = fitdist(data, 'Lognormal');

%% compare results
HistPlot = histogram(data, 'Normalization', 'pdf', 'EdgeColor', [0.1 0.1 0.1], 'BinWidth', 1, 'DisplayStyle', 'stairs', 'DisplayName', 'data', 'LineWidth', 1);

x = (0:0.1:18.5);
gammaCDF = gammaFit.pdf(x);
weibCDF = weibFit.pdf(x);
lognCDF = lognormFit.pdf(x);

hold on
grid on
xlabel('COC')
ylabel('Probability')
% add pdf plots
gammaLine = line(x, gammaCDF, 'DisplayName', 'gamma fit', 'Color', '#FF6A00');
weibLine = line(x, weibCDF, 'DisplayName', 'weibul fit', 'Color', '#0094FF');
lognLine = line(x, lognCDF, 'DisplayName', 'lognormal fit', 'Color', '#429400');

legend([HistPlot, gammaLine, weibLine, lognLine])
hold off