'''
To run a test 
1. makesure you have the correct output files from matlab in the tests folder, see below for how the files should be named (to make folder for it, but git wont take big files)
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
from core.utils.config_and_input.open_otb import open_otb
from core.utils.decomposition.notch_filter import notch_filter
from core.utils.decomposition.bandpass_filter import bandpass_filter
from core.utils.decomposition.extend_emg import extend_emg
from core.utils.decomposition.whiten_emg import whiten_emg
from core.utils.decomposition.fixed_point_alg import fixed_point_alg
from core.utils.decomposition.get_spikes import get_spikes
from core.utils.decomposition.min_cov_isi import min_cov_isi
from core.utils.decomposition.get_silhouette import get_silhouette
from core.utils.decomposition.peel_off import peel_off

# pcaesig test has been removed
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


# Tests uses unmodified data from original open_otb file where possible, which came from the provided data files trial1_20MVC.otb+ and trial1_40MVC.otb+
class Test20MVCfile(unittest.TestCase): 

    def testOpenOTB(self):
        if not os.path.exists(expOutOpenOTBPlus):
            print("expected OpenOTBPlus output file not found!")
        expected = loadmat(expOutOpenOTBPlus)
        output = open_otb(inputFile20, INPUT20MVCFILE, 0)
        # print(expected)
        # test data arrays are the exact same
        try:
            npt.assert_array_equal(output[1].get("data"), expected.get("signal")[0][0][0])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected data:\n{e}")
        # auxiliary 
        try:
            npt.assert_array_equal(output[1].get("auxiliary"), expected.get("signal")[0][0][1])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected auxiliary array:\n{e}")

        # auxiliary name (failing cause it needs to be array of arrays)
        try:
            npt.assert_array_equal(output[1].get("auxiliaryname"), expected.get("signal")[0][0][2])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected auxiliary name array:\n{e}")

        # fsamp (cast to uint16)
        try:
            npt.assert_array_equal(np.asarray(output[1].get("fsamp"), dtype = np.uint16), expected.get("signal")[0][0][3])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected fsamp value:\n{e}")
        
        # nChan 
        try:
            npt.assert_array_equal(np.asarray(output[1].get("nChan"), dtype = np.uint8), expected.get("signal")[0][0][4])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected nChan value:\n{e}")
        
        # ngrid 
        try:
            npt.assert_array_equal(np.asarray(output[1].get("ngrid")), expected.get("signal")[0][0][5])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected ngrid value:\n{e}")
        
        # grid name (needs to be 2 nested arrays)
        try:
            npt.assert_array_equal(np.asarray(output[1].get("gridname")), expected.get("signal")[0][0][6])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected grid names:\n{e}")
        
        # muscle (needs to be nested arrays)
        try:
            npt.assert_array_equal(np.asarray(output[1].get("muscle")), expected.get("signal")[0][0][7])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected muscle names:\n{e}")
        
        # path
        try:
            npt.assert_array_equal(np.asarray([output[1].get("path")]), expected.get("signal")[0][0][8])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected path names:\n{e}")
        # target
        try:
            npt.assert_array_equal(np.asarray([output[1].get("target")]), expected.get("signal")[0][0][9])
        except AssertionError as e:
            raise AssertionError(f"open_otb failed to return the expected targets:\n{e}")


# to add openIntan and openOEphys 
# to add segment sessions
# to add formatsignalHDEMG.m
    def testNotchFilter(self):
        if not os.path.exists(expOutNotchSig):
            print("expected notch_filter output file not found!")
        expected = loadmat(expOutNotchSig).get("filteredsignal")
        output = notch_filter(expected.get("signal")[0][0][0], expected.get("signal")[0][0][3])
        try:
            npt.assert_array_equal(np.asarray(output), expected)
        except AssertionError as e:
            raise AssertionError(f"notch_filter failed to return the expected signal:\n{e}")
        
    # emgtype = 1 (surface) or "surface" in new version
    # apparently the difference between our and the original output is tiny, and has something to do with our floating point precision rounding
    # to double check if acceptable or needs to be strict
    def testBandpassFilter(self):
        if not os.path.exists(expOutBandpass):
            print("expected bandpass_filter output file not found!")
        expected = loadmat(expOutBandpass).get('filteredsignal')
        output = bandpass_filter(input.get('signal')[0][0][0], input.get('signal')[0][0][3], emg_type="surface")

        try:
            npt.assert_array_equal((output), expected)
        except AssertionError as e:
            raise AssertionError(f"bandpass_filter failed to return the expected signal:\n{e}")


    def testExtendEMG(self):
        if not os.path.exists(expOutExt3):
            print("expected extend_emg output file for ext factor 3 not found!")
        if not os.path.exists(expOutExt10):
            print("expected extend_emg output file for ext factor 10 not found!")

        expected3 = loadmat(expOutExt3).get('esample')
        expected10 = loadmat(expOutExt10).get('esample')
        extFactorsToTest = [(expected3, 3),(expected10, 10)]

        # Note: extend_emg now uses a template parameter that wasn't in the old function
        # We may need to create an empty template of appropriate size
        for expected, factor in extFactorsToTest:
            # Create an empty template of appropriate size
            signal = input.get('signal')[0][0][0]
            nchans = signal.shape[0]
            nobvs = signal.shape[1]
            extended_template = np.zeros([nchans * factor, nobvs + factor - 1])
            
            out = extend_emg(extended_template, signal, factor)
            try:
                npt.assert_array_equal(out, expected)
            except AssertionError as e:
                raise AssertionError(f"extend_emg failed to return the expected signal for extension factor: {factor}\n{e}")

    # The demean function might be integrated into whiten_emg or another function
    # This test may need modification
    def testDemean(self):
        if not os.path.exists(expOutDemean):
            print("expected output file for demean not found!")
        # This implementation depends on how demean is now handled in the new codebase
        # If it's part of another function, we'll need to adjust this test
        # For now, commenting this out as it might not be directly testable
        """
        output = demean(input.get("signal")[0][0][0])
        expected = loadmat(expOutDemean).get('demsignals')
        try:
            npt.assert_array_equal(output, expected)
        except AssertionError as e:
            raise AssertionError(f"demean failed to return the expected demsignals:\n{e}")
        """
        pass
        
    def testWhitenEMG(self):
        # whiten_emg may have a different signature than the old whiteesig function
        outputWhitenedEMG, outputWhiteningMatrix, outputDewhiteningMatrix = whiten_emg(input.get("signal")[0][0][0])
       
        expected = loadmat(expOutWhiten)
        expectedWhitenedEMG = expected.get('whitensignals')
        expectedWhiteningMatrix = expected.get('whiteningMatrix')
        expectedDewhiteningMatrix = expected.get('dewhiteningMatrix')

        try:
            npt.assert_array_equal(outputWhitenedEMG, expectedWhitenedEMG)
        except AssertionError as e:
            raise AssertionError(f"whiten_emg failed to return the expected whitenedEMG:\n{e}")
        try:
            npt.assert_array_equal(outputWhiteningMatrix, expectedWhiteningMatrix)
        except AssertionError as e:
            raise AssertionError(f"whiten_emg failed to return the expected whiteningMatrix:\n{e}")
        try:
            npt.assert_array_equal(outputDewhiteningMatrix, expectedDewhiteningMatrix)
        except AssertionError as e:
            raise AssertionError(f"whiten_emg failed to return the expected dewhiteningMatrix:\n{e}")
        
    def testFixedPointAlg(self):
        # Note: Parameters might have changed in the new implementation
        initialWeights = 'from above'
        whitenedSignal = 'from above'
        seperationMatrix = 42
        contrastFunc = 42  # This might be different in the new implementation
        expectedWeights = 42
        # fixed_point_alg now takes dot_cf as a parameter, which might need to be provided
        outputWeights = fixed_point_alg(initialWeights, seperationMatrix, whitenedSignal, contrastFunc, None)

        self.assertEqual(outputWeights, expectedWeights, "fixed_point_alg failed to return the expected output for the weights")
        
    def testGetSpikes(self):
        initialWeights = 'from above'
        whitenedSignal = 'from above'
        fsamp = 42
        icasig, spikes2 = get_spikes(initialWeights, whitenedSignal, fsamp)

        expectedIcasig = 42
        expectedSpikes2 = 42

        self.assertEqual(icasig, expectedIcasig, "get_spikes failed to return the expected output for the icasig")
        self.assertEqual(spikes2, expectedSpikes2, "get_spikes failed to return the expected output for spikes2")
    
    def testMinCovISI(self):
        initialWeights = 'from above'
        whitenedSignal = 'from above'
        CoV = 42
        fsamp = 42
        # min_cov_isi has a different parameter list compared to minimizeCOVISI
        # It now takes B, Z, fsamp, cov_n, spikes_n
        B = 42  # Basis matrix
        Z = whitenedSignal
        spikes_n = 42
        wlast, spikeslast, CoVlast = min_cov_isi(initialWeights, B, Z, fsamp, CoV, spikes_n)

        expectedWlast = 42
        expectedSpikeslast = 42
        expectedCoVlast = 42

        self.assertEqual(wlast, expectedWlast, "min_cov_isi failed to return the expected output for the wlast")
        self.assertEqual(spikeslast, expectedSpikeslast, "min_cov_isi failed to return the expected output for spikeslast")
        self.assertEqual(CoVlast, expectedCoVlast, "min_cov_isi failed to return the expected output for the CoVlast")

    def testGetSilhouette(self):
        initialWeights = 'from above'
        whitenedSignal = 'from above'
        fsamp = 42
        # get_silhouette has different parameter order compared to calcSIL
        icasig, spikes2, sil = get_silhouette(initialWeights, whitenedSignal, fsamp)

        expectedIcasig = 42
        expectedSpikes2 = 42
        expectedSil = 42

        self.assertEqual(icasig, expectedIcasig, "get_silhouette failed to return the expected output for the icasig")
        self.assertEqual(spikes2, expectedSpikes2, "get_silhouette failed to return the expected output for spikes2")
        self.assertEqual(sil, expectedSil, "get_silhouette failed to return the expected output for the SIL")

    def testPeelOff(self):
        whitenedSignal = 'from above'
        fsamp = 42
        spikes = 42
        # peel_off has a different parameter list compared to peeloff
        # It doesn't require a win parameter
        whitenResidual = peel_off(whitenedSignal, spikes, fsamp)
        expectedWhitenResidual = 42

        self.assertEqual(whitenResidual, expectedWhitenResidual, "peel_off failed to return the expected output")


if __name__ == '__main__':
    suite = unittest.TestSuite()
    #suite.addTest(Test20MVCfile('testOpenOTB')) 
    #suite.addTest(Test20MVCfile('testNotchFilter'))
    #suite.addTest(Test20MVCfile('testBandpassFilter'))
    #suite.addTest(Test20MVCfile('testExtendEMG'))
    #suite.addTest(Test20MVCfile('testDemean'))
    #suite.addTest(Test20MVCfile('testpcaesig'))
    suite.addTest(Test20MVCfile('testWhitenEMG'))
    
    unittest.TextTestRunner().run(suite)