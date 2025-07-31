"""
Unified 0D energy storage component class
"""
import logging
from dataclasses import dataclass
import copy
from pathlib import Path

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
        :param ts: timestep [min]
        """

        self.par = par
        self.ts = ts
        self.state_initial = copy.deepcopy(state)
        self.state = state
        self.logger = logging.getLogger(__name__)

    def step_action(self,
                    E_req: float):
        """
        Update of storage component

        :param E_req: Energy requirement [kWh], <0 for discharge, >0 for charge
        :return:
        """
        # Calculation of updated SoC
        # -----------------------------
        E_SoC_0 = self.state.SoC * self.par.E_cap  # [kWh]

        if E_req <= 0:  # -> bat. discharge
            E_SoC_1 = E_SoC_0 + E_req
            E_out = - E_req
            P_out = - E_req / (self.ts / 60)
            E_in = 0
            P_in = 0
            E_loss = 0
            P_loss = 0
        else:  # ... charge with efficiency
            E_SoC_1 = E_SoC_0 + self.par.eta * E_req
            E_loss = (1 - self.par.eta) * E_req
            E_out = 0
            P_out = 0
            E_in = E_req
            P_in = E_req / (self.ts / 60)
            P_loss = E_loss / (self.ts / 60)

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

    def reset(self,
              reset_capacity: bool = True):
        """
        Reset to initial state
        (e.g. for ML/RL-Algorithms)
        :return:
        """
        self.state = copy.deepcopy(self.state_initial)
        if reset_capacity:
            self.par.E_cap = 0.001


if __name__ == "__main__":
    """
    See /test for demonstration and examples
    """
    path_ecarrier = Path.cwd() / Path("energycarrier/energycarrier.yaml")
    ec_dict = ECarrier.from_yaml(path_ecarrier)
    path_component_defs = Path.cwd() / Path("components_storage")
    component_defs = ESCParameter.from_dir(path_component_defs, ecarrier=ec_dict)
    components = [EnergyStorageComponent(par,ts=1) for k,par in component_defs.items()]