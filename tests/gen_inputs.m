[dlgbox, signal] = openOTBplus('', 'trial1_20MVC.otb+', 0);
save('ExpOut20OpentOTBplus.mat')

demsignals = demean(signal.data);
save('ExpOut20Demean.mat')

[E, D] = pcaesig(signal.data);
[whitensignals, whiteningMatrix, dewhiteningMatrix] = whiteesig(signal.data, E, D);
save('ExpOut20Whiteesig.mat');

% Act like this is the first iteration.
X = whitensignals;
w = randn(size(whitensignals, 1), 1);
B = zeros(size(whitensignals, 1), 75);
w_skew = fixedpointalg(w, X, B, 500, 'skew');
w_kurtosis = fixedpointalg(w, X, B, 500, 'kurtosis');
w_logcosh = fixedpointalg(w, X, B, 500, 'logcosh');
save('ExpOut20FixedPointAlg.mat');

[icasig, spikes2] = getspikes(w_skew, X, signal.fsamp);
save('ExpOut20GetSpikes.mat');

ISI = diff(spikes2 / signal.fsamp); % Interspike interval
CoV = std(ISI) / mean(ISI); % Coefficient of variation
Wini = sum(X(:,spikes2), 2); % update W by summing the spikes

[wlast, spikeslast, CoVlast] = minimizeCOVISI(Wini, X, CoV, signal.fsamp);
save('ExpOut20MinimizeCOVISI.mat');
