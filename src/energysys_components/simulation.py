"""
Energy Conversion Component - Simulation class
"""
import pandas as pd
from energysys_components.energy_conversion import ECCState, EnergyConversionComponent, ECCParameter


class Simulation:
    """
    Simulation class
    """

    def __init__(self,
                 component_parameter: ECCParameter,
                 loadprofile: list = None,
                 timestep: int = 1,
                 initial_state: ECCState = None
                 ):
        """
        :param par:         ECCParameter dataclass object
        :param state:       ECCState dataclass object
        :param ts:          timestep [min]
        # :param debug:     bool, not implemented yet
        """

        self.component = EnergyConversionComponent(par=component_parameter,
                                                   ts=timestep,
                                                   state=initial_state)
        self.loadprofile = loadprofile

        # Result DataFrame Initialization
        state_attr = [a for a in dir(ECCState()) if not a.startswith('__')]
        self.results = pd.DataFrame(columns=state_attr)
        # Initial state
        self.results.loc[0] = vars(ECCState())

    def run(self):
        for ix, loadtarget in enumerate(self.loadprofile):
            self.component.apply_control(loadtarget)
            self.results = pd.concat([self.results,
                                      pd.DataFrame([vars(self.component.state)])],
                                     axis=0,  ignore_index=True)


