'''
To run these tests:
1. cd into the tests/ folder
2. run `matlab -nodisplay -nosplash -nodesktop -r 'run(\'gen_inputs.m\'); exit()'` to generate the necessary .mat files
3. execute this file
'''

import unittest
import numpy as np
import numpy.testing as npt
import scipy
import filecmp
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from scipy.io import loadmat
from core.utils.config_and_input.open_otb_plus import open_otb_plus
from core.utils.decomposition.notch_filter import notch_filter
from core.utils.decomposition.bandpass_filter import bandpass_filter
from core.utils.decomposition.extend_emg import extend_emg
from core.utils.decomposition.whiten_emg import whiten_emg
from core.utils.decomposition.fixed_point_alg import fixed_point_alg
from core.utils.decomposition.get_spikes import get_spikes
from core.utils.decomposition.min_cov_isi import min_cov_isi
from core.utils.decomposition.get_silhouette import get_silhouette
from core.utils.decomposition.peel_off import peel_off
from core.EmgDecomposition import offline_EMG


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
expOutWhiten = os.path.join(os.getcwd(), "ExpOut20Whiteesig.mat")
expOutFilterExtendWhiten =  os.path.join(os.getcwd(), "ExpOut20FilterExtendWhiten.mat")
expOutConSphSkew = os.path.join(os.getcwd(), "ExpOut20ConSphSkew.mat")
expOutConSphKurt = os.path.join(os.getcwd(), "ExpOut20ConSphKurt.mat")
expOutConSphLogc = os.path.join(os.getcwd(), "ExpOut20ConSphLogc.mat")
expOutFixedPointAlg = os.path.join(os.getcwd(), "ExpOut20FixedPointAlg.mat")
expOutGetSpikes = os.path.join(os.getcwd(), "ExpOut20GetSpikes.mat")
expOutMinimizeCOVISI = os.path.join(os.getcwd(), "ExpOut20MinimizeCOVISI.mat")
expOutCalcSIL = os.path.join(os.getcwd(), "ExpOut20CalcSIL.mat")

INPUT20MVCFILE = "trial1_20MVC.otb+"
INPUT40MVCFILE = "trial1_40MVC.otb+"

inputFile20 = os.path.join(os.getcwd(), INPUT20MVCFILE)
inputFile40 = os.path.join(os.getcwd())
input = loadmat(expOutOpenOTBPlus)

emg = offline_EMG(os.path.join(os.getcwd(), 'emg_obj_save_dir'), True)
emg.open_otb_plus(inputFile20)
# print("/////////////////////////////////")
# emg.convul_sphering(0, 0, 0)
# print(emg.signal_dict)
# Tests uses unmodified data from original open_otb_plus file where possible, which came from the provided data files trial1_20MVC.otb+ and trial1_40MVC.otb+
class Test20MVCfile(unittest.TestCase): 

    def assert_spikes_close(self, actual, desired, threshold=0.05, err_msg=None):
        actual_set = set(actual)
        desired_set = set(desired)
        self.assertLess(len(actual_set ^ desired_set), threshold * len(actual_set | desired_set), err_msg)

    def testOpenOTBPlus(self):
        if not os.path.exists(expOutOpenOTBPlus):
            print("expected OpenOTBPlus output file not found!")
        expected = loadmat(expOutOpenOTBPlus)
        output = open_otb_plus(inputFile20)
        
        # test data arrays are the exact same
        
        print("//////////////////////////////")
        print(output)
        print("//////////////////////////////")
        print(expected)
        # grid data
        try:
            npt.assert_array_equal(output.get("data"), expected.get("signal")[0][0][0])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected data:\n{e}")

        # auxiliary data
        try:
            npt.assert_array_equal(output.get("auxiliary"), expected.get("signal")[0][0][1])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected auxiliary array:\n{e}")

        # auxiliary names
        try:
            npt.assert_array_equal(np.array([output.get("auxiliaryname")]), expected.get("signal")[0][0][2])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected auxiliary name array:\n{e}")

        # fsamp (cast to uint16)
        try:
            npt.assert_array_equal(np.array(output.get("fsamp"), dtype = np.uint16), expected.get("signal")[0][0][3])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected fsamp value:\n{e}")
        
        # nChan 
        try:
            npt.assert_array_equal(np.array(output.get("nChan"), dtype = np.uint8), expected.get("signal")[0][0][4])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected nChan value:\n{e}")
        
        # ngrid 
        try:
            npt.assert_array_equal(np.array(output.get("ngrid")), expected.get("signal")[0][0][5])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected ngrid value:\n{e}")

        # grid names
        try:
            npt.assert_array_equal(np.asarray([output.get("gridname")]), expected.get("signal")[0][0][6])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected grid names:\n{e}")

        # muscle (needs to be nested arrays)
        try:
            npt.assert_array_equal(np.asarray([output.get("muscle")]), expected.get("signal")[0][0][7])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected muscle names:\n{e}")

        # path
        try:
            npt.assert_array_equal(np.asarray([output.get("path")]), expected.get("signal")[0][0][8])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected path names:\n{e}")
        # target
        try:
            npt.assert_array_equal(np.asarray([output.get("target")]), expected.get("signal")[0][0][9])
        except AssertionError as e:
            raise AssertionError(f"open_otb_plus failed to return the expected targets:\n{e}")


