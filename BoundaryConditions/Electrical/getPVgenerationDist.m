% Find distribution function for auxiliary power demand of BSL agents and
% some PHH agents
% The distribution should have the following properties:
%    - Min. Value 10%
%    - Max. Value 100%
%    - Mean 40%

close all

% start parameter
x = 10:0.1:100;

p0 = [6.5, 1876.4, 41.92];
% show starting curve
fx = FPD(x, p0(1), p0(2), p0(3));
figure('Name', 'CurvePlot');
plt = plot(x, fx);
xlabel("aux. power demand");
ylabel("Probability");

% get optimal parameters
options = optimset('PlotFcns',@optimplotfval);
%[Opt, fval] = fminsearch(@(param)getErrorWeib(x, param), [1, 3, 45], options);

options.MaxFunEvals = 1e3;
[Opt, fval] = fminsearch(@(param)getErrorFPD(x, param), p0, options);

% Test of different distributions
% Probability density function for scaled x
% weibul
function f = weibPD(x, lambda, k, scale)
    x = (x - 10) / scale;
    f = k ./ lambda .* (x ./ lambda).^(k-1) .* exp(-(x ./ lambda).^k);
end

%F-Distribution
function f = FPD(x, m, n, scale)
    x = (x - 10) / scale;
    f = fpdf(x, m, n);
end

% error functions for optimisation
function e = getErrorWeib(x, LaKSc)
    f = weibPD(x, LaKSc(1), LaKSc(2), LaKSc(3));
    % update only if allowed solution
    if isreal(f)
        fh = findobj( 'Type', 'Figure', 'Name', 'CurvePlot' );
        ax = fh.Children(1);
        ax.Children(1).YData = f;
        refreshdata
        drawnow
        e = f(end);
        meanWeibPD = LaKSc(1) * gamma(1 + 1/LaKSc(2));
        e = e + (40-(meanWeibPD*LaKSc(3)+10))^2;
    else
        e = 1e9;
    end
end

% error functions for optimisation
function e = getErrorFPD(x, MNSc)
    f = FPD(x, MNSc(1), MNSc(2), MNSc(3));
    % update only if allowed solution
    if isreal(f)
        fh = findobj( 'Type', 'Figure', 'Name', 'CurvePlot' );
        ax = fh.Children(1);
        ax.Children(1).YData = f;
        refreshdata
        drawnow
        % punish high probabilities at the end
        e = f(end);
        % punish difference of mean to 40% in scaled x
        [meanFPD, ~] = fstat(MNSc(1), MNSc(2));
        e = e + (40-(meanFPD*MNSc(3)+10))^2;
        % punish wide areas with very low probabilities
        df = abs(diff(f));
        e = e + 1000 * (0.01 - min(df))^2;
    else
        e = 1e9;
    end
end