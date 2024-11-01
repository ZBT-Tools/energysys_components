"""
Main conversion class
"""
from dataclasses import dataclass, field
from scipy import interpolate
from energysys_components.various.normalization import denorm
from energysys_components.energy_carrier import ECarrier
import copy


@dataclass(frozen=False)
class EConversionParams:
    """
    Definition of energy conversion component
    """
    name: str

    # Definition of energy carriers
    E_in_mc_type: ECarrier
    E_in_sd1_type: ECarrier
    E_in_sd2_type: ECarrier
    E_out_type: ECarrier

    # Startup
    t_preparation: float  # Time until system is available [Minutes] ("idle")
    E_preparation: float  # Preparation Energy [kWh] (from cold to idle)

    # Load Operation
    P_out_min_pct: float  # Minimum operating load [% Load]
    P_out_rated: float  # Rated Load [kW]

    p_change_pos: float  # [% output load/min]
    p_change_neg: float  # [% output load/min]

    E_loadchange: list  # load change dependend additional required energy
    # (example: due to SOFC stack temperature increase)  [[load [%]],[Energy [kWh]]]

    # Overall component efficiency
    eta_pct: list  # load dependend efficiency  [[load [%]],[efficiency [%]]]
    # Main conversion path efficiency
    eta_mc_pct: list  # load dependend efficiency  [[load [%]],[efficiency [%]]]

    # Shutdown
    t_cooldown: float  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd: list  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio

    # Factor useable heat in loss
    fact_P_heat_P_Loss: float  # [0,1] Factor of useable heat energy in loss

    # Techno-economic
    spec_invest_cost: float  # [€/kW]
    spec_volume: float  # [m^^3/kW]
    spec_mass: float  # [kg/kW]

    # Control Settins
    control_type_target: bool  # If true, input is target, not difference action

    eta_preparation: float = 60  # For calculation of losses below operation
    norm_limits: list = field(default_factory=lambda: [0, 1])

    def __post_init__(self):
        """
        Calculation of helper functions, interpolators, ...

        Returns
        -------

        """

        # Startup calculations
        # ---------------------------------------------------------
        # Based on par.preparation_time & par.min_load_perc calculate
        # heatup/startup increase per time [%/min]
        # Example:  min_load_perc= 5%, preparation_time= 30min
        #           --> preparation_incr =  2.5% / min
        self.p_change_st_pct = self.P_out_min_pct / self.t_preparation

        self.E_preparation_heat = self.E_preparation * self.eta_preparation / 100
        self.E_preparation_loss = self.E_preparation - self.E_preparation_heat

        # Shutdown calculations
        # ---------------------------------------------------------
        # Based on par.cooldown_time & par.min_load_perc calculate
        # cool down decrease per time [%/min]
        # Example:  min_load_perc = 5%, cooldown_time= 30min
        #           --> cooldown_decr =  2.5% / min
        self.p_change_sd_pct = self.P_out_min_pct / self.t_cooldown

        # Efficiency calculations - overall component
        # ---------------------------------------------------------

        # Interpolator eta(output load [%]) [%]
        self.eta_pct_ip = interpolate.interp1d(self.eta_pct[0],
                                               self.eta_pct[1],
                                               kind='linear',
                                               bounds_error=False,
                                               fill_value=(self.eta_pct[1][0],
                                                           self.eta_pct[1][-1]))

        # Interpolator eta(output load [kW]) [%]
        self.eta_kW_ip = interpolate.interp1d(
            [e / 100 * self.P_out_rated for e in self.eta_pct[0]],
            self.eta_pct[1],
            kind='linear',
            bounds_error=False,
            fill_value=(self.eta_pct[1][0],
                        self.eta_pct[1][-1]))

        # Interpolator eta(input load [kW]) [%]
        list_P_out_kW = [ol_perc / 100 * self.P_out_rated for ol_perc in self.eta_pct[0]]
        list_P_in_kW = [ol_perc / 100 * self.P_out_rated /
                        (self.eta_pct_ip(ol_perc) / 100) for ol_perc in self.eta_pct[0]]
        list_eta_in_kW = [ol / il * 100 if il != 0 else 0 for ol, il in
                          zip(list_P_out_kW, list_P_in_kW)]

        self.eta_in_kW_ip = interpolate.interp1d(
            list_P_in_kW,
            list_eta_in_kW,
            kind='linear',
            bounds_error=False,
            fill_value=(list_eta_in_kW[0],
                        list_eta_in_kW[-1]))

        # Efficiency calculations - main conversion path
        # ---------------------------------------------------------

        # Interpolator eta(output load [%]) [%]
        self.eta_mc_pct_ip = interpolate.interp1d(self.eta_mc_pct[0],
                                                  self.eta_mc_pct[1],
                                                  kind='linear',
                                                  bounds_error=False,
                                                  fill_value=(self.eta_mc_pct[1][0],
                                                              self.eta_mc_pct[1][-1]))

        # Interpolator eta(output load [kW]) [%]
        self.eta_mc_kW_ip = interpolate.interp1d(
            [e / 100 * self.P_out_rated for e in self.eta_mc_pct[0]],
            self.eta_mc_pct[1],
            kind='linear',
            bounds_error=False,
            fill_value=(self.eta_mc_pct[1][0],
                        self.eta_mc_pct[1][-1]))

        # Interpolator eta(input load [kW]) [%]
        list_P_out_kW = [ol_perc / 100 * self.P_out_rated for ol_perc in self.eta_mc_pct[0]]
        list_P_in_kW = [ol_perc / 100 * self.P_out_rated /
                        (self.eta_mc_pct_ip(ol_perc) / 100) for ol_perc in self.eta_mc_pct[0]]
        list_eta_in_kW = [ol / il * 100 if il != 0 else 0 for ol, il in
                          zip(list_P_out_kW, list_P_in_kW)]

        self.eta_mc_in_kW_ip = interpolate.interp1d(
            list_P_in_kW,
            list_eta_in_kW,
            kind='linear',
            bounds_error=False,
            fill_value=(list_eta_in_kW[0],
                        list_eta_in_kW[-1]))

        # Load change energy interpolator Energy_state=f(Load [%])
        # ---------------------------------------------------------
        self.E_loadchange_ip = interpolate.interp1d(self.E_loadchange[0],
                                                    self.E_loadchange[1],
                                                    kind='linear',
                                                    bounds_error=False,
                                                    fill_value=(self.E_loadchange[1][0],
                                                                self.E_loadchange[1][-1]))

        # Some characteristic loads for convenience:
        # https://stackoverflow.com/questions/2474015/
        # "Getting the index of the returned max or min item using max()/min() on a list"
        self.P_out_etamax_pct = self.eta_pct[0][max(range(len(self.eta_pct[1])),
                                                    key=self.eta_pct[1].__getitem__)]

        self.P_out_min = self.P_out_min_pct / 100 * self.P_out_rated
        self.P_out_etamax = self.P_out_etamax_pct / 100 * self.P_out_rated

        self.P_in_min = self.P_out_min / (self.eta_pct_ip(self.P_out_min_pct) / 100)
        self.P_in_max = self.P_out_rated / (self.eta_pct_ip(100) / 100)
        self.P_in_etamax = self.P_out_etamax / (self.eta_pct_ip(self.P_out_etamax_pct) / 100)

        self.P_in_mc_min = self.P_out_min / (self.eta_mc_pct_ip(self.P_out_min_pct) / 100)
        self.P_in_mc_max = self.P_out_rated / (self.eta_mc_pct_ip(100) / 100)
        self.P_in_mc_etamax = self.P_out_etamax / (self.eta_mc_pct_ip(self.P_out_etamax_pct) / 100)

        self.split_P_sd1 = self.split_P_sd[0] / sum(self.split_P_sd)
        self.split_P_sd2 = self.split_P_sd[1] / sum(self.split_P_sd)


