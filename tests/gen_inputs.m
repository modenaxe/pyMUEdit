[dlgbox, signal] = openOTBplus('', 'trial1_20MVC.otb+', 0);
save('ExpOut20OpentOTBplus.mat')

demsignals = demean(signal.data);
save('ExpOut20Demean.mat')
