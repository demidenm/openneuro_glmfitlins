import os
import nbformat
import re
import json
import pandas as pd
import numpy as np
from IPython.display import display, Markdown
from bids.modeling import BIDSStatsModelsGraph
from bids.layout import BIDSLayout, BIDSLayoutIndexer
from nilearn.interfaces.bids import parse_bids_filename
from nilearn.image import index_img, load_img, new_img_like, mean_img
from nilearn.glm import expression_to_contrast_vector
from pyrelimri import similarity


def get_numvolumes(nifti_path_4d):
    """
    Alternative method to get number of volumes using Nilearn.
    
    Parameters:
    nifti_path(str) : Path to the fMRI NIfTI (.nii.gz) file
    
    Returns:
    Number of volumes in the fMRI data using nilearn image + shape
    """
    try:
        # Load 4D image
        img = load_img(nifti_path_4d)
        
        # Get number of volumes
        return img.shape[3] if len(img.shape) == 4 else None
    
    except Exception as e:
        print(f"Nilearn error reading file {nifti_path_4d}: {e}")
        return None


def trim_derivatives(boldpath: str, confpath: str, num_totrim: int):
    """
    Trim a specified number of initial volumes from an fMRI NIfTI file and confounds file.
    
    Parameters:
    boldpath (str) : Path to the fMRI NIfTI (.nii.gz) file
    confpath (str) : Path to the counfounds (.tsv) file
    num_totrim (int) : number of initial volumes to remove, int

    Returns:
    BOLD NIfTI, confounds dataframe
    """
    nifti_data = trim_calibration_volumes(bold_path=boldpath, num_voltotrim=num_totrim)
    confounds_data = trim_confounds(confounds_path=confpath, num_rowstotrim=num_totrim)

    return nifti_data, confounds_data


def trim_calibration_volumes(bold_path: str, num_voltotrim:int):
    """
    Trim a specified number of initial volumes from an fMRI NIfTI file.
    
    Parameters:
    bold_path (str): Path to the 4D fMRI NIfTI file (.nii or .nii.gz)
    num_voltotrim (int): Number of initial volumes to remove
    
    Returns:
    Trimmed nifti file
    """
    if not os.path.exists(bold_path):
        raise FileNotFoundError(f"File not found: {bold_path}")
    
    # load nifti & trim
    try:
        img = load_img(bold_path)
        total_vols = img.shape[3] if len(img.shape) == 4 else None
        if total_vols is None:
            raise ValueError(f"Invalid NIfTI file: {bold_path}")
        
        print("Trimming {} volumes from {} volumes".format(num_voltotrim, total_vols))
        trimmed_img = index_img(img, slice(num_voltotrim, None))

    except Exception as e:
        raise ValueError(f"Error loading NIfTI file: {e}")    
    
    return trimmed_img


def trim_confounds(confounds_path:str, num_rowstotrim:int):
    """
    Trim confounds rows by specified N of calibration volumes
    
    Parameters:
    confounds_path (str) : Path to the confounds tsv file
    num_rowstotrim (int) : Number of initial rows to remove
    
    Returns:
    modified confounds dataframe
    """
    # file exists 
    if not os.path.exists(confounds_path):
        raise FileNotFoundError(f"File not found: {confounds_path}")
    
    # load file
    try:
        confounds_df = pd.read_csv(confounds_path, sep='\t')
    except Exception as e:
        raise ValueError(f"Error reading confounds file: {e}")
    
    # Check number of rows
    total_rows = len(confounds_df)
    
    if num_rowstotrim >= total_rows:
        raise ValueError(f"Number of rows to trim ({num_rowstotrim}) exceeds total rows ({total_rows}).")
    
    # trim rows
    trimmed_df = confounds_df.iloc[num_rowstotrim:].reset_index(drop=True)
    
    return trimmed_df


