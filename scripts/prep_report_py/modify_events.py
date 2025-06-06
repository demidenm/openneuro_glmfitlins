import os
import pandas as pd
import numpy as np
from pathlib import Path


def add_reactiontime_regressor(eventsdf, trial_type_col='trial_type', resp_trialtype: list = ['response'], 
                                response_colname: str = 'response_time', rtreg_name: str ='rt_reg', 
                                onset_colname: str = 'onset', duration_colname: str = 'duration', 
                                new_trialtype: str = None, resp_in_ms: bool = False):
    """
    Pull reaction time regressor rows and add them to the dataframe as regressor.
    Assumes reaction times are in milliseconds; converts [times] / 1000 to convert to seconds for "duration".

    Parameters
    ----------
    eventsdf : DataFrame containing event data with response times.
    trial_type_col (str): Column name for identifying response trials.
    resp_trialtype (list): Values in trial_type_col that have associated response times.
    response_colname (str): Column name containing response time.
    rtreg_name (str): Name for new reaction time regressor.
    onset_colname (str): Name for onset times column.
    duration_colname (str): Name for duration times column.
    new_trialtype (str): Column name to store the new regressor trial type.
    resp_in_ms (bool): Whether response time is in milliseconds (convert to seconds if True).

    Returns
    -------
    DataFrame with reaction time regressor rows added.
    """
    # Set name for new s column
    new_trial_name = new_trialtype if new_trialtype else trial_type_col

    if isinstance(resp_trialtype, str):
        resp_trialtype = [resp_trialtype]

    # Filter and copy relevant rows
    rt_reg_rows = eventsdf[eventsdf[trial_type_col].isin(resp_trialtype)].copy()
    rt_reg_rows[new_trial_name] = rtreg_name

    # Compute duration
    if resp_in_ms:
        rt_reg_rows[duration_colname] = rt_reg_rows[response_colname] / 1000
    else:
        rt_reg_rows[duration_colname] = rt_reg_rows[response_colname]

    # Replace NAs with 0 and report how many were replaced
    na_count = rt_reg_rows[duration_colname].isna().sum()
    rt_reg_rows[duration_colname] = rt_reg_rows[duration_colname].fillna(0)

    print(f"[INFO] Replaced {na_count} missing or None RT duration values with 0.")

    # Select relevant columns and concatenate
    rt_reg_rows = rt_reg_rows[[onset_colname, duration_colname, new_trial_name]]

    # sort and reset to avoid fitlins convolution error
    result_rts = pd.concat([eventsdf, rt_reg_rows], ignore_index=True).sort_values(by="onset", ascending=True).reset_index(drop=True)
    
    return result_rts


