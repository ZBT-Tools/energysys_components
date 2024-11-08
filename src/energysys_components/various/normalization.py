def norm(val_r: float,
         norm_dict: dict):
    """
    Normalize real value of real range to normalized value of normalized range.
    norm_dict = {"n":[min,max], "r":[min,max]}
    """
    return (norm_dict['n'][1] - norm_dict['n'][0]) * (val_r - norm_dict['r'][0]) / \
           (norm_dict['r'][1] - norm_dict['r'][0]) + norm_dict['n'][0]


def denorm(val_n: float,
           norm_dict: dict):
    """
    Denormalize normalized value of normalized range to denormalized value
     of real range.
    input dict structure
    norm_dict = {"n":[min,max], "r":[min,max]}
    """
    return (val_n - norm_dict['n'][0]) / (norm_dict['n'][1] - norm_dict['n'][0]) * \
           (norm_dict['r'][1] - norm_dict['r'][0]) + norm_dict['r'][0]
