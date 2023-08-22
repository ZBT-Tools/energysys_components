"""
Main conversion class
"""
from dataclasses import dataclass, field
from scipy import interpolate
from various.normalization import denorm
import copy


@dataclass(frozen=False)
class EConversionParams:
    """
    Definition of energy conversion component
    """

    # Startup
    t_preparation: float  # Time until system is available [Minutes] ("idle")
    W_preparation: float  # Preparation Energy [kWh] (from cold to idle)

    # Load Operation
    P_out_min_pct: float  # Minimum operating load [% Load]
    P_out_rated: int  # Rated Load [kW]
    eta_pct: list  # Const. or load dependend efficiency [% Efficiency],
    # or  [[load [%]],[efficiency [%]]]

    p_change_pos: float  # [% output load/min]
    p_change_neg: float  # [% output load/min]

    # Shutdown
    t_cooldown: float  # Time until system cooled down [Minutes] ("idle to cool")

    # Techno-economic
    spec_invest_cost: float  # [€/kW]
    spec_volume: float  # [m^^3/kW]
    spec_mass: float  # [kg/kW]

    # Control Settins
    control_type_target: bool  # If true, input is target, not difference action

    eta_preparation: float = 60
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

        self.W_preparation_heat = self.W_preparation * self.eta_preparation / 100
        self.W_preparation_loss = self.W_preparation - self.W_preparation_heat

        # Shutdown calculations
        # ---------------------------------------------------------
        # Based on par.cooldown_time & par.min_load_perc calculate
        # cool down decrease per time [%/min]
        # Example:  min_load_perc = 5%, cooldown_time= 30min
        #           --> cooldown_decr =  2.5% / min
        self.p_change_sd_pct = self.P_out_min_pct / self.t_cooldown

        # Efficiency calculations
        # ---------------------------------------------------------
        # Linear efficiency curve interpolator

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
                        (self.eta_kW_ip(ol_perc) / 100) for ol_perc in self.eta_pct[0]]
        list_eta_in_kW = [ol / il * 100 if il != 0 else 0 for ol, il in
                          zip(list_P_out_kW, list_P_in_kW)]

        self.eta_in_kW_ip = interpolate.interp1d(
            list_P_in_kW,
            list_eta_in_kW,
            kind='linear',
            bounds_error=False,
            fill_value=(list_eta_in_kW[0],
                        list_eta_in_kW[-1]))

        # Some characteristic loads for convenience:
        # https://stackoverflow.com/questions/2474015/
        # "Getting the index of the returned max or min item using max()/min() on a list"
        self.P_out_etamax_pct = self.eta_pct[0][max(range(len(self.eta_pct[1])),
                                                    key=self.eta_pct[1].__getitem__)]

        self.P_out_etamax = self.P_out_etamax_pct / 100 * self.P_out_rated
        self.P_in_maxeta = self.P_out_etamax / (self.eta_pct_ip(self.P_out_etamax_pct) / 100)

        self.P_out_min = self.P_out_min_pct / 100 * self.P_out_rated
        self.P_in_min = self.P_out_min / (self.eta_pct_ip(self.P_out_min_pct) / 100)
        self.P_in_max = self.P_out_rated / (self.eta_pct_ip(100) / 100)


@dataclass(frozen=False)
class EConversionState:
    """
    State definition of energy conversion component
    """

    # Input
    P_in: float = 0  # [kW]
    W_in_01: float = 0  # [kWh]

    # Output
    P_out: float = 0  # [kW]
    W_out_01: float = 0  # [kWh]

    # Loss
    P_loss: float = 0  # [kW]
    W_loss_01: float = 0  # [kWh]

    # Startup / Shutdown information
    heatup_pct: float = 0  # [%]
    eta_pct: float = 0  # [%]
    opex_Eur: float = 0  # [€]

    # Convergence
    W_balance_01: float = 0  # [kWh]

    # Following are not really state variables, beside it is dynamically increased optimization goal
    # capex_Eur: float = 0  # [€]
    # volume: float = 0  # [m^^3]
    # weight: float = 0  # [kg]

    errorcode: int = 0  # not implemented yet


