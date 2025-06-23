'''
To run a test 
1. makesure you have the correct output files from matlab in the tests folder, see  below for how the files should be named (to make folder for it, but git wont take big files)
2. scroll to bottom and uncomment the desired test
3. make sure your current directory is tests 
'''

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

# expected outputs (to update such that it doesnt have to be ran in test folder)
# loadmat(expOutOpenOTBPlus).get("signal")[0][0][x] returns data, auxiliary, auxiliaryname, fsamp, nChan, ngrid, gridname, muscle, path, target
# for x = 0, 1, 2... respectively  
####################### the expected file names must match the following #########################
expOutOpenOTBPlus = os.path.join(os.getcwd(), "ExpOut20OpentOTBplus.mat")
expOutNotchSig = os.path.join(os.getcwd(), "ExpOut20NotchSignals.mat")
expOutBandpass = os.path.join(os.getcwd(), "ExpOut20BandpassingAlsSurface.mat")
expOutExt3 = os.path.join(os.getcwd(), "ExpOut20Extend3.mat")
expOutExt10 = os.path.join(os.getcwd(), "ExpOut20Extend10.mat")
expOutDemean = os.path.join(os.getcwd(), "ExpOut20Demean.mat")
expOutPcaesig = os.path.join(os.getcwd(), "ExpOut20Pcaesig.mat")
expOutWhiten = os.path.join(os.getcwd(), "ExpOut20Whiteesig.mat")

INPUT20MVCFILE = "trial1_20MVC.otb+"
INPUT40MVCFILE = "trial1_40MVC.otb+"

inputFile20 = os.path.join(os.getcwd())
inputFile40 = os.path.join(os.getcwd())
input = loadmat(expOutOpenOTBPlus)
# used for multiple functions
outputE, outputD = pcaesig.pcaesig(input.get("signal")[0][0][0])

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


# Tests uses unmodified data from original openOTBplus file where possible, which came from the provided data files trial1_20MVC.otb+ and trial1_40MVC.otb+
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
        output = notchsignals.notchsignals(expected.get("signal")[0][0][0], expected.get("signal")[0][0][3])
        #print(output)
        #print(type(output))
        #print(expected)
        #print(type(expected))
        try:
            npt.assert_array_equal(np.asarray(output), expected)
        except AssertionError as e:
            raise AssertionError(f"notchsignals failed to return the expected signal:\n{e}")
        
    # emgtype = 1 (surface)
    # apparently the difference between our and the original output is tiny, and has something to do with our floating point precision rounding
    # to double check if acceptable or needs to be strict
    def testBandpassingals(self):
        if not os.path.exists(expOutBandpass):
            print("expected bandpassingals output file not found!")
        expected = loadmat(expOutBandpass).get('filteredsignal')
        output = bandpassingals.bandpassingals(input.get('signal')[0][0][0], input.get('signal')[0][0][3], 1)

        try:
            npt.assert_array_equal((output), expected)
        except AssertionError as e:
            raise AssertionError(f"bandpassingals failed to return the expected signal:\n{e}")


    def testExtend(self):
        if not os.path.exists(expOutExt3):
            print("expected notchsignals output file for ext factor 3 not found!")
        if not os.path.exists(expOutExt10):
            print("expected notchsignals output file for ext factor 10 not found!")

        expected3 = loadmat(expOutExt3).get('esample')
        expected10 = loadmat(expOutExt10).get('esample')
        extFactorsToTest = [(expected3, 3),(expected10, 10)]

        for expected, factor in extFactorsToTest:
            out = extend.extend(input.get('signal')[0][0][0], factor)
            try:
                npt.assert_array_equal(out, expected)
            except AssertionError as e:
                raise AssertionError(f"extend failed to return the expected signal for extension factor: {factor}\n{e}")

    # failing but basically identical, floating point precision. To check if acceptable
    def testDemean(self):
        if not os.path.exists(expOutDemean):
            print("expected output file for demean not found!")
        output = demean.demean(input.get("signal")[0][0][0])
        expected = loadmat(expOutDemean).get('demsignals')
        try:
            npt.assert_array_equal(output, expected)
        except AssertionError as e:
            raise AssertionError(f"demean failed to return the expected demsignals:\n{e}")


    # failing, output matrix sizes diff and values diff, possible bug
    # seems a few of them are in the wrong order, or is the opposite sign (neg pos), also missing two rows of data each
    def testpcaesig(self):
        if not os.path.exists(expOutPcaesig):
            print("expected output file for pcaesig not found!")
        # global as it needs to be accessed again later
        # outputE, outputD = pcaesig.pcaesig(input.get("signal")[0][0][0])
        expected = loadmat(expOutPcaesig)
        expectedE = expected.get('E')
        expectedD = expected.get('D')

        try:
            npt.assert_array_equal(outputE, expectedE)
        except AssertionError as e:
            raise AssertionError(f"pcaesig failed to return the expected E matrix:\n{e}")
        try:
            npt.assert_array_equal(outputD, expectedD)
        except AssertionError as e:
            raise AssertionError(f"pcaesig failed to return the expected D matrix:\n{e}")
        
    # failing, numbers are different
    def testWhiteesig(self):
        # doesnt need E and D??? The original matlab code uses it
        outputWhitenedEMG, outputWhiteningMatrix, outputDewhiteningMatrix = whiteesig.whiteesig(input.get("signal")[0][0][0])
       
        expected = loadmat(expOutWhiten)
        expectedWhitenedEMG = expected.get('whitensignals')
        expectedWhiteningMatrix = expected.get('whiteningMatrix')
        expectedDewhiteningMatrix = expected.get('dewhiteningMatrix')

        try:
            npt.assert_array_equal(outputWhitenedEMG, expectedWhitenedEMG)
        except AssertionError as e:
            raise AssertionError(f"whiteesig failed to return the expected whitenedEMG:\n{e}")
        try:
            npt.assert_array_equal(outputWhiteningMatrix, expectedWhiteningMatrix)
        except AssertionError as e:
            raise AssertionError(f"whiteesig failed to return the expected whiteningMatrix:\n{e}")
        try:
            npt.assert_array_equal(outputDewhiteningMatrix, expectedDewhiteningMatrix)
        except AssertionError as e:
            raise AssertionError(f"whiteesig failed to return the expected dewhiteningMatrix:\n{e}")
        

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
    #suite.addTest(Test20MVCfile('testOpenOTBPlus')) 
    #suite.addTest(Test20MVCfile('testNotchSignals'))
    #suite.addTest(Test20MVCfile('testBandpassingals'))
    #suite.addTest(Test20MVCfile('testExtend'))
    #suite.addTest(Test20MVCfile('testDemean'))
    #suite.addTest(Test20MVCfile('testpcaesig'))
    suite.addTest(Test20MVCfile('testWhiteesig'))
    
    unittest.TextTestRunner().run(suite)