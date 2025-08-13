"""
This module contains all the functions used to quantify and analyze MU
persistent inward currents.

Currently includes delta F.
"""

import pandas as pd
import numpy as np
from itertools import combinations
from core.muAnalysisCore.AnalysisResultsHist import store
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from app.muAnalysisFunctions.CommonOpenFunc import CommonOpenFunc
from sklearn.svm import SVR
from scipy.stats import iqr

def compute_deltaf(
    average_method="test_unit_average",
    normalisation="False",
    clean=True,
    recruitment_difference_cutoff=1.0,
    corr_cutoff=0.7,
    controlunitmodulation_cutoff=0.5,
):
    """
    Compute deltaF values for pairs of motor units (MUs) from EMG data.

    Parameters
    ----------
    average_method : str, optional
        Method for averaging deltaF values. Default is "test_unit_average".
    normalisation : str, optional
        Normalisation method for deltaF ("False" or "ctrl_max_desc").
    clean : bool, optional
        If True, apply exclusion criteria to remove unreliable measurements.
    recruitment_difference_cutoff : float, optional
        Minimum recruitment time difference (in seconds) between control and test units.
    corr_cutoff : float, optional
        Minimum correlation between MU discharge rates for inclusion.
    controlunitmodulation_cutoff : float, optional
        Minimum modulation in the control unit's firing rate.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing MUs and their computed deltaF values.
    """
    
    smoothfits = compute_svr()["gensvr"]
    emgfile = FileUploadFunc.file
    dfret_ret = []
    mucombo_ret = np.empty(0, int)

    # If less than 2 MUs, can not quantify deltaF
    if emgfile["NUMBER_OF_MUS"] < 2:
        dfret_ret = np.nan
        mucombo_ret = np.nan*np.ones([1, 2]) 

        delta_f = pd.DataFrame({'MU': mucombo_ret, 'dF': dfret_ret})

        return delta_f

    # If more than 2 MUs, quantify deltaF.
    # Combinations of MUs.
    combs = combinations(range(emgfile["NUMBER_OF_MUS"]), 2)

    # init
    r_ret = []
    dfret = []
    testmu = []
    ctrl_mod = []
    mucombo = []
    rcrt_diff = []
    controlmu = [] 
    for mucomb in list(combs):  # For all possible combinations of MUs
        # Extract possible MU combinations (a unique MU pair)
        mu1_id, mu2_id = mucomb[0], mucomb[1]
        # Track current MU combination
        mucombo.append((mu1_id, mu2_id))

        # First MU firings, recruitment, and decrecruitment
        if np.size(np.where(emgfile["BINARY_MUS_FIRING"][mu1_id] == 1)) == 0:
            mu1_rcrt, mu1_drcrt = 0, 0
        else:
            mu1_times = np.where(emgfile["BINARY_MUS_FIRING"][mu1_id] == 1)[0]
            mu1_rcrt, mu1_drcrt = mu1_times[1], mu1_times[-1]
        # Skip first since idr is defined on second

        # Second MU firings, recruitment, and decrecruitment
        if np.size(np.where(emgfile["BINARY_MUS_FIRING"][mu2_id] == 1)) == 0:
            mu2_rcrt, mu2_drcrt = 0, 0
        else:
            mu2_times = np.where(emgfile["BINARY_MUS_FIRING"][mu2_id] == 1)[0]
            mu2_rcrt, mu2_drcrt = mu2_times[1], mu2_times[-1]
        # Skip first since idr is defined on second

        # Region of MU overlap
        muoverlap = range(
            max(mu1_rcrt, mu2_rcrt), min(mu1_drcrt, mu2_drcrt),
        )

        # If MUs do not overlapt by more than two or more samples
        if len(muoverlap) < 2:
            dfret = np.append(dfret, np.nan)
            r_ret = np.append(r_ret, np.nan)
            rcrt_diff = np.append(rcrt_diff, np.nan)
            ctrl_mod = np.append(ctrl_mod, np.nan)
            continue  # TODO test

        # Corr between units - not always necessary, can be set to 0 when
        # desired.
        r = pd.DataFrame(
            zip(
                smoothfits[mu1_id][muoverlap],
                smoothfits[mu2_id][muoverlap],
            )
        ).corr()
        r_ret = np.append(r_ret, r[0][1])

        # Recruitment diff, necessary to ensure PICs are activated in
        # control unit.
        rcrt_diff = np.append(
            rcrt_diff, np.abs(mu1_rcrt-mu2_rcrt)/emgfile["FSAMP"],
        )
        if mu1_rcrt < mu2_rcrt:
            controlU = 1  # MU 1 is control unit, 2 is test unit

            # If control (reporter) unit is not on for entirety of test
            # unit, set last firing to control unit.
            if mu1_drcrt < mu2_drcrt:
                mu2_drcrt = mu1_drcrt
                # This may understimate PICs, other methods can be employed
            # delta F: change in control MU discharge rate between test
            # unit recruitment and derecruitment.
            df = smoothfits[mu1_id][mu2_rcrt]-smoothfits[mu1_id][mu2_drcrt]

            # Control unit discharge rate modulation while test unit is
            # firing.
            ctrl_mod = np.append(
                ctrl_mod,
                np.nanmax(smoothfits[mu1_id][range(mu2_rcrt, mu2_drcrt)])
                - np.nanmin(smoothfits[mu1_id][range(mu2_rcrt, mu2_drcrt)]),
            )

            if normalisation == "False":
                dfret = np.append(dfret, df)
            elif normalisation == "ctrl_max_desc":
                # Normalise deltaF values to control unit descending range
                # during test unit firing.
                k = smoothfits[mu1_id][mu2_rcrt]-smoothfits[mu1_id][mu1_drcrt]
                dfret = np.append(dfret, df/k)

        elif mu1_rcrt > mu2_rcrt:
            controlU = 2  # MU 2 is control unit, 1 is test unit
            if mu1_drcrt > mu2_drcrt:
                # If control (reporter) unit is not on for entirety of
                # test unit, set last firing to control unit.
                mu1_drcrt = mu2_drcrt
                # This may understimate PICs, other methods can be employed.
            # delta F: change in control MU discharge rate between test
            # unit recruitment and derecruitment.
            df = smoothfits[mu2_id][mu1_rcrt]-smoothfits[mu2_id][mu1_drcrt]

            # Control unit discharge rate modulation while test unit is
            # firing.
            ctrl_mod = np.append(
                ctrl_mod,
                np.nanmax(smoothfits[mu2_id][range(mu1_rcrt, mu1_drcrt)])
                - np.nanmin(smoothfits[mu2_id][range(mu1_rcrt, mu1_drcrt)]),
            )

            if normalisation == "False":
                dfret = np.append(dfret, df)
            elif normalisation == "ctrl_max_desc":
                # Normalise deltaF values to control unit descending range
                # during test unit firing.
                k = smoothfits[mu2_id][mu1_rcrt]-smoothfits[mu2_id][mu2_drcrt]
                dfret = np.append(dfret, df/k)

        elif mu1_rcrt == mu2_rcrt:
            if mu1_drcrt > mu2_drcrt:
                controlU = 1  # MU 1 is control unit, 2 is test unit
                # delta F: change in control MU discharge rate between
                # test unit recruitment and derecruitment.
                df = smoothfits[mu1_id][mu2_rcrt]-smoothfits[mu1_id][mu2_drcrt]

                # Control unit discharge rate modulation while test unit is
                # firing.
                ctrl_mod = np.append(
                    ctrl_mod,
                    np.nanmax(smoothfits[mu1_id][range(mu2_rcrt, mu2_drcrt)])
                    - np.nanmin(smoothfits[mu1_id][range(mu2_rcrt, mu2_drcrt)]),
                )

                if normalisation == "False":
                    dfret = np.append(dfret, df)
                elif normalisation == "ctrl_max_desc":
                    # Normalise deltaF values to control unit descending
                    # range during test unit firing.
                    k = smoothfits[mu1_id][mu2_rcrt]-smoothfits[mu1_id][mu1_drcrt]
                    dfret = np.append(dfret, df/k)
            else:
                controlU = 2  # MU 2 is control unit, 1 is test unit
                # delta F: change in control MU discharge rate between
                # test unit recruitment and derecruitment.
                df = smoothfits[mu2_id][mu1_rcrt]-smoothfits[mu2_id][mu1_drcrt]

                # Control unit discharge rate modulation while test unit is
                # firing.
                ctrl_mod = np.append(
                    ctrl_mod,
                    np.nanmax(smoothfits[mu2_id][range(mu1_rcrt, mu1_drcrt)])
                    - np.nanmin(smoothfits[mu2_id][range(mu1_rcrt, mu1_drcrt)]),
                )

                if normalisation == "False":
                    dfret = np.append(dfret, df)
                elif normalisation == "ctrl_max_desc":
                    # Normalise deltaF values to control unit descending
                    # range during test unit firing.
                    k = smoothfits[mu2_id][mu1_rcrt]-smoothfits[mu2_id][mu2_drcrt]
                    dfret = np.append(dfret, df/k)

        # Collect which MUs were control vs test
        controlmu.append(mucombo[-1][controlU-1])
        testmu.append(mucombo[-1][1-controlU//2])

    if clean:  # Remove values that dont meet exclusion criteria
        rcrt_diff_bin = rcrt_diff > recruitment_difference_cutoff
        corr_bin = r_ret > corr_cutoff
        ctrl_mod_bin = ctrl_mod > controlunitmodulation_cutoff
        clns = np.asarray([rcrt_diff_bin & corr_bin & ctrl_mod_bin])
        dfret[~clns[0]] = np.nan

    if average_method == "test_unit_average":
        # Average across all control units
        for ii in range(emgfile["NUMBER_OF_MUS"]):
            clean_indices = [
                index for (index, item) in enumerate(testmu) if item == ii
            ]
            if np.isnan(dfret[clean_indices]).all():
                dfret_ret = np.append(dfret_ret, np.nan)
            else:
                dfret_ret = np.append(
                    dfret_ret, np.nanmean(dfret[clean_indices]),
                )
            mucombo_ret = np.append(mucombo_ret, int(ii))
    else:  # Return all values and corresponding combinations
        dfret_ret = dfret
        mucombo_ret = mucombo

    delta_f = pd.DataFrame({'MU': mucombo_ret, 'dF': dfret_ret})
    
    # update results table
    store.append_analysis_hist(
        "PIC", delta_f.to_dict("records")
    )
    
    return delta_f

def compute_svr(
    gammain=1/1.6,
    regparam=1/0.370,
    endpointweights_numpulses=5,
    endpointweights_magnitude=5,
    discontfiring_dur=1.0,
):
    """
    Compute smoothed instantaneous discharge rates (IDR) for all motor units
    (MUs) using Support Vector Regression (SVR).

    Parameters
    ----------
    gammain : float, optional
        Gamma parameter for the SVR RBF kernel.
    regparam : float, optional
        Regularization parameter (C) for the SVR.
    endpointweights_numpulses : int, optional
        Number of MU pulses at each endpoint to upweight.
    endpointweights_magnitude : float, optional
        Magnitude of weight applied to endpoints.
    discontfiring_dur : float, optional
        Minimum duration (seconds) of a firing gap considered a discontinuity.

    Returns
    -------
    dict
        Dictionary containing:
        - "svrfit": list of fitted discharge rate arrays per MU.
        - "svrtime": list of corresponding time vectors per MU.
        - "gensvr": list of full-length time-aligned fitted arrays.
    """
        
    emgfile = FileUploadFunc.file
    idr = CommonOpenFunc().compute_idr(emgfile)  # Calc IDR

    svrfit_acm = []
    svrtime_acm = []
    gensvr_acm = []
    for mu in range(len(idr)):  # For all MUs
        # Skip if no data
        if idr[mu].size==0:
            svrfit_acm.append([])
            svrtime_acm.append([])
            gensvr_acm.append(np.nan*np.ones(emgfile["EMG_LENGTH"]))

        else:            # Train the model on the data.
            # Time vector, removing first element.
            xtmp = np.transpose([idr[mu].timesec[1:]])
            # Discharge rates, removing first element, since DR has been assigned
            # to second pulse.
            ytmp = idr[mu].idr[1:].to_numpy()
            # Time between discharges, will use for discontinuity calc
            xdiff = idr[mu].diff_mupulses[2:].values
            # Motor unit pulses, samples
            mup = np.array(idr[mu].mupulses[1:].values)

            # Defining weight vector. A scaling applied to the regularization
            # parameter, per sample.
            smpwht = np.ones(len(ytmp))
            smpwht[0:endpointweights_numpulses-1] = endpointweights_magnitude
            smpwht[(len(ytmp)-(endpointweights_numpulses-1)):len(ytmp)] = endpointweights_magnitude

            # Create an SVR model with a gausian kernel and supplied hyperparams.
            # Origional hyperparameters from Beauchamp et. al., 2022:
            # https://doi.org/10.1088/1741-2552/ac4594
            svr = SVR(
                kernel='rbf', gamma=gammain, C=np.abs(regparam),
                epsilon=iqr(ytmp)/11,
            )
            svr.fit(xtmp, ytmp, sample_weight=smpwht)

            # Defining prediction vector
            # From the second firing to the end of firing, in samples.
            predind = np.arange(mup[0], mup[-1]+1)
            predtime = (predind/emgfile["FSAMP"]).reshape(-1, 1)  # In time (s)
            newtm = []
            # Initialise nan vector for tracking fits aligned in time. Usefull for
            # later quant metrics.
            gen_svr = np.nan*np.ones(emgfile["EMG_LENGTH"])

            # Check for discontinous firing
            bkpnt = mup[
                np.where((xdiff > (discontfiring_dur * emgfile["FSAMP"])))[0]
            ]
            bkpnt = bkpnt[np.where(bkpnt != mup[-1])]

            if len(bkpnt) == 1:
                if bkpnt[0] == mup[0]:  # When first firing is the only discontinuity
                    bkpnt = []
                    predind = np.arange(mup[1], mup[-1]+1)
                    predtime = (predind/emgfile["FSAMP"]).reshape(-1, 1)

            # Make predictions on the data
            if len(bkpnt) > 0:  # If there is a point of discontinuity
                if bkpnt[0] == mup[0]:  # When first firing is discontinuity
                    smoothfit = np.nan*np.ones(1)
                    newtm = np.nan*np.ones(1)
                    bkpnt = bkpnt[1:]

                tmptm = predtime[
                    0: np.where(
                        (bkpnt[0] >= predind[0:-1]) & (bkpnt[0] < predind[1:])
                    )[0][0],
                ]  # Break up time vector for first continous range of firing
                smoothfit = svr.predict(tmptm)  # Predict with svr model
                newtm = np.append(newtm,tmptm,)  # Track new time vector

                tmpind = predind[
                    0: np.where(
                        (bkpnt[0] >= predind[0:-1]) & (bkpnt[0] < predind[1:])
                    )[0][0]
                ]  # Sample vector of first continous range of firing
                
                # Fill corresponding sample indices with svr fit
                gen_svr[tmpind.astype(np.int64)] = smoothfit
                # Add last firing as discontinuity
                bkpnt = np.append(bkpnt, mup[-1])
                for ii in range(len(bkpnt)-1):  # All instances of discontinuity
                    curind = np.where(
                        (bkpnt[ii] > predind[0:-1]) & (bkpnt[ii] <= predind[1:])
                    )[0][0]  # Current index of discontinuity
                    nextind = np.where(
                        (bkpnt[ii+1] > predind[0:-1]) & (bkpnt[ii+1] <= predind[1:])
                    )[0][0]  # Next index of discontinuity

                    # MU firing before discontinuity
                    curmup = np.where(mup == bkpnt[ii])[0][0]
                    curind_nmup = np.where(
                        (mup[curmup+1] > predind[0:-1]) & (mup[curmup+1] <= predind[1:])
                    )[0][0]  # MU firing after discontinuity

                    # If the next discontinuity is the next MU firing, nan fill
                    if curind_nmup >= nextind:
                        # Edge case NEED TO CHECK THE GREATER THAN CASE>> WHY TODO
                        smoothfit = np.append(smoothfit, np.nan*np.ones(1))
                        newtm = np.append(newtm, np.nan*np.ones(1))
                    else:  # Fit next continuous region of firing
                        smoothfit = np.append(
                            smoothfit,
                            np.nan*np.ones(len(predtime[curind:curind_nmup])-2),
                        )
                        smoothfit = np.append(
                            smoothfit, svr.predict(predtime[curind_nmup:nextind]),
                        )
                        newtm = np.append(
                            newtm,
                            np.nan*np.ones(len(predtime[curind:curind_nmup])-2),
                        )
                        newtm = np.append(newtm, predtime[curind_nmup:nextind],)
                        gen_svr[predind[curind_nmup:nextind]] = svr.predict(
                            predtime[curind_nmup:nextind]
                        )
            else:
                smoothfit = svr.predict(predtime)
                newtm = predtime
                gen_svr[predind] = smoothfit


            # Append fits, new time vect, time aligned fits
            svrfit_acm.append(smoothfit.copy())
            svrtime_acm.append(np.squeeze(newtm.copy()))
            gensvr_acm.append(gen_svr.copy())
            
   # Return results as dictionary
    svrfits = {
        "svrfit": svrfit_acm,
        "svrtime": svrtime_acm,
        "gensvr": gensvr_acm,
    }

    return svrfits