class EnergyConversion:
    """
    Energy Conversion class
    """

    def __init__(self, conv_par: EConversionParams,
                 conv_state: EConversionState,
                 ts: int = 15,
                 debug: bool = False):
        """

        :param conv_par:    EConversionParams dataclass object
        :param conv_state:  EConversionState dataclass object
        :param ts:           timestep [min]
        :param debug:       bool flag, not implemented yet
        """

        # ToDO: Check if dataclass object conv_par can be freezed here

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
        """

        # # State calculations prior to action
        # # ---------------------------------------------------------
        # Explaination: Below minimum load corner point, real component output load is zero.
        #               However for calculation of changes in heatup or cooldown states it is
        #               used as an artificial variable (for simplicity) and is therefore calculated
        #               below based on the below-load-operation state variable heatup_pct.
        #               It is used only internally.
        #

        if self.state.heatup_pct < 100:
            P_out_0_pct = round(self.state.heatup_pct / 100 * self.par.P_out_min_pct, 5)
            P_out_pct = round(self.state.heatup_pct / 100 * self.par.P_out_min_pct, 5)
        else:
            P_out_0_pct = round(self.state.P_out / self.par.P_out_rated, 5) * 100
            P_out_pct = round(self.state.P_out / self.par.P_out_rated, 5) * 100

        heatup_pct = self.state.heatup_pct

        # # Control action
        # # ---------------------------------------------------------
        error = 0  # Init error code

        if not self.par.control_type_target:
            # ToDo: needs to be updated '23^
            load_operation_time = 0  # min
            pass

        else:  # --> Control type target

            # Limit input to valid action range
            # Idea: Warning could be implement
            if action > 1:
                action = 1
            elif action < 0:
                action = 0

            # Denormalize action [0,1] to load [%]
            # Background: Simple way to use different types of normalization for Machine Learning
            P_out_target_pct = denorm(action, {'n': [self.par.norm_limits[0],
                                                     self.par.norm_limits[1]],
                                               'r': [0, 100]})

            # Update step, case distinction
            # ---------------------------------------------------------
            # Different load ranges [%]...
            #   - [0,self.par.P_out_min_pct):   Startup/Shutdown area   [S]
            #   - [self.par.P_out_min_pct,100]: Operation range         [O]
            #
            # results in 3 cases for load increase: [S->S, S->O, O->O],
            # and 3 cases for load decrease:        [O->O, O->S, S->S].

            # For later energy calculations....
            load_operation_time = 0  # min

            if P_out_pct <= P_out_target_pct:  # --> load holding & increase cases

                if P_out_target_pct < self.par.P_out_min_pct:  # --> [S->S]
                    P_out_pct = min(P_out_target_pct,
                                    P_out_pct + self.par.p_change_st_pct * self.ts)
                    heatup_pct = P_out_pct / self.par.P_out_min_pct * 100

                elif (P_out_target_pct >= self.par.P_out_min_pct) and \
                        (P_out_pct < self.par.P_out_min_pct):  # --> [S->O]

                    prep_delta_perc = (self.par.P_out_min_pct - P_out_pct)  # %pts to min. load
                    prep_time_min = prep_delta_perc / self.par.p_change_st_pct  # time to min. load
                    if prep_time_min <= self.ts:  # --> operation mode reached
                        P_out_pct = min(P_out_target_pct,
                                        self.par.P_out_min_pct + self.par.p_change_pos * (
                                                self.ts - prep_time_min))
                        load_operation_time = self.ts - prep_time_min
                        heatup_pct = 100
                    else:  # --> operation mode not reached
                        P_out_pct = P_out_pct + self.par.p_change_st_pct * self.ts
                        heatup_pct = P_out_pct / self.par.P_out_min_pct * 100

                elif (P_out_target_pct >= self.par.P_out_min_pct) and \
                        (P_out_pct >= self.par.P_out_min_pct):  # --> [O->O]

                    P_out_pct = min(P_out_target_pct,
                                    P_out_pct + self.par.p_change_pos * self.ts)
                    load_operation_time = self.ts

            elif P_out_pct > P_out_target_pct:  # --> load decrease cases
                if P_out_target_pct >= self.par.P_out_min_pct:  # --> [O->O]
                    P_out_pct = max(P_out_target_pct,
                                    P_out_pct - self.par.p_change_neg * self.ts)
                    load_operation_time = self.ts

                elif (P_out_target_pct < self.par.P_out_min_pct) and \
                        (P_out_pct >= self.par.P_out_min_pct):  # --> [O->S]

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

                elif (P_out_target_pct < self.par.P_out_min_pct) and \
                        (P_out_pct < self.par.P_out_min_pct):  # --> [S->S]

                    P_out_pct = max(P_out_target_pct,
                                    P_out_pct - self.par.p_change_sd_pct * self.ts)
                    heatup_pct = P_out_pct / self.par.P_out_min_pct * 100

        # Efficiency calculation
        # ---------------------------------------------------------
        if heatup_pct < 100:
            eta_perc_1 = self.par.eta_preparation
        else:
            eta_perc_1 = self.par.eta_pct_ip(P_out_pct).item(0)

        # Update state vars - Calculation of required input and output power and energy
        # ---------------------------------------------------------

        if (heatup_pct < 100) and (P_out_pct >= P_out_0_pct):  # -> Startup or holding idle
            # Energy amount for 'holding prior idle state (loss compensation)', if required
            # ToDo: condition below is sufficient for rule based control,
            #       needs to be refined for RL-Approaches

            if P_out_pct == P_out_0_pct + self.par.p_change_st_pct * self.ts:
                W_compens = 0
                W_compens_loss = 0
            elif P_out_pct - self.par.p_change_sd_pct * self.ts < 0:
                W_compens = 0
                W_compens_loss = 0
            else:
                W_compens = (self.par.p_change_sd_pct * self.ts / self.par.P_out_min_pct) \
                            * self.par.W_preparation
                W_compens_loss = (self.par.p_change_sd_pct * self.ts /
                                  self.par.P_out_min_pct) * self.par.W_preparation_heat

            # Energy amount for 'changing heatup state'
            W_startup = ((heatup_pct - self.state.heatup_pct) / 100 * self.par.W_preparation)

            W_startup_combined = W_compens + W_startup

            # State variables
            state_W_in_01 = W_startup_combined
            state_W_loss_01 = state_W_in_01 * ((100 - self.par.eta_preparation) /
                                               100) + W_compens_loss

            state_P_in = state_W_in_01 / (self.ts / 60)
            state_P_loss = state_W_loss_01 / (self.ts / 60)

            # No output energy / load for heatup / coastdown state
            state_W_out_01 = 0
            state_P_out = 0

        elif (heatup_pct < 100) and (P_out_pct < P_out_0_pct):  # Coasting down

            # If required calculate operating portion of input energy
            if self.state.heatup_pct == 100:
                eta_pct_01 = (self.state.eta_pct +
                              self.par.eta_pct_ip(self.par.P_out_min_pct).item(0)) / 2

                W_in_01_operation = ((self.state.P_in + self.par.P_in_min) /
                                     2 * (load_operation_time / 60))
                W_loss_01_operation = W_in_01_operation * (100 - eta_pct_01) / 100
                W_out_01 = (self.state.P_out + self.par.P_out_min) / 2 * (
                        load_operation_time / 60)
            else:
                W_in_01_operation = 0
                W_loss_01_operation = 0
                W_out_01 = 0

            coastdown_time = self.ts - load_operation_time

            P_out_cooldownst_pct = min(P_out_0_pct, self.par.P_out_min_pct)
            # Maximal cooldown during give time:
            diff_cooldown_max_pct = min(self.par.p_change_sd_pct * coastdown_time,
                                        P_out_cooldownst_pct)

            # If required calculate energy amount for coast down
            if P_out_pct > P_out_cooldownst_pct - diff_cooldown_max_pct:
                diff_load_perc = P_out_pct - (P_out_cooldownst_pct - diff_cooldown_max_pct)
                W_diff = diff_load_perc / self.par.P_out_min_pct * self.par.W_preparation
                W_in_01_coastdown = W_diff
            else:
                W_in_01_coastdown = 0

            W_loss_01_coastdown = (diff_cooldown_max_pct /
                                   self.par.P_out_min_pct) * self.par.W_preparation_heat

            # New state variables
            state_W_in_01 = W_in_01_coastdown + W_in_01_operation
            state_W_loss_01 = W_loss_01_coastdown + W_loss_01_operation

            # Power at end of time step is mean energy of coast down, not inluding prior load
            # operation
            state_P_in = W_in_01_coastdown / (coastdown_time / 60)
            state_P_loss = W_loss_01_coastdown / (coastdown_time / 60)

            # No output load for heatup/coastdown state
            state_P_out = 0
            state_W_out_01 = W_out_01

        else:  # Load Operation

            # Energy calculations
            P_out = self.par.P_out_rated * (P_out_pct / 100)

            W_out_01 = (max(self.state.P_out, self.par.P_out_min) + P_out) / 2 * (
                    load_operation_time / 60)

            P_in = P_out / (eta_perc_1 / 100)

            # If required calculate starting portion of input energy
            if self.state.heatup_pct < 100:
                # starting_time = self.ts - load_operation_time
                W_startup = ((heatup_pct - self.state.heatup_pct) / 100 * self.par.W_preparation)

                W_in_01_starting = W_startup
                W_loss_01_starting = W_startup * ((100 - self.par.eta_preparation) / 100)

                W_in_01_operation = (self.par.P_in_min + P_in) / 2 * (load_operation_time / 60)
                eta_pct_op1 = (self.par.eta_pct_ip(self.par.P_out_min_pct).item(0) +
                               eta_perc_1) / 2
                W_loss_01_operation = W_in_01_operation * (100 - eta_pct_op1) / 100

            else:
                W_in_01_starting = 0
                W_loss_01_starting = 0
                W_in_01_operation = (self.state.P_in + P_in) / 2 * (load_operation_time / 60)
                eta_pct_01 = (self.state.eta_pct + eta_perc_1) / 2
                W_loss_01_operation = W_in_01_operation * (100 - eta_pct_01) / 100

            W_in_01_combined = W_in_01_starting + W_in_01_operation
            W_loss_01_combined = W_loss_01_starting + W_loss_01_operation
            P_loss = P_in * (100 - eta_perc_1) / 100

            # New state variables
            state_W_in_01 = W_in_01_combined
            state_W_out_01 = W_out_01
            state_W_loss_01 = W_loss_01_combined

            state_P_in = P_in
            state_P_out = P_out
            state_P_loss = P_loss

        state_heatup_pct = heatup_pct
        state_eta_pct = eta_perc_1
        state_opex_Eur = None
        state_errorcode = error

        # Energy balance checks
        # ---------------------------------------------------------
        W_heatup = (heatup_pct - self.state.heatup_pct) / 100 * self.par.W_preparation_heat
        state_W_balance = state_W_in_01 - state_W_out_01 - state_W_loss_01 - W_heatup

        if not hypothetical_step:
            # New state variables
            self.state.W_in_01 = state_W_in_01
            self.state.W_out_01 = state_W_out_01
            self.state.W_loss_01 = state_W_loss_01

            self.state.P_in = state_P_in
            self.state.P_out = state_P_out
            self.state.P_loss = state_P_loss

            self.state.heatup_pct = state_heatup_pct
            self.state.eta_pct = state_eta_pct

            self.state.W_balance_01 = state_W_balance

            # To Be implemented
            self.state.opex_Eur = state_opex_Eur
            self.state.errorcode = state_errorcode

        else:
            hypothetical_state = dict()
            hypothetical_state["W_in_01"] = state_W_in_01
            hypothetical_state["W_out_01"] = state_W_out_01
            hypothetical_state["W_loss_01"] = state_W_loss_01
            hypothetical_state["W_balance_01"] = state_W_balance

            hypothetical_state["P_in"] = state_P_in
            hypothetical_state["P_out"] = state_P_out
            hypothetical_state["P_loss"] = state_P_loss
            hypothetical_state["heatup_pct"] = state_heatup_pct
            hypothetical_state["state_eta_pct"] = state_eta_pct

            hypothetical_state["opex_Eur"] = state_opex_Eur
            hypothetical_state["errorcode"] = state_errorcode

            return hypothetical_state

    def step_action_stationary(self, action: float) -> None:
        """
        Performs step_action() until target "action" is reached.
        Condition for stationarity:
        W_in_01 @ t-1 == W_in_01 @ t
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
            W_in_0 = self.state.W_in_01
            self.step_action(action)
            P_out_pct = self.state.P_out / self.par.P_out_rated * 100
            W_in_1 = self.state.W_in_01
            if W_in_0 == W_in_1:
                cond = True
            ct_iteration += 1

        # Final Step
        self.step_action(action)

        if ct_iteration == 100:
            raise Exception("Stationary step did not converge.")
        pass

    def target_from_target_input(self, input_load: float) -> float:
        """
        Calculation of action (= load target [0,1]) for step_action()-Method equivalent to
        given input load requirement [kW]

        Only usable for load operation!
        Returns error if input_load < minimum input load.

        Solves:

            Find P_out for given P_in in:
            P_in * eta(P_out)/ 100 = P_out

        #IDEA: Could use one of the new eta_input-curves instead
                --> Implemented


        :param input_load: float, Input load [kW]

        """

        # def func(x):
        #     return input_load / self.par.p_out * self.eta(x * 100) / 100 - x

        # Check if input_load is above required minimum
        if input_load < self.par.P_in_min:
            raise Exception("Input load too low for action")
        elif input_load > self.par.P_in_max:
            raise Exception("Input load too high for action")
        else:
            # root = fsolve(func, [0], full_output=True)
            # val = root[0][0]
            # conv = root[2]
            P_out = input_load * self.par.eta_in_kW_ip(input_load)

            return P_out / self.par.P_out_rated

    def P_in_from_P_out(self, output_load: float) -> float:
        """
        Simple function that applies output load in kW and get equivalent input load [kW].
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
            input_load = output_load / (self.par.eta_pct_ip(output_load_perc) / 100)
            return input_load

    def reset(self):
        """
        Reset to initial state
        (e.g. for ML/RL-Algorithms)
        :return:
        """
        self.state = copy.deepcopy(self.state_initial)


if __name__ == "__main__":
    """
    See /test for demonstration and tests
    """
    ...
