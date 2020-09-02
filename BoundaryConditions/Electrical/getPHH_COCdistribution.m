%% Generate test data
data = zeros(1000, 1);
data(1:423) = 2.05;
data(424:755) = 3.44;
data(756:874) = 4.05;
data(875:965) = 4.94;
data(966:end) = 5;

%% get distribution functions
gammaFit = fitdist(data, 'gamma');
weibFit = fitdist(data, 'weibul');
lognormFit = fitdist(data, 'Lognormal');
betaFit = fitdist(data ./ 5, 'Beta');

%% compare results
HistPlot = histogram(data, 'Normalization', 'cdf', 'EdgeColor', [0.1 0.1 0.1], 'BinWidth', 0.05, 'DisplayStyle', 'stairs', 'DisplayName', 'data', 'LineWidth', 2);

x = (0:0.1:7.5);
xBeta = (0:0.01:1);
gammaCDF = gammaFit.cdf(x);
weibCDF = weibFit.cdf(x);
lognCDF = lognormFit.cdf(x);
betaCDF = betaFit.cdf(xBeta);

hold on
grid on
xlabel('COC')
ylabel('Probability')
% add pdf plots
gammaLine = line(x, gammaCDF, 'DisplayName', 'gamma fit', 'Color', '#FF6A00');
weibLine = line(x, weibCDF, 'DisplayName', 'weibul fit', 'Color', '#0094FF');
lognLine = line(x, lognCDF, 'DisplayName', 'lognormal fit', 'Color', '#429400');
betaLine = line(xBeta.*5, betaCDF, 'DisplayName', 'beta fit', 'Color', '#202020');

legend([HistPlot, gammaLine, weibLine, lognLine, betaLine])
hold off