"""
Energy Storage, Battery System
"""
from dataclasses import dataclass
import copy


@dataclass(frozen=True)
class StorageParams:
    """
    Definition of energy storage component
    """
    efficiency_perc: float  # Const. or output dependend efficiency [% Efficiency],
    # or  [[load [%]],[efficiency [%]]]
    C_rate_charge: float  # This is the charge per hour rate –
    # one divided by the number of hours to charge the battery fully.
    spec_invest_cost: float  # [€/kWh]
    spec_volume: float  # [m^^3/kWh]
    spec_mass: float  # [kg/kWh]


@dataclass(frozen=False)
class StorageState:
    """
    To be implemented
    """

    errorcode: int = 0  # for passing different errors


class EnergyStorage:
    """
    Energy storage class
    """

    def __init__(self,
                 stor_par: StorageParams,
                 stor_state: StorageState,
                 ts=15):
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

    def step_action(self, action: float, hypothetical_step=False):
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
