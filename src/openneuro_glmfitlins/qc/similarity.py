"""R-squared map QC: mean/std images, Dice with the MNI mask and voxels in/out of mask."""

import numpy as np
from nilearn.image import load_img, new_img_like
from nilearn.interfaces.bids import parse_bids_filename
from pyrelimri import similarity


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
    parts = []
    if 'sub' in parsed_dat:
        parts.append(f"sub-{parsed_dat['sub']}")
    if 'ses' in parsed_dat:
        parts.append(f"ses-{parsed_dat['ses']}")
    if 'run' in parsed_dat:
        parts.append(f"run-{parsed_dat['run']}")

    sub_run_info = '_'.join(parts)
    
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


def get_low_quality_subs(ratio_df, dice_thresh=0.85, voxout_thresh=0.10):
    """
    Get sorted list of low-quality image names based on: 'dice' score < dice_thresh & 'voxoutmask' > voxout_thresh

    Parameters:
    ratio_df: DataFrame with 'voxoutmask', 'dice', and 'img1' columns.
    dice_thresh: Threshold for the 'dice' metric.
    voxout_thresh: Threshold for the 'voxoutmask' metric.

    Returns:
    Sorted list of image names that fall below the quality thresholds.
    """
    low_quality = ratio_df[
        (ratio_df['dice'] < dice_thresh) &
        (ratio_df['voxoutmask'] > voxout_thresh)
    ]
    
    low_quality_imgs = sorted(low_quality['img1'].tolist())
    return low_quality_imgs