def generate_tablecontents(notebook_name):
    """Generate a Table of Contents from markdown headers in the current Jupyter Notebook."""
    toc = ["# Table of Contents\n"]

    # Get the current notebook name dynamically
    notebook_path = os.getcwd()
    notebook_file = os.path.join(notebook_path, notebook_name)
    
    if not notebook_file:
        print("No notebook file found in the directory.")
        return
    
    # Load the notebook content
    with open(notebook_file, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    for cell in notebook.cells:
        if cell.cell_type == "markdown":  # Only process markdown cells
            lines = cell.source.split("\n")
            for line in lines:
                match = re.match(r"^(#+)\s+([\d.]+)?\s*(.*)", line)  # Match headers with optional numbering
                if match:
                    level = len(match.group(1))  # Number of `#` determines header level
                    header_number = match.group(2) or ""  # Capture section number if present
                    header_text = match.group(3).strip()  # Extract actual text
                    
                    # Format the anchor link correctly for Jupyter:
                    # 1. Keep original casing
                    # 2. Preserve periods
                    # 3. Replace spaces with hyphens
                    # 4. Remove special characters except `.` and `-`
                    anchor = f"{header_number} {header_text}"
                    anchor = anchor.replace(" ", "-")  # Convert spaces to hyphens
                    anchor = re.sub(r"[^\w.\-]", "", anchor)  # Remove special characters except `.` and `-`

                    toc.append(f"{'  ' * (level - 1)}- [{header_number} {header_text}](#{anchor})")

    # diplay table of contents in markdown
    display(Markdown("\n".join(toc)))


def get_bidstats_events(bids_inp, spec_cont, scan_length=125, ignored=None, return_events_num=0):
    """
    Initializes a BIDS layout, processes a BIDSStatsModelsGraph, 
    and returns a DataFrame of the first collection's entities.

    Parameters:
    - bids_inp (str): Path to the BIDS dataset.
    - spec_cont: Specification content for BIDSStatsModelsGraph.
    - scan_length (int, optional): Scan length parameter for load_collections. Default is 125.
    - ignored (list, optional): List of regex patterns to ignore during indexing.
    - return_events_num (int, optional): Number of events to return. Default is 0.

    Returns:
    - DataFrame: Data representation of the first collection with entities, or None if errors occur.
    """
    try:
        indexer = BIDSLayoutIndexer(ignore=ignored) if ignored else BIDSLayoutIndexer()
        bids_layout = BIDSLayout(root=bids_inp, reset_database=True, indexer=indexer)
    except Exception as e:
        print(f"Error initializing BIDSLayout: {e}")
        return None

    try:
        graph = BIDSStatsModelsGraph(bids_layout, spec_cont)
        graph.load_collections(scan_length=scan_length)
    except Exception as e:
        print(f"Error creating or loading BIDSStatsModelsGraph: {e}")
        return None

    try:
        root_node = graph.root_node
        colls = root_node.get_collections()
        if not colls:
            raise ValueError("No collections found in the root node.")
        return colls[return_events_num].to_df(entities=True), root_node
    except Exception as e:
        print(f"Error processing root node collections: {e}")
        return None


def extract_model_info(model_spec):
    """
    Extracts subject numbers, node levels, convolve model type, regressors, and contrasts from a BIDS model specification,
    and multiplies each condition by its corresponding weight.

    Parameters:
    model_spec (dict): The BIDS model specification dictionary.

    Returns:
    dict: A dictionary containing the extracted information, including weighted conditions.
    """

    extracted_info = {
        "subjects": model_spec.get("Input", {}).get("subject", []),
        "nodes": [],
    }

    for node in model_spec.get("Nodes", []):
        node_info = {
            "level": node.get("Level"),
            "regressors": node.get("Model", {}).get("X", []),
            "contrasts": [
                {
                    "name": contrast.get("Name", "Unnamed Contrast"),
                    "conditions": contrast.get("ConditionList", []),
                    "weights": contrast.get("Weights", []),
                    "test": contrast.get("Test", "t")  # Default test type to "t"
                }
                for contrast in node.get("Contrasts", [])
            ],
            "convolve_model": "spm",  # Default value spm
            "if_derivative_hrf": False    # Track if HRF derivative is used
        }

        # Extract HRF convolution model type and derivative status
        transformations = node.get("Transformations", {}).get("Instructions", [])
        for instruction in transformations:
            if instruction.get("Name") == "Convolve":
                node_info["convolve_model"] = instruction.get("Model", "Unknown")
                node_info["if_derivative_hrf"] = instruction.get("Derivative", "False") == "True"
                break  # Stop searching after finding first Convolve transformation

        extracted_info["nodes"].append(node_info)
    
    return extracted_info



# below est_contrast_vifs code is courtsey of Jeanette Mumford's repo: https://github.com/jmumford/vif_contrasts
def est_contrast_vifs(desmat, contrasts):
    """
    IMPORTANT: This is only valid to use on design matrices where each regressor represents a condition vs baseline
     or if a parametrically modulated regressor is used the modulator must have more than 2 levels.  If it is a 2 level modulation,
     split the modulation into two regressors instead.

    Calculates VIF for contrasts based on the ratio of the contrast variance estimate using the
    true design to the variance estimate where between condition correaltions are set to 0
    desmat : pandas DataFrame, design matrix
    contrasts : dictionary of contrasts, key=contrast name,  using the desmat column names to express the contrasts
    returns: pandas DataFrame with VIFs for each contrast
    """
    desmat_copy = desmat.copy()
    # find location of constant regressor and remove those columns (not needed here)
    desmat_copy = desmat_copy.loc[
        :, (desmat_copy.nunique() > 1) | (desmat_copy.isnull().any())
    ]
    # Scaling stabilizes the matrix inversion
    nsamp = desmat_copy.shape[0]
    desmat_copy = (desmat_copy - desmat_copy.mean()) / (
        (nsamp - 1) ** 0.5 * desmat_copy.std()
    )
    vifs_contrasts = {}
    for contrast_name, contrast_string in contrasts.items():
        try:
            contrast_cvec = expression_to_contrast_vector(
                contrast_string, desmat_copy.columns
            )
            true_var_contrast = (
                contrast_cvec
                @ np.linalg.inv(desmat_copy.transpose() @ desmat_copy)
                @ contrast_cvec.transpose()
            )
            # The folllowing is the "best case" scenario because the between condition regressor correlations are set to 0
            best_var_contrast = (
                contrast_cvec
                @ np.linalg.inv(
                    np.multiply(
                        desmat_copy.transpose() @ desmat_copy,
                        np.identity(desmat_copy.shape[1]),
                    )
                )
                @ contrast_cvec.transpose()
            )
            vifs_contrasts[contrast_name] = true_var_contrast / best_var_contrast
        except Exception as e:
            print(f"Error computing VIF for regressor '{contrast_name}': {e}")

    return vifs_contrasts


def gen_vifdf(designmat, contrastdict, nuisance_regressors):
    """
    Create a Pandas DataFrame with VIF values for regressors.

    Parameters:
    designmat: The design matrix used in the analysis.
    contrastdict (dict): dictionary containing contrast names and their corresponding expressions.
    nuisance_regressors (list): A list containing nusiance regressors to exclude.

    Returns:
    Returns regressors vif dict & DataFrame of VIFs w/ columns ['type', 'name', 'value'].
    """
    # Filter columns by removing nuisance regressors & create dictionary that excludes intercept
    filtered_columns = designmat.columns[~designmat.columns.isin(nuisance_regressors)]
    regressor_dict = {item: item for item in filtered_columns if item != "intercept"}
    reg_vifs = est_contrast_vifs(desmat=designmat, contrasts=regressor_dict)

    df_reg = pd.DataFrame(list(reg_vifs.items()), columns=["name", "value"])
    df_reg["type"] = "regressor"

    return reg_vifs, df_reg


# functions for subjects and contrasts generic files
def create_subjects_json(subj_list, studyid, taskname, specpath):
    subjects_file_path = os.path.join(specpath, f'{studyid}-{taskname}_subjects.json')
    subjects_data = {
        "Subjects": subj_list
    }
    with open(subjects_file_path, 'w') as f:
        json.dump(subjects_data, f, indent=4)
    print(f"\t\tSaved subjects file for task {taskname} to {subjects_file_path}")

def create_gencontrast_json(studyid, taskname, specpath):
    contrasts_file_path = os.path.join(specpath, f'{studyid}-{taskname}_contrasts.json')
    contrasts_data = {
        "Contrasts": [
            {
                "Name": "AvB",
                "ConditionList": ["trial_type.a", "trial_type.b"],
                "Weights": [1, -1],
                "Test": "t"
            },
            {
                "Name": "FacesvPlaces",
                "ConditionList": ["trial_type.faces", "trial_type.places"],
                "Weights": [1, -1],
                "Test": "t"
            }
        ]
    }
    with open(contrasts_file_path, 'w') as f:
        json.dump(contrasts_data, f, indent=4)
    print(f"\t\tSaved contrasts file for task {taskname} to {contrasts_file_path}")


def calc_niftis_meanstd(path_imgs):
    """
    Calculate the mean & standard deviation across a list of NIfTI images.

    Parameters:
    - images_paths: List of paths to NIfTI images.

    Returns:
    NIfTI Image for mean and std in position 1 , 2
    """
    # if path_imgs list is empty
    assert len(path_imgs) > 0, "Error: The list of image paths is empty."

    # load ref image to obtain header info
    reference_img = load_img(path_imgs[0])
    
    # load / stack image data
    loaded_images = [load_img(img_path).get_fdata() for img_path in path_imgs]
    img_data_array = np.array(loaded_images)

    # data array is not empty and has more than 1 image
    assert img_data_array.size > 0, "Error: No valid image data were loaded."
    assert img_data_array.shape[0] > 1, "Error: At least two images are required for mean and std calculation."

    # calculate the mean and std across images (axis=0)
    mean_imgs = np.mean(img_data_array, axis=0)
    std_imgs = np.std(img_data_array, axis=0, ddof=1)  # ddof=1 for sample std

    # Create NIfTI images for the mean and std
    mean_nifti = new_img_like(reference_img, mean_imgs)
    std_nifti = new_img_like(reference_img, std_imgs)

    return mean_nifti, std_nifti


def voxel_inout_ratio(img_path, mask_path):
    """
    Calculates the percentage of non-zero voxels inside and outside a brain mask 
    for a given image

    Parameters:
    img_path (str): Path to the NIfTI image file.
    mask_path (str): Path to the corresponding brain mask (same space).

    Returns:
    percent_inside: Percentage of non-zero voxels inside the brain mask.
    percent_outside: Percentage of non-zero voxels outside the brain mask.
    ratio_invout: ratio of inside versus outside 
    """
    img_nifit = load_img(img_path)
    mask_nifti = load_img(mask_path)

    # extract numpy arrays & get nonzeros
    img_data = img_nifit.get_fdata()
    mask_data = mask_nifti.get_fdata() > 0      
    nonzero_inside = np.count_nonzero(img_data[mask_data])
    nonzero_outside = np.count_nonzero(img_data[~mask_data])
    total_nonzero = nonzero_inside + nonzero_outside

    # percentages and ratio
    percent_inside = (nonzero_inside / total_nonzero) * 100 if total_nonzero != 0 else 0
    percent_outside = (nonzero_outside / total_nonzero) * 100 if total_nonzero != 0 else 0
    ratio_invout = percent_inside / percent_outside if percent_outside != 0 else float('inf')

    return percent_inside, percent_outside, ratio_invout


def similarity_boldstand_metrics(img_path, brainmask_path):
    # Parse filename to extract BIDS info
    parsed_dat = parse_bids_filename(img_path)
    sub_run_info = f"sub{parsed_dat.get('sub', 'Unknown')}_run{parsed_dat.get('run', 'Unknown')}"
    
    # dice similarity
    dice_est = similarity.image_similarity(
        imgfile1=img_path,
        imgfile2=brainmask_path,
        mask=None,
        thresh=None,
        similarity_type='dice'
    )

    perc_in, perc_out, inout_ratio =  voxel_inout_ratio(img_path=img_path, mask_path=brainmask_path)

    # results as a dictionary
    return {
        "img1": sub_run_info,
        "img2": "mni152",
        "dice": dice_est,
        "voxinmask": perc_in,
        "voxoutmask": perc_out,
        "ratio_inoutmask": inout_ratio,
    }

def get_low_quality_subs(ratio_df, percentile=10):
    """
    return a sorted list of low-quality image names based on computed bottom `percentile` threshold for 'voxoutmask' and 'dice' metrics.

    Parameters:
    ratio_df: DataFrame with 'voxoutmask', 'dice', and 'img1' columns.
    percentile: Percentile threshold to determine low quality (default is 10).

    Returns:
    Sort list of bottom percentile
    """
    voxoutmask_thresh = np.percentile(ratio_df['voxoutmask'], percentile)
    dice_thresh = np.percentile(ratio_df['dice'], percentile)

    low_quality = ratio_df[
        (ratio_df['voxoutmask'] <= voxoutmask_thresh) |
        (ratio_df['dice'] <= dice_thresh)
    ]
    
    low_quality_imgs = sorted(low_quality['img1'].tolist())
    return low_quality_imgs