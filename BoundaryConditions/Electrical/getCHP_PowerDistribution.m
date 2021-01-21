%% Generate test data
% Electrical power of most CHP plants in germany (2019)
%  - class1 <= 0.002 MW
%  - class2 <= 0.01 MW
%  - class3 <= 0.02 MW
%  - class4 <= 0.05 MW
%  - class5 <= 0.25 MW
PeMin = 0.001;  % MW
PeClass = [0.002, 0.01, 0.02, 0.05, 0.25];  % MW
nClass = [12153, 21519, 9559, 6986, 3251];
nAll = sum(nClass);

% get propotion of each class
pClass = nClass / nAll;
pClassCum = cumsum(pClass);

% create example data set with correct distribution
data = rand(100000, 1);

mask = data <= pClassCum(1);
data(mask) = rand(sum(mask), 1) * (PeClass(1) - PeMin) + PeMin;
for cNr = 2:5
    mask = data > pClassCum(cNr-1) & data <= pClassCum(cNr);
    data(mask) = rand(sum(mask), 1) * (PeClass(cNr) - PeClass(cNr-1)) + PeClass(cNr-1);
end

%% get distribution functions
gammaFit = fitdist(data, 'gamma');
weibFit = fitdist(data, 'weibul');
lognormFit = fitdist(data, 'Lognormal');

%% compare results
x = (0:0.0001:0.275);

subplot(1, 2, 1)
HistPlotCDF = histogram(data, 'Normalization', 'cdf', ...
                       'EdgeColor', [0.1 0.1 0.1], 'BinWidth', 0.001, ...
                       'DisplayStyle', 'stairs', 'DisplayName', 'data', ...
                       'LineWidth', 2, 'EdgeAlpha', 0.4);

gammaCDF = gammaFit.cdf(x);
weibCDF = weibFit.cdf(x);
lognCDF = lognormFit.cdf(x);

hold on
grid on
title('CDF')
xlabel('Electrical Power [MW]')
ylabel('Probability')
% add pdf plots
gammaLine = line(x, gammaCDF, 'DisplayName', 'gamma fit', 'Color', '#FF6A00');
weibLine = line(x, weibCDF, 'DisplayName', 'weibul fit', 'Color', '#0094FF');
lognLine = line(x, lognCDF, 'DisplayName', 'lognormal fit', 'Color', '#429400');

legend([HistPlotCDF, gammaLine, weibLine, lognLine])
hold off

subplot(1, 2, 2)
HistPlotPDF = histogram(data, 'Normalization', 'pdf', ...
                       'EdgeColor', [0.1 0.1 0.1], 'BinWidth', 0.001, ...
                       'DisplayStyle', 'stairs', 'DisplayName', 'data', ...
                       'LineWidth', 2, 'EdgeAlpha', 0.4);

gammaPDF = gammaFit.pdf(x);
weibPDF = weibFit.pdf(x);
lognPDF = lognormFit.pdf(x);

hold on
grid on
title('PDF')
xlabel('Electrical Power [MW]')
ylabel('Number of CHP plants')
% add pdf plots
gammaLine = line(x, gammaPDF, 'DisplayName', 'gamma fit', 'Color', '#FF6A00');
weibLine = line(x, weibPDF, 'DisplayName', 'weibul fit', 'Color', '#0094FF');
lognLine = line(x, lognPDF, 'DisplayName', 'lognormal fit', 'Color', '#429400');

legend([HistPlotPDF, gammaLine, weibLine, lognLine])
hold off