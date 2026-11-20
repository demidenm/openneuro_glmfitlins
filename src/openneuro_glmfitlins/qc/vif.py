"""Variance inflation factors for regressors and contrasts."""

import numpy as np
import pandas as pd
from nilearn.glm import expression_to_contrast_vector


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
    Create a Pandas DataFrame with VIF values for contrasts and regressors.

    Parameters
    designmat: The design matrix used in the analysis.
    modconfig (dict): A dictionary containing model configuration, including:
        - 'nuisance_regressors': A regex pattern to filter out nuisance regressors.
           - 'contrasts': A dictionary of contrast definitions.

    Returns
    Returns contrasts & regressors vif dict & DataFrame of combined VIFs w/ columns ['type', 'name', 'value'].
    """
    filtered_columns = designmat.columns[~designmat.columns.isin(nuisance_regressors)]
    regressor_dict = {item: item for item in filtered_columns if item != "intercept"}

    
    # est VIFs for contrasts and regressors
    con_vifs = est_contrast_vifs(desmat=designmat, contrasts=contrastdict)
    reg_vifs = est_contrast_vifs(desmat=designmat, contrasts=regressor_dict)

    # convert to do
    df_con = pd.DataFrame(list(con_vifs.items()), columns=["name", "value"])
    df_con["type"] = "contrast"
    df_reg = pd.DataFrame(list(reg_vifs.items()), columns=["name", "value"])
    df_reg["type"] = "regressor"

    # combine & rename cols
    df = pd.concat([df_con, df_reg], ignore_index=True)
    df = df[["type", "name", "value"]]

    return con_vifs,reg_vifs,df
