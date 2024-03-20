"""
Energy Storage, Battery System
"""
from dataclasses import dataclass
import copy

from energysys_components.energy_carrier import ECarrier


@dataclass(frozen=False)
class StorageParams:
    """
    Definition of energy storage component
    """
    name: str

    # Definition of energy carriers
    E_in_mc_type: ECarrier
    E_in_sd1_type: ECarrier
    E_in_sd2_type: ECarrier
    E_out_type: ECarrier

    eta: float  # Const. or output dependend efficiency [0-1]
    C_rate_charge: float  # This is the charge per hour rate –
    # one divided by the number of hours to charge the battery fully.

    spec_invest_cost: float  # [€/kWh]
    spec_volume: float  # [m^^3/kWh]
    spec_mass: float  # [kg/kWh]
    E_cap: float = 0  # Capacity of storage component [kWh]
    autoIncrease: bool = True  # Allows component to increase capacity on the fly during calculation


@dataclass(frozen=False)
class StorageState:
    """
    To be implemented
    """
    SoC: float = 1  # State of charge 0-1, 0: empty, 1: full
    E_cap_incr: float = 0  # Required capacity increase during run

    errorcode: int = 0  # for passing different errors


class EnergyStorage:
    """
    Energy storage class
    """

    def __init__(self,
                 stor_par: StorageParams,
                 stor_state: StorageState,
                 ts):
        """
        :param stor_par: StorageParams object
        :param stor_state: StorageState object
        :param ts: timestep [min]
        """

        self.par = stor_par
        self.ts = ts
        cop = copy.deepcopy(stor_state)
        self.state_initial = cop
        self.state = stor_state

    def step_action(self, E_req: float):
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
        else:  # ... charge with efficiency
            E_SoC_1 = E_SoC_0 + self.par.eta * E_req

        # If required, update capacity 'on the fly' ....
        if E_SoC_1 < 0:  # ... if SoC < 0
            if self.par.autoIncrease:
                adder = -1 * E_SoC_1
                self.par.E_cap += adder
                self.state.E_cap_incr += adder
                E_SoC_1 = 0
            else:
                raise Exception("Battery overflow")

        elif E_SoC_1 > self.par.E_cap:  # ... if SoC > 1
            if self.par.autoIncrease:
                adder = E_SoC_1 - self.par.E_cap
                self.par.E_cap += adder
                self.state.E_cap_incr += adder
            else:
                raise Exception("Battery overflow")
        else:
            pass

        self.state.SoC = E_SoC_1 / self.par.E_cap

        pass

    def reset(self):
        """
        Reset to initial state
        (e.g. for ML/RL-Algorithms)
        :return:
        """
        self.state = copy.deepcopy(self.state_initial)


if __name__ == "__main__":
    ...
