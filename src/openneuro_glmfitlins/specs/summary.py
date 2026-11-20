"""Pure helpers that read information out of a BIDS Stats Models spec dict."""


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
            "convolve_inputs": [],            # Obtain regressors that were convolved
            "if_derivative_hrf": False,    # Track if HRF derivative is used
            "if_dispersion_hrf": False,    # Track if HRF dispersion is used
            "target_var": [] # Track values receiving an assignment duration (e.g. not parametric)
        }

        # Extract HRF convolution model type and derivative status
        transformations = node.get("Transformations", {}).get("Instructions", [])
        for instruction in transformations:
            if instruction.get("Name") == "Convolve":
                node_info["convolve_model"] = instruction.get("Model", "Unknown")
                node_info["if_derivative_hrf"] = instruction.get("Derivative", False) == True
                node_info["if_dispersion_hrf"] = instruction.get("Dispersion", False) == True
                node_info["convolve_inputs"] = instruction.get("Input", [])
                break  # Stop searching after finding first Convolve transformation
            
            if instruction.get("Name") == "Assign" and instruction.get("TargetAttr") == "duration":
                targets = instruction.get("Target", [])
                if isinstance(targets, str):
                    targets = [targets]
                node_info["target_var"].extend(targets)

        extracted_info["nodes"].append(node_info)
    
    return extracted_info


def pull_contrast_conditions_spec(spec_content):
    """
    get unique condition list values from spec content
    """
    condition_vals = set()
    
    # At node with contrasts, get condition lists
    for node in spec_content.get("Nodes", []):
        for contrast in node.get("Contrasts", []):
            condition_list = contrast.get("ConditionList", [])

            for condition in condition_list:
                condition_vals.add(condition)
                
    return sorted(list(condition_vals))