def ds003425(eventspath: str, task: str):
    """
    Process event data for ds003425 by modifying trial types if applicable. 
    Per DOI: 10.1038/s41598-022-05019-y, 'As noted previously we modelled CS+ reinforced (i.e., shock) trials and the first and last CS− trials as two 
    separate regressors that were not used in higher-level analyses (they were modelled similar to the conditions of interest).'
    Shock = 1=csp shock in events files
    CS- trials 4=csm and 5=csmi in events files
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["learning", "prelearning", "regulate"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        # Only modify if trial_type does NOT contain 6
        if 6 not in eventsdat['trial_type'].values:
            # Filter events where trial_type is 4 or 5
            filtered_events = eventsdat[eventsdat['trial_type'].isin([4, 5])]

            if not filtered_events.empty:
                # first and last row from the filtered events
                first_and_last_events = filtered_events.iloc[[0, -1]].copy()
                first_and_last_events['trial_type'] = 6

                # Append modified first and last events back to the original dataset
                eventsdat = pd.concat([eventsdat, first_and_last_events], ignore_index=True)
                return eventsdat
        else:
            print(f"Trial type value '6' already contained in events file. Skipping modification for {os.path.basename(eventspath)}")
            return None
    else:
        return None


def ds000002(eventspath: str, task: str):
    """
    Process event data for ds000002 by modifying trial types if applicable. 
    Per DOI: 10.1016/j.neuroimage.2005.08.010, 'PCL trials alone were modeled ...  A nuisance regressor was added, 
    which consisted of trials on which no response was made.'
    
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["deterministicclassification", "mixedeventrelatedprobe", "probabilisticclassification"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        if "missed" in eventsdat['trial_type'].values or eventsdat['trial_type'].isna().any():
            # dropping unclear NaN values -- rest blocks?
            eventsdat = eventsdat.dropna(subset=['duration', 'trial_type'])

            # A nuisance regressor was added, which consisted of trials on which no response was made 
            # setting as trial_type == 'missed'. Will convolve and include as nuisance
            eventsdat.loc[eventsdat['response_time'].isna(), 'trial_type'] = 'missed'
            return eventsdat_cpy

        else:
            print(f"Trial type value 'missed' already contained in events file. Skipping modification for {os.path.basename(eventspath)}")
            return None

def ds000102(eventspath: str, task: str):
    """
    Process event data for ds000102: adding rt regressor. 

    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["flanker"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        if "rt_reg" not in eventsdat['trial_type'].values:
            # create rt regressor

            # RT appears important, adding RT 'rt_reg' into trial_type column. Missed is included, set to 0 by func since NaN
            # include 'rt_reg' in spec file
            eventsdat_cpy = eventsdat.copy()
            cols_rt = ['congruent_correct', 'incongruent_incorrect', 'incongruent_correct', 'congruent_incorrect'] 
            eventsdat_cpy = add_reactiontime_regressor(eventsdf=eventsdat_cpy, trial_type_col='trial_type', resp_trialtype = cols_rt, 
            response_colname = 'response_time', rtreg_name ='rt_reg', resp_in_ms = False)
            
            # Sort by 'onset' column from low to high
            eventsdat_cpy = eventsdat_cpy.sort_values(by='onset', ascending=True)
            return eventsdat_cpy

        else:
            print(f"Trial type value 'missed' already contained in events file. Skipping modification for {os.path.basename(eventspath)}")
            return None



def ds000109(eventspath: str, task: str):
    """
    Process event data for ds000109 by modifying trial types if applicable. 
    Per DOI: 10.1523/JNEUROSCI.5511-11.2012, Dropping NaN in timing columns that are incorrect
    
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["theoryofmindwithmanualresponse"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        # Check if there are any NAs in the specified columns or trial_type has spaces
        if eventsdat[['onset', 'duration', 'trial_type']].isna().any().any() or eventsdat['trial_type'].str.contains(r'\s', na=False).any():
            print("**NaN dropped and trial_type spaces removed**")
            # Only run this if there are NAs in those columns
            eventsdat_cpy = eventsdat.dropna(subset=['onset', 'duration', 'trial_type'])
            eventsdat_cpy.loc[:, 'trial_type'] = eventsdat_cpy['trial_type'].str.replace(' ', '')

            return eventsdat_cpy
        else:
            print("No NaNs or spaces found in the specified columns. Skipping modification.")
            return None


def ds000115(eventspath: str, task: str):
    """
    Process event data for ds000115 by modifying trial types if applicable. 
    Modifying to not use '-' in python column names. Do not use '_' to replace as that is a parsing value in PyBIDS
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["letter0backtask", "letter1backtask", "letter2backtask"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        # Check if there are hyphens or whitespace in 'trial_type'
        if eventsdat['trial_type'].astype(str).str.contains(r'[-\s]', na=False).any():
            print("Cleaning 'trial_type' values: removing hyphens and spaces")
            # remove hyphens and whitespace from 'trial_type'
            eventsdat.loc[:, 'trial_type'] = eventsdat['trial_type'].str.replace(r'[-\s]', '', regex=True)
            return eventsdat

        else:
            print("No spaces or hyphens found in the specified columns. Skipping modification.")
            return None


def ds001734(eventspath: str, task: str):
    """
    Process event data for NARPS ds001734 by modifying trial types if applicable. 
    PyBIDS Replace() transformation fails for 'NoResp" in participant_response column. Renaming to noresp

    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["MGT"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        # Check if there are hyphens or whitespace in 'trial_type'
        if "NoResp" in eventsdat['participant_response'].values:
            print("Replace NoResp with noresp in 'participant_response'")
            eventsdat.loc[eventsdat['participant_response'] == 'NoResp', 'participant_response'] = 'noresp'
 
            return eventsdat

        else:
            print(" NoResp not found in the specified columns. Skipping modification.")
            return None


def ds000148(eventspath: str, task: str):
    """
    Process event data for ds000148 by modifying trial types if applicable. 
    Modifying to not use ' ' in python column names. 
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["figure2backwith1backlures"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        # Check if there are hyphens or whitespace in 'trial_type'
        if eventsdat['trial_type'].astype(str).str.contains(r'\s', na=False).any():
            print("Cleaning 'trial_type' values: removing spaces")
            eventsdat.loc[:, 'trial_type'] = eventsdat['trial_type'].str.replace(r'\s', '', regex=True)
            return eventsdat

        else:
            print("No spaces found in the specified columns. Skipping modification.")
            return None


def ds001848(eventspath: str, task: str):
    """
    Process event data for ds001848 by modifying trial types if applicable. 
    Modifying to not use the repeating and space values
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task == "ParallelAdaptation":
        eventsdat = pd.read_csv(eventspath, sep='\t')

        # trial_type exists or contains non-null values
        if 'trial_type' not in eventsdat.columns or eventsdat['trial_type'].isnull().all():
            print("Creating 'trial_type' with remapped values removing spaces and camelcase")

            remap_dict = {}
            for val in eventsdat['Condition Name'].dropna().unique():
                first = val.split()[0]
                snake = ''
                for i, char in enumerate(first):
                    if char.isupper() and i != 0 and not first[i-1].isupper():
                        snake += '_'
                    snake += char.lower()
                remap_dict[val] = snake

            eventsdat['trial_type'] = eventsdat['Condition Name'].map(remap_dict)

            print("Unique trial types:", eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("'trial_type' already exists or is partially filled. Skipping modification.")
            return None

        

def ds002033(eventspath: str, task: str):
    """
    Process event data for ds002033 by modifying trial types if applicable. 
    Modifying to not use the repeating and space values
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task == "ChangeDetection":
        eventsdat = pd.read_csv(eventspath, sep='\t')

        # trial_type exists or contains non-null values
        if 'trial_type' not in eventsdat.columns or eventsdat['trial_type'].isnull().all():
            print("Creating 'trial_type' with remapped values removing spaces and camelcase")

            remap_dict = {}
            for val in eventsdat['Condition Name'].dropna().unique():
                first = val.split()[0]
                snake = ''
                for i, char in enumerate(first):
                    if char.isupper() and i != 0 and not first[i-1].isupper():
                        snake += '_'
                    snake += char.lower()
                remap_dict[val] = snake

            eventsdat['trial_type'] = eventsdat['Condition Name'].map(remap_dict)

            print("Unique trial types:", eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("'trial_type' already exists or is partially filled. Skipping modification.")
            return None


def ds003789(eventspath: str, task: str):
    """
    Process event data for ds003789 by modifying trial types if applicable. 
    Modifying to not use the repeating and space values
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    eventsdat = pd.read_csv(eventspath, sep='\t')

    if task in ["retrieval"]:
        # if trial_type contains updated values
        if not eventsdat['trial_type'].isin(['foil_new', 'lure_new', 'target_old', 'lure_old']).any():
            print("Modifying 'trial_type' with remapped values & dropping na")
            eventsdat['trial_type'] = eventsdat['trial_type'].replace({
                'foil new': 'foil_new',
                'lure new': 'lure_new',
                'target old': 'target_old',
                'lure old': 'lure_old'
            })
            eventsdatcpy = eventsdat.dropna(subset=['onset', 'duration', 'trial_type'])
            na_count = eventsdatcpy["response_time"].isna().sum()
            eventsdatcpy["response_time"] = eventsdatcpy["response_time"].fillna(0)

            print("Unique trial types:", eventsdatcpy['trial_type'].unique(), "Replace response NA rows:", na_count)
            return eventsdatcpy

        else:
            print("Modified 'trial_type' already exists . Skipping modification.")
            return None
        
    if task in ["encoding"]:
        #if trial_type contains updated values
        if not eventsdat['trial_type'].isin(['fixation', 'word_list1', 'word_list2', 'word_list3', 'rt_reg']).any():
            print("Modifying 'trial_type' with remapped values")
            eventsdat['trial_type'] = eventsdat['trial_type'].replace({
                '0.0': 'fixation',
                'rep1': 'word_list1',
                'rep2': 'word_list2',
                'rep3': 'word_list3'
            })
            eventsdatcpy = eventsdat.dropna(subset=['onset', 'duration', 'trial_type'])
            na_count = eventsdatcpy["response_time"].isna().sum()
            eventsdatcpy["response_time"] = eventsdatcpy["response_time"].fillna(0)
            
            print("Unique trial types:", eventsdatcpy['trial_type'].unique(), "Replace response NA rows:", na_count)
            return eventsdatcpy

        else:
            print("Modified 'trial_type' already exists . Skipping modification.")
            return None


def ds001715(eventspath: str, task: str):
    """
    Process event data for ds001715 by modifying trial types if applicable. 
    Modifying to not use the repeating and space values
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task == "dts":
        orig_to_new = {
            "SignedMotionCohRight": "signedmotion_cohright",
            "SignedColorCohRight": "signedcolor_cohright",
            "RT": "response_time",
            "isMissedTrial": "missed_trial"
        }
        eventsdat = pd.read_csv(eventspath, sep='\t')


        # if all new columns already exist
        if not all(col in eventsdat.columns for col in orig_to_new.values()):
            print("Creating new columns in snake_case and filling RT NAs with zero.")

            for orig_col, new_col in orig_to_new.items():
                if orig_col in eventsdat.columns:
                    eventsdat[new_col] = eventsdat[orig_col]
            
            eventsdat["response_time"] = eventsdat["response_time"].fillna(0)
            eventsdat["signedmotion_abs"] = abs(eventsdat["signedmotion_cohright"])
            eventsdat["signedcolor_abs"] = abs(eventsdat["signedcolor_cohright"])

            return eventsdat

        else:
            print("New columns already exist. Skipping creation.")
            return None


def ds000001(eventspath: str, task: str):
    """
    Process event data for ds000001 by modifying NA values to 0. With N/As fitlins model spec issues -- convolution doesnt work
    Modifying to not use the repeating and space values
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task == "balloonanalogrisktask":
        check_col_nans = ['cash_demean', 'control_pumps_demean', 'explode_demean', 'pumps_demean','response_time']
        eventsdat = pd.read_csv(eventspath, sep='\t')

        if eventsdat[check_col_nans].isna().any().any():
            print("Modify events to replace NaN with zero for Fitlins Models")
            eventsdat[check_col_nans] = eventsdat[check_col_nans].fillna(0)
            
            return eventsdat

        else:
            print("Columns dont contain NaN. Skipping creation.")
            return None


def ds000008(eventspath: str, task: str):
    """
    Process event data for ds000008 by modifying spaces/dashes in trialtype which are not compatible with PyBIDS transformations
    Modifying to not use the repeating and space values
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["conditionalstopsignal", "stopsignal"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        # if trial_type column contains whitespace
        if eventsdat['trial_type'].astype(str).str.contains(r'\s', na=False).any():
            print("Modifying events to remove spaces in condition names and dropping rows with NA in onset/duration/trial_type")

            # removing spaces and dashes & drop onset/duration/trial_type that contain N/A
            eventsdat['trial_type'] = eventsdat['trial_type'].str.replace(r'[-\s]', '', regex=True)
            eventsdat = eventsdat.dropna(subset=['onset', 'duration', 'trial_type'])
            print("Unique trial types:",  eventsdat['trial_type'].unique())
            
            return eventsdat
        else:
            print("No whitespace found in trial_type. Skipping modification.")
            return None


def ds002872(eventspath: str, task: str):
    """
    Process event data for ds002827 by modifying trial types if applicable. 
    Modify onset and duration, some include '.' (seconds) others ',' (suggest ms). Occurrs in error
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["illusion"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        orig_to_new = {
            "T1": "t_low",
            "T2": "t_hi",
            "P1": "p_hi",
            "P2": "p_low"
        }

        #  if there trial_type values in current matrix
        if not eventsdat['trial_type'].isin(['t_hi', 't_low', 'p_hi', 'p_low']).any():
            print("Cleaning 'trial_type' values by remapping and remiving commas in onset/duration to decimal")
            #  comma decimal separator in numeric columns
            eventsdat.loc[:, 'onset'] = eventsdat['onset'].astype(str).str.replace(',', '.').astype(float)
            eventsdat.loc[:, 'duration'] = eventsdat['duration'].astype(str).str.replace(',', '.').astype(float)
            
            
            # remap cols
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(orig_to_new)

            print("Unique trial types:",  eventsdat['trial_type'].unique())

            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None


def ds001233(eventspath: str, task: str):
    """
    Process event data for ds001233 by modifying trial types if applicable. 
    Modify onset and duration, Modifying numeric finger events to labels and make "trial_type". Remap 0 to incorr and 1 to corr for accuracy
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["cuedSFM"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        orig_to_new = {
            2: "index",
            3: "middle",
            4: "ring",
            5: "pinky"
        }
        acc = {
            0: "incorrect",
            1: "correct"
        }

        #  if there trial_type values in current matrix
        if 'trial_type' not in eventsdat.columns or not eventsdat['trialType'].isin(['index', 'middle', 'ring', 'pinky']).any():
            print("Cleaning 'trial_type' values by remapping and update correct/incc")            
            # remap cols
            eventsdat['trial_type'] = eventsdat['trialType'].replace(orig_to_new)
            eventsdat['accuracy'] = eventsdat['correct'].replace(acc)

            print("Unique trial types:",  eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None


def ds001229(eventspath: str, task: str):
    """
    Process event data for ds001229 by modifying trial types if applicable. 
    trial_type doesnt exist, create by combining category + type. Note, typo categor, categ, category in some task events
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    Returns:
    modified events files
    """

    if task in ["em","wm"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        #  if there trial_type values in current matrix
        if 'trial_type' not in eventsdat.columns:
            print("Creating 'trial_type' values by combining categ / category / categor + type")            
            # create trial_type col
            if 'categor' in eventsdat.columns:
                eventsdat['trial_type'] = eventsdat['categor'] + '_' + eventsdat['type']
            elif 'categ' in eventsdat.columns:
                eventsdat['trial_type'] = eventsdat['categ'] + '_' + eventsdat['type']
            elif 'category' in eventsdat.columns:
                eventsdat['trial_type'] = eventsdat['category'] + '_' + eventsdat['type']
            else:
                raise KeyError("Neither 'categor' nor 'category' column found in events file.")
            
            print("Unique trial types:",  eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None


def ds001297(eventspath: str, task: str):
    """
    Process event data for ds001297 by modifying trial types if applicable. 
    refactoring to make friend, control easier to compare
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    remap_dict = {
                '+fill0': 'fill',
                '+fill1': 'fill',
                '+fill2': 'fill',
                '+fill3': 'fill',
                'friend1': 'friend',
                'friend2': 'friend',
                'friend3': 'friend',
                'friend4': 'friend',
                'control1': 'control',
                'control2': 'control',
                'control3': 'control',
                'control4': 'control',
                'oddball1': 'oddball',
                'oddball2': 'oddball',
                'oddball3': 'oddball',
                'oddball4': 'oddball',
                'blank': 'blank',
                'self': 'self',
                'motor': 'motor'
            }

    if task in ["faceidentityoddball"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')
        eventsdat['old_trial_type'] = eventsdat['trial_type']

        #  if there trial_type values in current matrix
        if not eventsdat['trial_type'].isin(['friend', 'control', 'fill', 'oddball']).any():
            print("Creating new 'trial_type' values by friend*, control*, fill*, oddball*")            

            # use the mapping to replace the values in trial type
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(remap_dict)

            print("Unique trial types:",  eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None


    def ds000009(eventspath: str, task: str):
        """
        Process event data for ds000009 by modifying trial types if applicable. 
        Parameters:
        eventspath (str): path to the events .tsv file
        task (str): task name for dataset 
        
        Returns:
        modified events files
        """

        if task in ["balloonanalogrisktask"]:
            eventsdat = pd.read_csv(eventspath, sep='\t')
            eventsdat['old_trial_type'] = eventsdat['trial_type']

            #  if there trial_type values in current trial_type
            if not eventsdat['trial_type'].isin(['pumps', 'explode', 'cashout']).any():
                print("Creating new 'trial_type' and demeaned values for pumps, explosions and cashouts")           
                action_to_trial_type = {
                    'ACCEPT': 'pumps',
                    'EXPLODE': 'explode',
                    'CASHOUT': 'cashout'
                }
                eventsdat['trial_type'] = eventsdat['action'].replace(action_to_trial_type)

                # estimate pumps for trial numbers
                eventsdat['pumps_number'] = eventsdat.groupby('trial_number').cumcount() + 1

                # demean pump number only for 'pumps' rows; trial number is initial pump to end trial event, e.g. cashout or explode
                pump_mask = eventsdat['trial_type'] == 'pumps'
                mean_pumps_per_trial = eventsdat.loc[pump_mask].groupby('trial_number')['pumps_number'].transform('mean')

                # create demeaned for only pumps
                eventsdat['demeaned_pumps'] = np.nan
                eventsdat.loc[pump_mask, 'demeaned_pumps'] = eventsdat.loc[pump_mask, 'pumps_number'] - mean_pumps_per_trial

                # obtain last pump before explode/cashout & map for all rows
                terminal_pumps = eventsdat[pump_mask].groupby('trial_number')['pumps_number'].max()
                eventsdat['terminal_pump_number'] = eventsdat['trial_number'].map(terminal_pumps)

                # demeaned terminal pump number for cashout and explode events 
                eventsdat['pumpsterminal_plusone'] = eventsdat['terminal_pump_number'] + 1 # since explode/cashout is AFTER the last pump
                mean_cashout = eventsdat[eventsdat['trial_type'] == 'cashout']['pumpsterminal_plusone'].mean()
                mean_explode = eventsdat[eventsdat['trial_type'] == 'explode']['pumpsterminal_plusone'].mean()

                eventsdat['demeaned_cashout'] = np.nan
                eventsdat.loc[eventsdat['trial_type'] == 'cashout', 'demeaned_cashout'] = \
                    eventsdat['pumpsterminal_plusone'] - mean_cashout

                eventsdat['demeaned_explode'] = np.nan
                eventsdat.loc[eventsdat['trial_type'] == 'explode', 'demeaned_explode'] = \
                    eventsdat['pumpsterminal_plusone'] - mean_explode

                # parametric modulators cannot have N/A, so setting to 0
                eventsdat[['demeaned_explode', 'demeaned_cashout', 'demeaned_pumps']] = (
                    eventsdat[['demeaned_explode', 'demeaned_cashout', 'demeaned_pumps']].fillna(0)
                )

                print("Unique trial types:",  eventsdat['trial_type'].unique())
                print("When complete, update *_scans.tsv file_name column with filename")
                # ". e.g. ds000009/ -type f -name '*scans.tsv'   -exec sed -i '1s/file_name/filename/' {} \;"

                return eventsdat

            else:
                print("No old trial_types found. Skipping modification.")
                return None

        if task in ["stopsignal"]:
            eventsdat = pd.read_csv(eventspath, sep='\t')
            eventsdat['old_trial_type'] = eventsdat['trial_type']

            eventsdat = pd.read_csv(eventspath, sep='\t')

            # if trial_type column contains whitespace
            if not eventsdat['trial_type'].isin(['unsuccessfulstop', 'unuccessfulgo', 'junk', 'successfulstop', 'successfulgo']).any():
                print("Modifying events to make trial type for 'unsuccessfulstop', 'unuccessfulgo', 'junk', 'successfulstop', 'successfulgo'")
                eventsdat['trial_type'] = eventsdat['TrialOutcome'].str.lower()
                eventsdat['response_time'] = eventsdat['ReactionTime']
                
                print("Unique trial types:",  eventsdat['trial_type'].unique())
                print("When complete, update *_scans.tsv file_name column with filename")
                # ". e.g. ds000009/ -type f -name '*scans.tsv'   -exec sed -i '1s/file_name/filename/' {} \;"

                return eventsdat
            else:
                print("All types in trial_type: 'unsuccessfulstop', 'unuccessfulgo', 'junk', 'successfulstop', 'successfulgo'. Skipping modification.")
                return None
        
        if task in ["emotionalregulation"]:
            eventsdat = pd.read_csv(eventspath, sep='\t')
            eventsdat['old_trial_type'] = eventsdat['trial_type']

            eventsdat = pd.read_csv(eventspath, sep='\t')

            # if trial_type column contains whitespace
            if not eventsdat['trial_type'].isin([{'att_neut', 'suppr_neg', 'att_neg', 'rating_par'}]).any():
                print("Modifying events to make trial type for 'att_neut', 'suppr_neg', 'att_neg', 'rating_par', 'junk_rating'")
                eventsdat['trial_type'] = eventsdat['trial_type_orig']
                eventsdat['response_time'] = eventsdat['reaction_time']
                eventsdat['response_time'] = eventsdat["response_time"].fillna(0)
                
                print("Unique trial types:",  eventsdat['trial_type'].unique())
                print("When complete, update *_scans.tsv file_name column with filename")
                # ". e.g. ds000009/ -type f -name '*scans.tsv'   -exec sed -i '1s/file_name/filename/' {} \;"

                return eventsdat
            else:
                print("All types in trial_type: 'att_neut', 'suppr_neg', 'att_neg', 'rating_par'.")
                return None

        if task in ["discounting"]:
            eventsdat = pd.read_csv(eventspath, sep='\t')

            # if columsn exist
            if not eventsdat.columns.isin(['demeaned_rlglater', 'demeaned_timedelay', 'demeaned_smsooner']).any():
                print("Modifying events to make trial type for 'demeaned_rlglater','demeaned_timedelay','demeaned_smsooner'")
                eventsdat['response_time'] = eventsdat['reaction_time']
                eventsdat['response_time'] = eventsdat["response_time"].fillna(0)
                
                # creating a relative larger later versus sooner, then creating demeaned parameters for relative large later, delay days and small sooner
                eventsdat['relative_lglater'] = eventsdat['delayed_amount'] / eventsdat['immediate_amount']
                eventsdat['demeaned_rlglater'] = eventsdat['relative_lglater'] - eventsdat['relative_lglater'].mean()
                eventsdat['demeaned_timedelay'] = eventsdat['delay_time_days'] - eventsdat['delay_time_days'].mean()
                eventsdat['demeaned_smsooner'] = eventsdat['immediate_amount'] - eventsdat['immediate_amount'].mean()


                print("Unique Column types:",  eventsdat.columns)
                print("When complete, update *_scans.tsv file_name column with filename")
                # ". e.g. ds000009/ -type f -name '*scans.tsv'   -exec sed -i '1s/file_name/filename/' {} \;"

                return eventsdat
            else:
                print("All columns present. Skipping modification.")
                return None


def ds000117(eventspath: str, task: str):
    """
    Process event data for ds000117 by modifying trial types to make them easier to interpret
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    trial_type_mapping = {
        'IniFF': 'famous_initial',
        'ImmFF': 'famous_immediate',
        'DelFF': 'famous_delayed',
        'IniUF': 'unfamiliar_initial',
        'ImmUF': 'unfamiliar_immediate',
        'DelUF': 'unfamiliar_delayed',
        'IniSF': 'scrambled_initial',
        'ImmSF': 'scrambled_immediate',
        'DelSF': 'scrambled_delayed'
    }

    if task in ["facerecognition"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')
        eventsdat['old_trial_type'] = eventsdat['trial_type']

        #  if there trial_type values in current matrix
        if not eventsdat['trial_type'].isin(['famous_immediate', 'famous_delayed', 'unfamiliar_initial', 'unfamiliar_initial']).any():
            print("Creating new 'trial_type' values with more descriptive names")            

            # use the mapping to replace the values in trial type
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(trial_type_mapping)
                # dropping unclear NaN values -- rest blocks?
            eventsdat = eventsdat.dropna(subset=['trial_type'])

            print("Unique trial types:",  eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None


def ds004556(eventspath: str, task: str):
    """
    Process event data for ds004556 by modifying trial types to make them easier to interpret
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    

    if task in ["feedback"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')
        eventsdat['old_rating'] = eventsdat['rating']

        #  if rating contains na
        if eventsdat['rating'].isna().any():
            print("replacing n/a in rating with '0' to make modulation compatible w/ fitlins")            

            eventsdat['rating'] = eventsdat["rating"].fillna(0)

            print("Unique values in rating:",  eventsdat['rating'].unique())
            return eventsdat

        else:
            print("No n/a in rating col. Skipping modification.")
            return None


def ds003831(eventspath: str, task: str):
    """
    Process event data for ds003831 created mean-cented arousal and valence cols
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    

    if task in ["identify1","identify2"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        #  if columns not present
        if not eventsdat['trial_type'].isin(['exstim_valcent', 'exstim_arouscent', 'instim_valcent', 'instim_arouscent']).any():

            # grab ex_stim and in_stim trial_type rows
            ex_stim_mask = eventsdat['trial_type'] == 'ex_stim'
            in_stim_mask = eventsdat['trial_type'] == 'in_stim'

            # calc means & make mean centered cols
            mean_valence_ex = eventsdat.loc[ex_stim_mask, 'valence'].mean()
            mean_arousal_ex = eventsdat.loc[ex_stim_mask, 'arousal'].mean()
            mean_valence_in = eventsdat.loc[in_stim_mask, 'valence'].mean()
            mean_arousal_in = eventsdat.loc[in_stim_mask, 'arousal'].mean()

            # initialize with zero, as in_prep and in_feel have no corresponding arousal/valence, so no modulator hence always 0.
            eventsdat['exstim_valcent'] = 0.0
            eventsdat['exstim_arouscent'] = 0.0
            eventsdat['instim_valcent'] = 0.0
            eventsdat['instim_arouscent'] = 0.0

            # add mean-centered values for ex_stim & in_stim
            ex_stim_indices = eventsdat[ex_stim_mask].index
            eventsdat.loc[ex_stim_indices, 'exstim_valcent'] = (
                eventsdat.loc[ex_stim_indices, 'valence'] - mean_valence_ex
            )
            eventsdat.loc[ex_stim_indices, 'exstim_arouscent'] = (
                eventsdat.loc[ex_stim_indices, 'arousal'] - mean_arousal_ex
            )

            in_stim_indices = eventsdat[in_stim_mask].index
            eventsdat.loc[in_stim_indices, 'instim_valcent'] = (
                eventsdat.loc[in_stim_indices, 'valence'] - mean_valence_in
            )
            eventsdat.loc[in_stim_indices, 'instim_arouscent'] = (
                eventsdat.loc[in_stim_indices, 'arousal'] - mean_arousal_in
            )
            print("Colnames:", eventsdat.columns)

            return eventsdat

    if task in ["modulate1","modulate2"]:
        eventsdat = pd.read_csv(eventspath, sep='\t')

        #  if columns not present
        if 'reg_error' not in eventsdat.columns:
            # feel and rest have no corresponding arousal/valence, so no modulator and thus 0.
            eventsdat['fb_valence'] = eventsdat['fb_valence'].fillna(0)
            eventsdat['fb_arousal'] = eventsdat['fb_arousal'].fillna(0)
            eventsdat['reg_error'] = np.sqrt(eventsdat['fb_valence']**2 + eventsdat['fb_arousal']**2)
            print("Colnames:", eventsdat.columns)
            return eventsdat
        else:
            print("Columns present. Skipping modification.")
            return None