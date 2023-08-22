def norm(val, prop):
    """
    input string uses self.prop dict for limits
    prop= {"n":[min,max], "r":[min,max]}
    """
    return (prop['n'][1] - prop['n'][0]) * (val - prop['r'][0]) / \
           (prop['r'][1] - prop['r'][0]) + prop['n'][0]


def denorm(val, prop):
    """
    input dict structure
    prop= {"n":[min,max], "r":[min,max]}
    """
    return (val - prop['n'][0]) / (prop['n'][1] - prop['n'][0]) * \
           (prop['r'][1] - prop['r'][0]) + prop['r'][0]