"""
Unified 0D energy storage component class
"""
import logging
from tqdm import tqdm
import random
from cProfile import Profile
from pstats import SortKey, Stats
from dataclasses import dataclass
import copy
from pathlib import Path

import pandas as pd
import yaml

from energysys_components.energy_carrier import ECarrier


@dataclass(frozen=False)
class ESCParameter:
    """
    Parameter of energy storage component
    """
    name: str

    # Definition of energy carriers
    E_in_mc_type: ECarrier
    E_in_sd1_type: ECarrier
    E_in_sd2_type: ECarrier
    E_out_type: ECarrier

    # Operation
    eta: float  # Const. or output dependent efficiency [-]
    C_rate: float  # This is the charge per hour rate [-] –
    # one divided by the number of hours to charge the battery fully.

    # Techno-economic
    spec_invest_cost: float  # [€/kWh]
    spec_volume: float  # [m^^3/kWh]
    spec_mass: float  # [kg/kWh]

    E_cap: float = 0  # Capacity of storage component [kWh]
    autoIncrease: bool = True  # Allows component to increase capacity on the fly during calculation

    @staticmethod
    def from_yaml(yaml_path: Path,
                  ecarrier: dict)-> dict[str, "ESCParameter"]:
        """
        Returns one or multiple ECC objects from a yaml file.

        :param ecarrier:
        :param yaml_path:
        :return:
        """
        components = dict()
        if Path.is_file(yaml_path):
            with open(yaml_path, "r") as f:
                dictionary = yaml.safe_load(f)
                for k, v in dictionary.items():
                    # Convert energy carrier strings to classes
                    try:
                        for ec in ["E_in_mc_type", "E_in_sd1_type", "E_in_sd2_type", "E_out_type"]:
                            v[ec] = ecarrier[v[ec]]
                    except KeyError:
                        raise Exception()

                    components[k] = ESCParameter(**v)
                return components
        else:
            raise FileNotFoundError(f"File {yaml_path} not found.")

    # https://stackoverflow.com/questions/33533148/how-do-i-type-hint-a-method-with-the-type-of-the-enclosing-class
    @staticmethod
    def from_dir(path: Path,
                 ecarrier: dict) -> dict[str, "ESCParameter"]:
        components = dict()
        for p in path.glob("*.yaml"):
            component_dict = ESCParameter.from_yaml(p, ecarrier=ecarrier)
            for k, v in component_dict.items():
                components[k] = v
        return components



@dataclass(frozen=False)
class ESCState:
    """
    State definition of energy storage component (ESC)
    """
    # Input
    P_in: float = 0  # [kW]
    E_in: float = 0  # [kWh]

    # Output
    P_out: float = 0  # [kW]
    E_out: float = 0  # [kWh]

    # Loss
    P_loss: float = 0  # [kW]
    E_loss: float = 0  # [kWh]

    SoC: float = 1  # State of charge 0-1, 0: empty, 1: full
    E_cap_incr: float = 0  # Required capacity increase during run