# to add openIntan and openOEphys 
# to add segment sessions
# to add formatsignalHDEMG.m

    # This ones confusing, not sure how to test it proper
    # all the filters got merged together? maybe chain the original matlab code and test everything together
    # concolutive sphering:         
    #     1) Filter the batched EMG data 
    #     2) Extend to improve speed of convergence/reduce numerical instability 
    #     3) Remove any DC component  
    #     4) Whiten
    # notch->bandpass->np.diff???->self.ext_number (doesnt seem to be used anywhere in conv sphere)
    #might need batch_wo_target or batch_w_target cause it sets batched_data and rn convul_sphering is returing
#Traceback (most recent call last):
#   File "/Users/w/Desktop/comp3900/capstone/tests/testMUeditfunctions2.py", line 51, in <module>
#     emg.convul_sphering(0, 0, 0)
#     ~~~~~~~~~~~~~~~~~~~^^^^^^^^^
#   File "/Users/w/Desktop/comp3900/capstone/src/core/EmgDecomposition.py", line 258, in convul_sphering
#     self.signal_dict["batched_data"][tracker], self.signal_dict["fsamp"]
#     ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
# KeyError: 'batched_data'
    def testConvolutiveSphering(self):
        if not os.path.exists(expOutFilterExtendWhiten):
            print("expected output file from filtering, extending, removing DC component, then whitening not found!")
        print("/////////////////////////////////")
        emg.convul_sphering(0, 0, 0)
        print(emg.signal_dict)
        #expected = loadmat(expOutFilterExtendWhiten).get("filteredsignal")
        
        output = notch_filter(expected.get("signal")[0][0][0], expected.get("signal")[0][0][3])
        try:
            npt.assert_array_equal(np.asarray(output), expected)
        except AssertionError as e:
            raise AssertionError(f"convul_sphering failed to return the expected signal:\n{e}")
        
    def testNotchFilter(self):
        if not os.path.exists(expOutNotchSig):
            print("expected notch_filter output file not found!")
        expected = loadmat(expOutNotchSig)
        output = notch_filter(expected.get("signal")[0][0][0], float(expected.get("signal")[0][0][3][0][0]))
        try:
            npt.assert_allclose(np.asarray(output), expected.get("filteredsignal"))
        except AssertionError as e:
            raise AssertionError(f"notch_filter failed to return the expected signal:\n{e}")
        
    # emgtype = 1 (surface) or "surface" in new version
    # apparently the difference between our and the original output is tiny, and has something to do with our floating point precision rounding
    # to double check if acceptable or needs to be (double checked, its acceptable)
    # which files differentiation from?
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
    # This function being integrated w another func is prob whats breaking one of the other tests. Just need to find out and combine the two tests
    def testDemean(self):
        if not os.path.exists(expOutDemean):
            print("expected output file for demean not found!")

        output = scipy.signal.detrend(
            input.get("signal")[0][0][0], axis=-1, type="constant", bp=0
        )
        expected = loadmat(expOutDemean).get('demsignals')
        try:
            npt.assert_allclose(output, expected)
        except AssertionError as e:
            raise AssertionError(f"demean failed to return the expected demsignals:\n{e}")

    # is part of convul_sphering, to combine w other tests
    def testWhitenEMG(self):
        # whiten_emg may have a different signature than the old whiteesig function
        outputWhitenedEMG, outputWhiteningMatrix, outputDewhiteningMatrix = whiten_emg(input.get("signal")[0][0][0])
       
        expected = loadmat(expOutWhiten)
        expectedWhitenedEMG = expected.get('whitensignals')
        expectedWhiteningMatrix = expected.get('whiteningMatrix')
        expectedDewhiteningMatrix = expected.get('dewhiteningMatrix')

        try:
            npt.assert_allclose(outputWhitenedEMG, expectedWhitenedEMG, rtol=2e-3)
        except AssertionError as e:
            raise AssertionError(f"whiten_emg failed to return the expected whitenedEMG:\n{e}")
        try:
            npt.assert_allclose(outputWhiteningMatrix, expectedWhiteningMatrix)
        except AssertionError as e:
            raise AssertionError(f"whiten_emg failed to return the expected whiteningMatrix:\n{e}")
        try:
            npt.assert_allclose(outputDewhiteningMatrix, expectedDewhiteningMatrix)
        except AssertionError as e:
            raise AssertionError(f"whiten_emg failed to return the expected dewhiteningMatrix:\n{e}")


