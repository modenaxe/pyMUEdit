import unittest
import numpy as np
import numpy.testing as npt
import filecmp
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scipy.io import loadmat
from utils.config_and_input import openOTBplus
from utils.decomposition import notchsignals, bandpassingals, extend, demean, whiteesig, fixedpointalg, getspikes, minimizeCOVISI, calcSIL, peeloff
from utils.manual_editing import pcaesig
# order the functions by original MUedit app 
# save each output  
# compare each MUedit output to outputs by our functions
INPUT20MVCFILE = "trial1_20MVC.otb+"
INPUT40MVCFILE = "trial1_40MVC.otb+"

inputFile20 = os.path.join(os.getcwd())
inputFile40 = os.path.join(os.getcwd())


# expected outputs
expOutOpenOTBPlus = os.path.join(os.getcwd(), "ExpOut20OpentOTBplus.mat")
expOutNotchSig = os.path.join(os.getcwd(), "ExpOut20NotchSignals.mat")


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
        if not os.path.exists(expOutOpenOTBPlus):
            print("expected OpenOTBPlus output file not found!")
        expected = loadmat(expOutOpenOTBPlus)
        output = openOTBplus.openOTBplus(inputFile20, INPUT20MVCFILE, 0)
        # print(expected)
        # test data arrays are the exact same
        try:
            npt.assert_array_equal(output[1].get("data"), expected.get("signal")[0][0][0])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected data:\n{e}")
        # auxiliary 
        try:
            npt.assert_array_equal(output[1].get("auxiliary"), expected.get("signal")[0][0][1])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected auxiliary array:\n{e}")

        # auxiliary name (failing cause it needs to be array of arrays)
        try:
            npt.assert_array_equal(output[1].get("auxiliaryname"), expected.get("signal")[0][0][2])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected auxiliary name array:\n{e}")

        # fsamp (cast to uint16)
        try:
            npt.assert_array_equal(np.asarray(output[1].get("fsamp"), dtype = np.uint16), expected.get("signal")[0][0][3])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected fsamp value:\n{e}")
        
        # nChan 
        try:
            npt.assert_array_equal(np.asarray(output[1].get("nChan"), dtype = np.uint8), expected.get("signal")[0][0][4])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected nChan value:\n{e}")
        
        # ngrid 
        try:
            npt.assert_array_equal(np.asarray(output[1].get("ngrid")), expected.get("signal")[0][0][5])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected ngrid value:\n{e}")
        
        # grid name (needs to be 2 nested arrays)
        try:
            npt.assert_array_equal(np.asarray(output[1].get("gridname")), expected.get("signal")[0][0][6])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected grid names:\n{e}")
        
        # muscle (needs to be nested arrays)
        try:
            npt.assert_array_equal(np.asarray(output[1].get("muscle")), expected.get("signal")[0][0][7])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected muscle names:\n{e}")
        
        # path
        try:
            npt.assert_array_equal(np.asarray([output[1].get("path")]), expected.get("signal")[0][0][8])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected path names:\n{e}")
        # target
        try:
            npt.assert_array_equal(np.asarray([output[1].get("target")]), expected.get("signal")[0][0][9])
        except AssertionError as e:
            raise AssertionError(f"openOTBplus failed to return the expected targets:\n{e}")


# to add openIntan and openOEphys 
# to add segment sessions
# to add formatsignalHDEMG.m
    def testNotchSignals(self):
        if not os.path.exists(expOutNotchSig):
            print("expected notchsignals output file not found!")
        expected = loadmat(expOutNotchSig).get("filteredsignal")
        signals = openOTBplus.openOTBplus(inputFile20, INPUT20MVCFILE, 0)
        output = notchsignals.notchsignals(signals[1].get("data"), signals[1].get("fsamp"))
        #print(output)
        #print(type(output))
        #print(expected)
        #print(type(expected))
        try:
            npt.assert_array_equal(np.asarray(output), expected)
        except AssertionError as e:
            raise AssertionError(f"notchsignals failed to return the expected signal:\n{e}")
        

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





#if __name__ == '__main__':
#    unittest.main()
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(Test20MVCfile('testOpenOTBPlus')) 
    suite.addTest(Test20MVCfile('testNotchSignals'))
    unittest.TextTestRunner().run(suite)