class EnergyStorageComponent:
    """
    State definition of energy storage component (ESC)
    """

    def __init__(self,
                 par: ESCParameter,
                 ts: float,
                 state: ESCState = ESCState()):
        """
        :param par: ESCParams object
        :param state: ESCState object
        :param ts: timestep [s]
        """

        self.par = par
        self.ts = ts
        self.state_initial = copy.deepcopy(state)
        self.state = state
        self.logger = logging.getLogger(__name__)

    def apply_control(self,
                      E_req: float):
        """
        Update of storage component

        :param E_req: Energy requirement [kWh],
            <0 for discharge,
            >0 for charge
        :return:
        """
        # Calculation of updated SoC
        # -----------------------------
        E_SoC_0 = self.state.SoC * self.par.E_cap  # [kWh]

        if E_req <= 0:  # ... bat. discharge
            E_SoC_1 = E_SoC_0 + E_req
            E_out = - E_req
            P_out = - E_req / (self.ts / 60 / 60)
            E_in = 0
            P_in = 0
            E_loss = 0
            P_loss = 0
        else:  # ... battery charge with efficiency
            E_SoC_1 = E_SoC_0 + self.par.eta * E_req
            E_loss = (1 - self.par.eta) * E_req
            E_out = 0
            P_out = 0
            E_in = E_req
            P_in = E_req / (self.ts / 60 / 60)
            P_loss = E_loss / (self.ts / 60 / 60)

        # If allowed and required, update capacity
        if E_SoC_1 < 0:
            if self.par.autoIncrease:
                adder = -1 * E_SoC_1
                self.par.E_cap += adder
                E_cap_incr = self.state.E_cap_incr + adder
                E_SoC_1 = 0
            else:
                raise Exception("Battery overflow")

        elif E_SoC_1 > self.par.E_cap:
            if self.par.autoIncrease:
                adder = E_SoC_1 - self.par.E_cap
                self.par.E_cap += adder
                E_cap_incr = self.state.E_cap_incr + adder
            else:
                raise Exception("Battery overflow")
        else:
            E_cap_incr = 0

        soc = E_SoC_1 / self.par.E_cap

        # Update state
        state_1 = ESCState(E_cap_incr=E_cap_incr,
                           E_in=E_in,
                           E_out=E_out,
                           E_loss=E_loss,
                           SoC=soc,
                           P_in=P_in,
                           P_loss=P_loss,
                           P_out=P_out)

        self.state = state_1
        pass

    def reset_state(self,
                    reset_capacity: bool = True):
        """
        Reset to initial state
        (e.g. for ML/RL-Algorithms)
        :return:
        """
        self.state = copy.deepcopy(self.state_initial)
        if reset_capacity:
            self.par.E_cap = 0.001


    def export_state(self,
                     add_timestep=None,
                     add_index=None)->dict:
        # Component state information
        c_data = dict()
        c_data.update(self.state.__dict__)
        if add_timestep is not None:
            c_data["time_s"]=add_timestep
        if add_index is not None:
            c_data["time_index"] = add_index
        # df = pd.DataFrame.from_dict(c_data, orient='index').transpose()

        return c_data

def test_apply_control(path_ecarrier,path_component_def):
    ec_dict = ECarrier.from_yaml(path_ecarrier)
    component_def = ESCParameter.from_yaml(path_component_def,ecarrier=ec_dict)
    timestep_s = 10
    component = EnergyStorageComponent(component_def["battery"],ts=timestep_s)


    # Stationary tests with identical control values:
    # control_values = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]
    ts = 0
    ts_ix = 0
    res_c = []
    component.reset_state()
    run_res_c=[]

    control_values = [random.uniform(0,10) for _ in tqdm(range(1000000))]

    for cv in tqdm(control_values):  # 1 year
        component.apply_control(cv)
        c_state = component.export_state(add_timestep=ts)
        run_res_c.append(c_state)
        ts += timestep_s
        ts_ix += 1
    #run_res_c = [dict(item, **{'run name': cv}) for item in run_res_c]
    res_c.extend(run_res_c)

    res_c = pd.DataFrame(res_c)

    return res_c

if __name__ == "__main__":
    """
    See /test for demonstration and examples
    """
    # path_ecarrier = Path.cwd() / Path("energycarrier/energycarrier.yaml")
    # ec_dict = ECarrier.from_yaml(path_ecarrier)
    # path_component_defs = Path.cwd() / Path("components_storage")
    # component_defs = ESCParameter.from_dir(path_component_defs, ecarrier=ec_dict)
    # components = [EnergyStorageComponent(par,ts=1) for k,par in component_defs.items()]
    # states = [c.export_state() for c in components]

    path_ecarrier = Path.cwd() / Path("energycarrier/energycarrier.yaml")
    path_component_def = Path.cwd() / Path("components_storage/battery.yaml")
    res = test_apply_control(path_ecarrier,path_component_def)

    # with Profile() as profile:
    #     test_apply_control(path_ecarrier,path_component_def)
    #     (            Stats(profile)
    #         .strip_dirs()
    #         .sort_stats(SortKey.CALLS)
    #         .print_stats()
    #     )