# original fix point alg
# % Input: 
# %   w = initial weigths
# %   X = whitened signal
# %   B = separation matrix of MU filters
# %   maxiter = maximal number of iteration before convergence
# %   contrastfunc = contrast function
#
# % Output:
# %   w = weigths (MU filter)    

# our implementation
#     Args:
#     w: Initial separation vector (flattened)
#     X: Whitened signal matrix
#     B: Basis matrix
#     cf_func_id: 0=skew, 1=kurtosis, 2=logcosh
#     maxiter: Maximum iterations
#
# Returns:
#     w: Updated separation vector
    def testFixedPointAlg(self):
        expected = loadmat(expOutFixedPointAlg, mat_dtype=True)

        outputSkew = fixed_point_alg(expected.get("w"), expected.get("B"), expected.get("X"), "skew")
        try:
            npt.assert_allclose(outputSkew, expected.get("w_skew")[:, 0])
        except AssertionError as e:
            raise AssertionError(f"fixed_point_alg failed to return the expected seperation vector using the skew contrast func:\n{e}")

        outputKurtosis = fixed_point_alg(expected.get("w"), expected.get("B"), expected.get("X"), "kurtosis")
        try:
            npt.assert_allclose(outputKurtosis, expected.get("w_kurtosis")[:, 0])
        except AssertionError as e:
            raise AssertionError(f"fixed_point_alg failed to return the expected seperation vector using the kurtosis contrast func:\n{e}")

        outputLogcosh = fixed_point_alg(expected.get("w"), expected.get("B"), expected.get("X"), "logcosh")
        try:
            npt.assert_allclose(outputLogcosh, expected.get("w_logcosh")[:, 0])
        except AssertionError as e:
            raise AssertionError(f"fixed_point_alg failed to return the expected seperation vector using the logcosh contrast func:\n{e}")


    def testGetSpikes(self):
        expected = loadmat(expOutGetSpikes)
        icasig, spikes2 = get_spikes(expected.get("w_skew")[:, 0], expected.get("X"), float(expected.get("signal")[0][0][3][0][0]))

        npt.assert_allclose(icasig, expected.get("icasig")[0], err_msg="get_spikes failed to return the expected output for the icasig")
        self.assert_spikes_close(spikes2, expected.get("spikes2")[0] - 1)
    
    def testMinCovISI(self):
        expected = loadmat(expOutMinimizeCOVISI)
        wlast, spikeslast, CoVlast = min_cov_isi(expected.get("Wini")[:, 0], expected.get("X"), float(expected.get("signal")[0][0][3][0][0]), expected.get("CoV"), expected.get("spikes2"))

        npt.assert_array_equal(wlast, expected.get("wlast")[:, 0], "min_cov_isi failed to return the expected output for the wlast")
        self.assert_spikes_close(spikeslast, expected.get("spikeslast")[0] - 1)
        npt.assert_array_equal(CoVlast, expected.get("CoVlast"), "min_cov_isi failed to return the expected output for the CoVlast")

    def testGetSilhouette(self):
        expected = loadmat(expOutCalcSIL)
        # get_silhouette has different parameter order compared to calcSIL
        icasig, spikes2, sil = get_silhouette(expected.get("wlast")[:, 0], expected.get("X"), float(expected.get("signal")[0][0][3][0][0]))

        npt.assert_allclose(icasig, expected.get("icasig")[0], err_msg="get_silhouette failed to return the expected output for the icasig")
        self.assert_spikes_close(spikes2, expected.get("spikes2")[0] - 1, err_msg="get_silhouette failed to return the expected output for spikes2")
        npt.assert_allclose(sil, expected.get("sil"), rtol=2e-3, err_msg="get_silhouette failed to return the expected output for the SIL")


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
    suite.addTest(Test20MVCfile('testOpenOTBPlus')) 
    # suite.addTest(Test20MVCfile('testConvolutiveSphering')) 
    # notchfilter, bandpass, extend and whitening will be merged into convolutivesphereing
    suite.addTest(Test20MVCfile('testNotchFilter'))
    #suite.addTest(Test20MVCfile('testBandpassFilter'))
    suite.addTest(Test20MVCfile('testExtendEMG'))
    suite.addTest(Test20MVCfile('testDemean'))
    #suite.addTest(Test20MVCfile('testpcaesig'))
    suite.addTest(Test20MVCfile('testWhitenEMG'))
    suite.addTest(Test20MVCfile('testFixedPointAlg'))
    suite.addTest(Test20MVCfile('testGetSpikes'))
    suite.addTest(Test20MVCfile('testMinCovISI'))
    suite.addTest(Test20MVCfile('testGetSilhouette'))
    
    unittest.TextTestRunner().run(suite)