@dataclass(frozen=False)
class EConversionState:
    """
    State definition of energy conversion component
    """

    # Input
    P_in: float = 0  # [kW]
    E_in: float = 0  # [kWh]

    # Input portion main conversion
    P_in_mc: float = 0  # [kW]
    E_in_mc: float = 0  # [kWh]

    # Input portion sencondary 1
    P_in_sd1: float = 0  # [kW]
    E_in_sd1: float = 0  # [kWh]

    # Input portion sencondary 2
    P_in_sd2: float = 0  # [kW]
    E_in_sd2: float = 0  # [kWh]

    # Output
    P_out: float = 0  # [kW]
    E_out: float = 0  # [kWh]

    # Loss
    P_loss: float = 0  # [kW]
    E_loss: float = 0  # [kWh]

    P_heat: float = 0  # [kW]
    E_heat: float = 0  # [kWh]

    heatup_pct: float = 0  # [%]
    eta_pct: float = 0  # [%]
    eta_mc_pct: float = 0  # [%]
    opex_Eur: float = 0  # [€]

    # Convergence
    E_balance: float = 0  # [kWh]

    # Following are not really state variables, could be implemented here for optimization / ML
    # capex_Eur: float = 0  # [€]
    # volume: float = 0     # [m^^3]
    # weight: float = 0     # [kg]

    errorcode: int = 0  # not implemented yet


