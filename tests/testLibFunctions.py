import unittest
import filecmp
import os
from lib import openOTBplus, notchsignals, bandpassingals, extend, demean, pcaesig, whiteesig, fixedpointalg, getspikes, minimizeCOVISI, calcSIL, peeloff
# order the functions by original MUedit app 
# save each output  
# compare each MUedit output to outputs by our functions
INPUT20MVCFILE = "trial1_20MVC.otb+"
INPUT40MVCFILE = "trial1_40MVC.otb+"

inputFile20 = os.path.join(os.getcwd(), INPUT20MVCFILE)
inputFile40 = os.path.join(os.getcwd(), INPUT40MVCFILE)

# file loaders: openOTBplus, openIntan.m and openOEphys.m
# config updaters: Quattrodlg.m, Intandlg.m, OEphysdlg.m
# segmentsession.m
# displayer: formatsignalHDEMG.m
# filters: notchsignals.m, bandpassingals.m
# extend.m
# Demean then whiten: demean.m, pcaesig.m, whiteesig.m
# fixedpointalg.m
# getspikes.m
# minimizeCOVISI.m
# accuracy assessments: calcSIL.m, peeloff.m

class Test20MVCfile(unittest.TestCase): 

    def testOpenOTBPlus(self):
        output = openOTBplus.openOTBplus(inputFile20, INPUT20MVCFILE, 1)
        # to be updated with correct output
        expected = 42
        self.assertEqual(output, expected, "openOTBplus failed to return the expected output")
# to add openIntan and openOEphys
# to add segment sessions
# to add formatsignalHDEMG.m
    def testNotchSignals(self):
        signal = 'from above'
        output = notchsignals.notchsignals(signal,1)
        expected = 42
        self.assertEqual(output, expected, "notchSignals failed to return the expected output")

    def testBandpassinggals(self):
        signal = 'from above'
        output = bandpassingals.bandpassingals(signal, 1, 1)
        expected = 42
        self.assertEqual(output, expected, "bandpassingals failed to return the expected output")

    def testExtend(self):
        signal = 'from above'
        extFactor = 1
        output = extend.extend(signal, extFactor)
        expected = 42
        self.assertEqual(output, expected, "extend failed to return the expected output")

    def testDemean(self):
        signal = 'from above'
        output = demean.demean(signal)
        expected = 42
        self.assertEqual(output, expected, "demean failed to return the expected output")
    
    def testpcaesig(self):
        signal = 'from above'
        outputE, outputD = pcaesig.pcaesig(signal)

        expectedE = 42
        expectedD = 42

        self.assertEqual(outputE, expectedE, "pcaesig failed to return the expected output for matrix E")
        self.assertEqual(outputD, expectedD, "pcaesig failed to return the expected output for matrix D")

    def testWhiteesig(self):
        signal = 'from above'
        matrixE = 'from above'
        matrixD = 'from above'
        outputWhitenedEMG, outputWhiteningMatrix, outputDewhiteningMatrix = whiteesig.whiteesig(signal, matrixE, matrixD)
       
        expectedWhitenedEMG = 42
        expectedWhiteningMatrix = 42
        expectedDewhiteningMatrix = 42

        self.assertEqual(outputWhitenedEMG, expectedWhitenedEMG, "whiteesig failed to return the expected output for the whitenedEMG")
        self.assertEqual(outputWhiteningMatrix, expectedWhiteningMatrix, "whiteesig failed to return the expected output for the whiteningMatrix")
        self.assertEqual(outputDewhiteningMatrix, expectedDewhiteningMatrix, "whiteesig failed to return the expected output for the DewhiteningMatrix")

    def testFixedPointAlg(self):
        initialWeights = 'from above'
        whitenedSignal = 'from above'
        seperationMatrix = 42
        maxiter = 42
        contrastFunc = 42
        expectedWeights = 42
        outputWeights = fixedpointalg.fixedpointalg(initialWeights, whitenedSignal, seperationMatrix, maxiter, contrastFunc)

        self.assertEqual(outputWeights, expectedWeights, "fixedPointAlg failed to return the expected output for the weights")
        
    def testGetSpikes(self):
        initialWeights = 'from above'
        whitenedSignal = 'from above'
        fsamp = 42
        icasig, spikes2 = getspikes.getspikes(initialWeights, whitenedSignal, fsamp)

        expectedIcasig = 42
        expectedSpikes2 = 42

        self.assertEqual(icasig, expectedIcasig, "getSpikes failed to return the expected output for the icasig")
        self.assertEqual(spikes2, expectedSpikes2, "getSpikes failed to return the expected output for spikes2")
    

    def testMinimizeCOVISI(self):
        initialWeights = 'from above'
        whitenedSignal = 'from above'
        CoV = 42
        fsamp = 42
        wlast, spikeslast, CoVlast = minimizeCOVISI.minimizeCOVISI(initialWeights, whitenedSignal, CoV, fsamp)

        expectedWlast = 42
        expectedSpikeslast = 42
        expectedCoVlast = 42

        self.assertEqual(wlast, expectedWlast, "minimizeCOVISI failed to return the expected output for the wlast")
        self.assertEqual(spikeslast, expectedSpikeslast, "minimizeCOVISI failed to return the expected output for spikeslast")
        self.assertEqual(CoVlast, expectedCoVlast, "minimizeCOVISI failed to return the expected output for the CoVlast")

    def testCalcSIL(self):
        initialWeights = 'from above'
        whitenedSignal = 'from above'
        fsamp = 42
        icasig, spikes2, sil = calcSIL.calcSIL(whitenedSignal, initialWeights, fsamp)

        expectedIcasig = 42
        expectedSpikes2 = 42
        expectedSil = 42

        self.assertEqual(icasig, expectedIcasig, "calcSIL failed to return the expected output for the icasig")
        self.assertEqual(spikes2, expectedSpikes2, "calcSIL failed to return the expected output for spikes2")
        self.assertEqual(sil, expectedSil, "calcSIL failed to return the expected output for the SIL")

    # %   X = whitened signal
    # %   spikes = discharge times of the motor unit
    # %   fsamp = sampling frequency
    # %   win = window to identify the motor unit action potential with spike trigger averaging
    # %   X = residual of the whitened signal
    def testPeelOff(self):
        whitenedSignal = 'from above'
        fsamp = 42
        spikes = 42
        win = 42
        whitenResidual = peeloff.peeloff(whitenedSignal, spikes, fsamp, win)
        expectedWhitenResidual = 42

        self.assertEqual(whitenResidual, expectedWhitenResidual, "peelOff failed to return the expected output")





if __name__ == '__main__':
    unittest.main()
