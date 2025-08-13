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
                 timestep_s: int = 1,
                 initial_state: ECCState = None
                 ):
        """
        :param component_parameter: ECCParameter dataclass object
        :param initial_state:       ECCState dataclass object
        :param timestep:            timestep [min]
        # :param debug:             bool, not implemented yet
        """
        self.timestep_s =timestep_s
        self.component = EnergyConversionComponent(par=component_parameter,
                                                   ts=timestep_s,
                                                   state=initial_state)
        self.loadprofile = loadprofile

        # Result DataFrame Initialization
        state_attr = [a for a in dir(ECCState()) if not a.startswith('__')]
        self.results = pd.DataFrame(columns=state_attr)
        # Initial state
        self.results.loc[0] = vars(ECCState())

    def run(self):
        run_res_c=[]
        # initial state
        c_state = self.component.export_state(add_timestep=0, add_index=0)
        run_res_c.append(c_state)

        for ix, loadtarget in enumerate(self.loadprofile):
            self.component.apply_control(loadtarget)
            c_state = self.component.export_state(add_timestep=(ix+1)*self.timestep_s, add_index=ix+1)
            run_res_c.append(c_state)
        run_res_c = pd.DataFrame(run_res_c)


        self.results = pd.concat([self.results,
                                      run_res_c],
                                     axis=0,  ignore_index=True)