class EnergyConversion:
    """
    Energy Conversion class
    """

    def __init__(self, conv_par: EConversionParams,
                 ts: int,
                 conv_state: EConversionState = EConversionState(),
                 # debug: bool = False (tbi)
                 ):
        """
        :param conv_par:    EConversionParams dataclass object
        :param conv_state:  EConversionState dataclass object
        :param ts:           timestep [min]
        # :param debug:       bool flag, not implemented yet
        """

        self.par = conv_par
        self.ts = ts
        cop = copy.deepcopy(conv_state)
        self.state_initial = cop  # Copy of initial state for reset()-method
        self.state = conv_state

    def step_action(self, action: float, hypothetical_step=False):
        """
        Define output target

        Two different ways of control:

            if conv_par.control_type_target = True
                0: Target Load 0%
                1: Target Load 100%

            if conv_par.control_type_target = False (no up-to-date implementation!)
                -1: Maximum (possible) deloading,
                1: Maximum (possible) loading

        :param action: float, to be performed action for component.
            Input range depends on defined system control type.
            [-1,1] for conv_par.control_type_target = False
            [0,1] for conv_par.control_type_target = True

        :param hypothetical_step: bool, If true, perform method, but without actually returning
         updated state

         Structure:

         1.) State calculations prior to action
         2.) Control action
         3.) Efficiency calculation
         4.) Calculation of state variables (P,W,...)
         5.) Energy balance calculation
         6.) Update state variables

        """
        # error = 0  # Init error code

        # 1.) State calculations prior to action
        # ---------------------------------------
        # Info: Below minimum load corner point, real component output load is zero.
        #               However for calculation of changes in heatup or cooldown states it is
        #               used as an artificial variable (for simplicity) and is therefore calculated
        #               below based on the below-load-operation state variable heatup_pct.
        #               It is used only internally.
        #

        if self.state.heatup_pct < 100:
            P_out_0_pct = round(self.state.heatup_pct / 100 * self.par.P_out_min_pct, 6)
        else:
            P_out_0_pct = round(self.state.P_out / self.par.P_out_rated, 6) * 100

        # 2.) Application of control action
        # ---------------------------------------------------------
        if not self.par.control_type_target:
            raise Exception('No up-to-date implementation of this control type.')

        else:  # --> Control type: target

            # Limit input to valid action range
            # Idea: Warning could be implement
            if action > 1:
                action = 1
            elif action < 0:
                action = 0

            # Denormalize action [0,1] to load [%]
            # Reason for implementation: Simple way to use different types of normalization for ML
            P_out_target_pct = denorm(action, {'n': [self.par.norm_limits[0],
                                                     self.par.norm_limits[1]],
                                               'r': [0, 100]})

        # Calculation of new heatup and load state [%]
        (P_out_1_pct,
         heatup_1_pct, load_operation_time) = self._calc_P_change(P_out_target_pct=P_out_target_pct)

        # 3.) Efficiency calculation
        # ---------------------------------------------------------
        if heatup_1_pct < 100:
            eta_1_pct = self.par.eta_preparation
            eta_mc_1_pct = 0
        else:
            eta_1_pct = self.par.eta_pct_ip(P_out_1_pct).item(0)
            eta_mc_1_pct = self.par.eta_mc_pct_ip(P_out_1_pct).item(0)

        # 4.) Energy Calculation
        # ---------------------------------------------------------
        # Calculation of updated state
        new_state_dict = self._calc_E_change(P_out_1_pct, P_out_0_pct, heatup_1_pct,
                                             load_operation_time,
                                             eta_1_pct, eta_mc_1_pct)

        # 5.) Energy balance calculation
        # ---------------------------------------------------------
        # Info: Only calculation of balance, here no abort criteria
        E_bulk1 = (heatup_1_pct - self.state.heatup_pct) / 100 * self.par.E_preparation_heat
        E_bulk2 = (self.par.E_loadchange_ip(P_out_1_pct) - self.par.E_loadchange_ip(P_out_0_pct))
        new_state_dict["E_balance"] = (new_state_dict["E_in_mc"] +
                                       new_state_dict["E_in_sd1"] +
                                       new_state_dict["E_in_sd2"] -
                                       new_state_dict["E_out"] -
                                       new_state_dict["E_loss"] -
                                       E_bulk1 -
                                       E_bulk2
                                       )

        # 6.) Finally update state variables
        # ---------------------------------------------------------
        if not hypothetical_step:
            self.state.E_in = new_state_dict["E_in"]
            self.state.E_in_mc = new_state_dict["E_in_mc"]
            self.state.E_in_sd1 = new_state_dict["E_in_sd1"]
            self.state.E_in_sd2 = new_state_dict["E_in_sd2"]
            self.state.E_out = new_state_dict["E_out"]
            self.state.E_loss = new_state_dict["E_loss"]
            self.state.E_heat = new_state_dict["E_heat"]

            self.state.P_in = new_state_dict["P_in"]
            self.state.P_in_mc = new_state_dict["P_in_mc"]
            self.state.P_in_sd1 = new_state_dict["P_in_sd1"]
            self.state.P_in_sd2 = new_state_dict["P_in_sd2"]
            self.state.P_out = new_state_dict["P_out"]
            self.state.P_loss = new_state_dict["P_loss"]
            self.state.P_heat = new_state_dict["P_heat"]

            self.state.heatup_pct = heatup_1_pct
            self.state.eta_pct = eta_1_pct
            self.state.eta_mc_pct = eta_mc_1_pct

            self.state.E_balance = new_state_dict["E_balance"]

            # self.state.opex_Eur = new_state_dict["opex_Eur"]
            # self.state.errorcode = new_state_dict["errorcode"]

            pass

        else:
            hypoth_state = EConversionState(
                E_in_mc=new_state_dict["E_in_mc"],
                P_out=new_state_dict["P_out"],
                eta_pct=eta_1_pct,
                P_in_mc=new_state_dict["P_in_mc"],
                heatup_pct=heatup_1_pct,
                eta_mc_pct=eta_mc_1_pct,
                P_in_sd1=new_state_dict["P_in_sd1"],
                P_in_sd2=new_state_dict["P_in_sd2"],
                E_in_sd1=new_state_dict["E_in_sd1"],
                E_in_sd2=new_state_dict["E_in_sd2"],
                P_in=new_state_dict["P_in"],
                E_out=new_state_dict["E_out"],
                E_in=new_state_dict["E_in"],
                P_heat=new_state_dict["P_heat"],
                P_loss=new_state_dict["P_loss"],
                E_balance=new_state_dict["E_balance"],
                E_heat=new_state_dict["E_balance"],
                E_loss=new_state_dict["E_loss"])


            return hypoth_state

    def _calc_P_change(self, P_out_target_pct):
        """
        Calculate new load P

        Different load ranges [%]...
          - [0,self.par.P_out_min_pct):   Startup/Shutdown area   [S]
          - [self.par.P_out_min_pct,100]: Operation range         [O]

        results in 3 cases for load increase: [S->S, S->O, O->O],
        and 3 cases for load decrease:        [O->O, O->S, S->S].

        :param P_out_target_pct: Target load [%]

        :return: P_out_pct  new P_out [%]
        :return: heatup_pct new heatup state [%]
        :return: load_operation_time time in operation [min]
        """
        # Initialization
        # ---------------------------------------
        # Additional state calculations prior to action
        # Info: Below minimum load corner point, real component output load is zero.
        #               However for calculation of changes in heatup or cooldown states it is
        #               used as an artificial variable (for simplicity) and is therefore calculated
        #               below based on the below-load-operation state variable heatup_pct.
        #               It is used only internally.

        if self.state.heatup_pct < 100:
            P_out_pct = round(self.state.heatup_pct / 100 * self.par.P_out_min_pct, 6)
        else:
            P_out_pct = round(self.state.P_out / self.par.P_out_rated, 6) * 100

        load_operation_time = 0  # min
        heatup_pct = self.state.heatup_pct

        # Positive load changes & load holding
        # ---------------------------------------
        if P_out_pct <= P_out_target_pct:

            # [S->S]
            if P_out_target_pct < self.par.P_out_min_pct:
                P_out_pct = min(P_out_target_pct,
                                P_out_pct + self.par.p_change_st_pct * self.ts)
                heatup_pct = P_out_pct / self.par.P_out_min_pct * 100

            # [S->O (potentially)]
            elif (P_out_target_pct >= self.par.P_out_min_pct) and \
                    (P_out_pct < self.par.P_out_min_pct):

                prep_delta_perc = (self.par.P_out_min_pct - P_out_pct)  # %pts to min. load
                prep_time_min = prep_delta_perc / self.par.p_change_st_pct  # time to min. load
                if prep_time_min <= self.ts:  # --> "O" reached
                    P_out_pct = min(P_out_target_pct,
                                    self.par.P_out_min_pct + self.par.p_change_pos * (
                                            self.ts - prep_time_min))
                    load_operation_time = self.ts - prep_time_min
                    heatup_pct = 100
                else:  # --> "O" not reached
                    P_out_pct = P_out_pct + self.par.p_change_st_pct * self.ts
                    heatup_pct = P_out_pct / self.par.P_out_min_pct * 100

            # [O->O]
            elif (P_out_target_pct >= self.par.P_out_min_pct) and \
                    (P_out_pct >= self.par.P_out_min_pct):

                P_out_pct = min(P_out_target_pct,
                                P_out_pct + self.par.p_change_pos * self.ts)
                load_operation_time = self.ts

        # Negative load changes
        # ---------------------------------------
        elif P_out_pct > P_out_target_pct:
            # [O->O]
            if P_out_target_pct >= self.par.P_out_min_pct:
                P_out_pct = max(P_out_target_pct,
                                P_out_pct - self.par.p_change_neg * self.ts)
                load_operation_time = self.ts

            # [O->S(potentially)]
            elif (P_out_target_pct < self.par.P_out_min_pct) and \
                    (P_out_pct >= self.par.P_out_min_pct):

                load_delta_perc = (P_out_pct - self.par.P_out_min_pct)  # %pts to min load
                unload_time_min = load_delta_perc / self.par.p_change_neg  # time to min load
                if unload_time_min < self.ts:  # --> shutdown mode reached
                    P_out_pct = max(P_out_target_pct,
                                    self.par.P_out_min_pct - self.par.p_change_sd_pct * (
                                            self.ts - unload_time_min))
                    heatup_pct = P_out_pct / self.par.P_out_min_pct * 100
                    load_operation_time = unload_time_min
                else:  # --> shutdown mode not reached
                    P_out_pct = P_out_pct - self.par.p_change_neg * self.ts
                    load_operation_time = self.ts
            # [S->S]
            elif (P_out_target_pct < self.par.P_out_min_pct) and \
                    (P_out_pct < self.par.P_out_min_pct):

                P_out_pct = max(P_out_target_pct,
                                P_out_pct - self.par.p_change_sd_pct * self.ts)
                heatup_pct = P_out_pct / self.par.P_out_min_pct * 100

        return P_out_pct, heatup_pct, load_operation_time

    def _calc_E_change(self, P_out_pct, P_out_0_pct, heatup_1_pct, load_operation_time,
                       eta_1_pct, eta_mc_1_pct) -> dict:
        """
        Energy calculation from prior state P_out_0_pct to new state P_out_pct
        Case distinction required:
         - load operation -> load operation [L->L]
         - noLoad operation -> noLoad operation [NL->NL]
         - load operation -> noLoad operation [L->NL]
         - noLoad operation -> load operation [NL->L]

        :return: new_state: dict
        """
        # Init return dict
        new_state = dict.fromkeys(['E_in', 'E_in_mc', 'E_loss', "E_in_sd1", "E_in_sd2", "E_out",
                                   "E_heat",
                                   'P_in', 'P_in_mc', 'P_loss', "P_in_sd1", "P_in_sd2", "P_out",
                                   "P_heat"])

        # [NL->NL], P_out_pct >= P_out_0_pct
        # (if required) Energy amount for 'holding prior idle state (loss compensation)'
        if (heatup_1_pct < 100) and (P_out_pct >= P_out_0_pct):
            if P_out_pct == P_out_0_pct + self.par.p_change_st_pct * self.ts:
                # -> Maximum start speed
                # Loss during pure startup is expected to be included in given E_preparation
                # and therefore no additional compensation is required #IDEA
                E_compens = 0
                E_compens_loss = 0

            elif P_out_pct - self.par.p_change_sd_pct * self.ts < 0:
                # In low heatup state, compesation is neglected, which is
                # sufficient for rule based control (as this is no reasonable target state),
                # however needs to be refined for advanced control #IDEA
                E_compens = 0
                E_compens_loss = 0

            elif P_out_pct == P_out_0_pct:
                # calculate compensation energy and loss of it (just for holding the state)
                E_compens = (self.par.p_change_sd_pct * self.ts / self.par.P_out_min_pct) \
                            * self.par.E_preparation
                E_compens_loss = E_compens

            else:
                # For all other startup targets, compesation is neglected, which is
                # sufficient for rule based control (as this is no reasonable target state),
                # however needs to be refined for advanced control #IDEA
                E_compens = 0
                E_compens_loss = 0

            # Energy amount for 'changing heatup state'
            E_startup = (heatup_1_pct - self.state.heatup_pct) / 100 * self.par.E_preparation
            E_startup_loss = (
                    (heatup_1_pct - self.state.heatup_pct) / 100 * self.par.E_preparation_loss)

            E_startup_combined = E_compens + E_startup

            # State variables
            new_state["E_in_mc"] = 0
            new_state["E_loss"] = E_compens_loss + E_startup_loss
            new_state["P_in_mc"] = 0
            new_state["P_loss"] = new_state["E_loss"] / (self.ts / 60)

            new_state["E_in_sd1"] = self.par.split_P_sd1 * E_startup_combined
            new_state["E_in_sd2"] = self.par.split_P_sd2 * E_startup_combined

            new_state["P_in_sd1"] = new_state["E_in_sd1"] / (self.ts / 60)
            new_state["P_in_sd2"] = new_state["E_in_sd2"] / (self.ts / 60)

            # No output energy & load for heatup_pct < 100
            new_state["E_out"] = 0
            new_state["P_out"] = 0

        # [xx->NL] P_out_pct < P_out_0_pct
        elif (heatup_1_pct < 100) and (P_out_pct < P_out_0_pct):

            # If required calculate operating portion (.._op) of input energy
            if self.state.heatup_pct == 100:
                E_in_op = (self.state.P_in + self.par.P_in_min) / 2 * (load_operation_time / 60)

                # Main conversion
                E_in_mc_op = ((self.state.P_in_mc + self.par.P_in_mc_min) /
                              2 * (load_operation_time / 60))

                # Load Change
                E_loadchange_op = (self.par.E_loadchange_ip(P_out_pct) -
                                   self.par.E_loadchange_ip(P_out_0_pct))

                # Secondary Energy
                E_in_sd_op = E_in_op - E_in_mc_op + E_loadchange_op
                E_in_sd1_op = self.par.split_P_sd1 * E_in_sd_op
                E_in_sd2_op = self.par.split_P_sd2 * E_in_sd_op

                E_out = (self.state.P_out + self.par.P_out_min) / 2 * (
                        load_operation_time / 60)
                E_loss_op = E_in_op - E_out
            else:
                E_in_mc_op = 0
                E_in_sd1_op = 0
                E_in_sd2_op = 0
                E_loss_op = 0
                E_out = 0

            # Coast down portion
            coastdown_time = self.ts - load_operation_time
            P_out_cooldownst_pct = min(P_out_0_pct, self.par.P_out_min_pct)  # PStart of coast down
            # (Hypothetically) max. cooldown during give time:
            diff_cooldown_max_pct = min(self.par.p_change_sd_pct * coastdown_time,
                                        P_out_cooldownst_pct)

            # If required calculate energy amount for coast down ( for superposed energy input)
            if P_out_pct > P_out_cooldownst_pct - diff_cooldown_max_pct:
                diff_load_perc = P_out_pct - (P_out_cooldownst_pct - diff_cooldown_max_pct)
                E_diff = diff_load_perc / self.par.P_out_min_pct * self.par.E_preparation
                E_in_sd1_cd = self.par.split_P_sd1 * E_diff
                E_in_sd2_cd = self.par.split_P_sd2 * E_diff

            else:
                diff_load_perc = 0
                E_in_sd1_cd = 0
                E_in_sd2_cd = 0

            E_loss_cd = (diff_cooldown_max_pct /
                         self.par.P_out_min_pct) * self.par.E_preparation_heat + \
                        (diff_load_perc / self.par.P_out_min_pct) * self.par.E_preparation_loss

            # state variables
            new_state["E_in_mc"] = E_in_mc_op
            new_state["E_loss"] = E_loss_op + E_loss_cd
            new_state["P_in_mc"] = 0
            new_state["P_loss"] = E_loss_cd / (coastdown_time / 60)

            new_state["E_in_sd1"] = E_in_sd1_op + E_in_sd1_cd
            new_state["E_in_sd2"] = E_in_sd2_op + E_in_sd2_cd

            new_state["E_out"] = E_out
            new_state["P_out"] = 0

            # Power at end of time step is mean energy of coast down, not inluding prior load
            # operation
            new_state["P_in_sd1"] = E_in_sd1_cd / (coastdown_time / 60)
            new_state["P_in_sd2"] = E_in_sd2_cd / (coastdown_time / 60)

        else:  # [xx->L] Load Operation
            # Energy calculations
            P_out = self.par.P_out_rated * (P_out_pct / 100)

            E_out = (max(self.state.P_out, self.par.P_out_min) + P_out) / 2 * (
                    load_operation_time / 60)

            P_in = P_out / (eta_1_pct / 100)
            P_in_mc = P_out / (eta_mc_1_pct / 100)

            # If required calculate starting portion of input energy
            if self.state.heatup_pct < 100:
                # Startup phase
                E_in_hp = ((heatup_1_pct - self.state.heatup_pct) / 100 * self.par.E_preparation)
                E_loss_hp = E_in_hp * ((100 - self.par.eta_preparation) / 100)
                E_in_sd1_hp = self.par.split_P_sd1 * E_in_hp
                E_in_sd2_hp = self.par.split_P_sd2 * E_in_hp

            else:
                E_loss_hp = 0
                E_in_sd1_hp = 0
                E_in_sd2_hp = 0

            # Operating Phase
            E_in_op = (max(self.state.P_in, self.par.P_in_min) + P_in) / 2 * (
                    load_operation_time / 60)
            E_in_mc_op = ((max(self.state.P_in_mc, self.par.P_in_mc_min) + P_in_mc) /
                          2 * (load_operation_time / 60))
            # Load Change
            E_loadchange_op = (self.par.E_loadchange_ip(P_out_pct) -
                               self.par.E_loadchange_ip(P_out_0_pct))

            E_in_sd_op = E_in_op - E_in_mc_op + E_loadchange_op
            E_in_sd1_op = self.par.split_P_sd1 * E_in_sd_op
            E_in_sd2_op = self.par.split_P_sd2 * E_in_sd_op
            E_loss_op = E_in_op - E_out

            # New state variables
            new_state["E_in_mc"] = E_in_mc_op
            new_state["E_in_sd1"] = E_in_sd1_op + E_in_sd1_hp
            new_state["E_in_sd2"] = E_in_sd2_op + E_in_sd2_hp
            new_state["E_out"] = E_out
            new_state["E_loss"] = E_loss_op + E_loss_hp

            new_state["P_in_mc"] = P_in_mc
            new_state["P_in_sd1"] = (P_in - P_in_mc) * self.par.split_P_sd1
            new_state["P_in_sd2"] = (P_in - P_in_mc) * self.par.split_P_sd2
            new_state["P_loss"] = P_in - P_out
            new_state["P_out"] = P_out

        # Summation of total input energy and load
        new_state["E_in"] = new_state["E_in_mc"] + new_state["E_in_sd1"] + new_state["E_in_sd2"]
        new_state["P_in"] = new_state["P_in_mc"] + new_state["P_in_sd1"] + new_state["P_in_sd2"]

        new_state["E_heat"] = self.par.fact_P_heat_P_Loss * new_state["E_loss"]
        new_state["P_heat"] = self.par.fact_P_heat_P_Loss * new_state["P_loss"]

        return new_state

    def step_action_stationary(self, action: float) -> None:
        """
        Performs step_action() until target "action" is reached.
        Condition for stationarity:
        E_in @ t-1 == E_in @ t
        P_out @ t-1 == P_out @ t

        Parameters
        ----------
        action

        Returns
        -------

        """
        ct_iteration = 0
        P_out_pct_target = action * 100
        P_out_pct = self.state.P_out / self.par.P_out_rated * 100

        cond = False
        while not ((P_out_pct_target == P_out_pct) and cond) and (ct_iteration <= 100):
            E_in_0 = self.state.E_in
            self.step_action(action)
            P_out_pct = self.state.P_out / self.par.P_out_rated * 100
            E_in_1 = self.state.E_in
            if E_in_0 == E_in_1:
                cond = True
            ct_iteration += 1

        # Final Step
        self.step_action(action)

        if ct_iteration == 100:
            raise Exception("Stationary step did not converge.")
        pass

    def action_for_P_in_mc_target(self, input_load: float) -> float:
        """
        Calculation of action (= load target [0,1]) for step_action()-Method equivalent to
        given main conversion(!) input load requirement [kW]

        Only usable for load operation!
        Returns error if input_load < minimum input load.

        Solves:

            Find P_out for given P_in in:
            P_in * eta(P_out)/ 100 = P_out

        :param input_load: float, Input load [kW]

        """

        # def func(x):
        #     return input_load / self.par.p_out * self.eta(x * 100) / 100 - x

        # Check if input_load is above required minimum
        if input_load < self.par.P_in_mc_min:
            raise Exception("Input load too low for action")
        elif input_load > self.par.P_in_mc_max:
            raise Exception("Input load too high for action")
        else:
            # root = fsolve(func, [0], full_output=True)
            # val = root[0][0]
            # conv = root[2]
            P_out = input_load * self.par.eta_mc_in_kW_ip(input_load) / 100

            return P_out / self.par.P_out_rated

    def action_for_E_in_mc_target(self, input_load: float) -> float:
        """
        Calculation of action (= load target [0,1]) for step_action()-Method equivalent to
        given main conversion(!) input energy requirement [kWh]

        To be implemented
        """

        # def func(x):
        #
        #     return input_load / self.par.p_out * self.eta(x * 100) / 100 - x
        #
        # # Check if input_load is above required minimum
        # if input_load < self.par.P_in_mc_min:
        #     raise Exception("Input load too low for action")
        # elif input_load > self.par.P_in_mc_max:
        #     raise Exception("Input load too high for action")
        # else:
        #     # root = fsolve(func, [0], full_output=True)
        #     # val = root[0][0]
        #     # conv = root[2]
        #     P_out = input_load * self.par.eta_mc_in_kW_ip(input_load) / 100
        #
        #     return P_out / self.par.P_out_rated

    def P_in_mc_from_P_out(self, output_load: float) -> float:
        """
        Simple function that applies output load in kW and get equivalent main conversion
         input load [kW].
        Only usable for load operation
        Returns error if below minimum output load

        :param output_load:  Output load [kW]

        """

        # Check if input_load is above required minimum
        if output_load < self.par.P_out_min:
            raise Exception("Output load too low for action")
        elif output_load > self.par.P_out_rated:
            raise Exception("Output load too high for action")
        else:
            output_load_perc = output_load / self.par.P_out_rated * 100
            input_mc_load = output_load / (self.par.eta_mc_pct_ip(output_load_perc) / 100)
            return input_mc_load

    def reset(self):
        """
        Reset to initial state
        (e.g. for ML/RL-Algorithms)

        :return:
        """
        self.state = copy.deepcopy(self.state_initial)


if __name__ == "__main__":
    """
    See /test for demonstration and testfunctions
    """
    ...
