"""
Unified 0D energy conversion component class
"""
from dataclasses import dataclass
from scipy import interpolate
from energysys_components.various.normalization import denorm
from energysys_components.energy_carrier import ECarrier
import copy
import logging


@dataclass(frozen=False)
class ECCParameter:
    """
    Parameter of energy conversion component
    """
    name: str

    # Definition of energy carriers
    E_in_mc_type: ECarrier
    E_in_sd1_type: ECarrier
    E_in_sd2_type: ECarrier
    E_out_type: ECarrier

    # Startup
    t_start: float  # Time until system is available [Minutes] ("idle") [min]
    E_start: float  # Preparation Energy (from cold to idle) [kWh]
    eta_start: float  # For calculation of losses below operation [-]

    # Load Operation
    P_out_rated: float  # Rated Load [kW]
    P_out_min_rel: float  # Minimum operating load / rated power [-]

    p_change_pos: float  # [% output load/min]
    p_change_neg: float  # [% output load/min]

    E_loadchange: list  # load change dependend additional required energy
    # (example: due to SOFC stack temperature increase)  [[load [-]],[Energy [kWh]]]

    # Overall component efficiency
    eta: list  # load dependend efficiency  [[load [-]],[efficiency [-]]]
    # Main conversion path efficiency
    eta_mc: list  # load dependend efficiency  [[load [-]],[efficiency [-]]]

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

    def __post_init__(self):
        """
        Calculation of interpolators, ...

        Returns
        -------

        """

        # Startup calculations
        # ---------------------------------------------------------
        self.E_start_heatup = self.E_start * self.eta_start
        self.E_start_loss = self.E_start - self.E_start_heatup

        # Shutdown calculations
        # ---------------------------------------------------------
        # Based on par.t_cooldown & par.min_load_perc calculate
        # cool down decrease per time [%/min]
        # Example:  min_load_perc = 5%, cooldown_time= 30min
        #           --> cooldown_decr =  2.5% / min
        # self.p_change_sd_pct = self.P_out_min_rel / self.t_cooldown

        # Efficiency calculations - overall component
        # ---------------------------------------------------------

        # Interpolator eta(output power rel [-]) [-]
        self.eta_ip = interpolate.interp1d(self.eta[0],
                                           self.eta[1],
                                           kind='linear',
                                           bounds_error=False,
                                           fill_value=(self.eta[1][0],
                                                       self.eta[1][-1]))

        # Interpolator eta(output power [kW]) [-]
        self.eta_kW_ip = interpolate.interp1d(
            [e * self.P_out_rated for e in self.eta[0]],
            self.eta[1],
            kind='linear',
            bounds_error=False,
            fill_value=(self.eta[1][0],
                        self.eta[1][-1]))

        # Interpolator eta(input load [kW]) [-]
        # list_P_out_kW = [P_rel * self.P_out_rated for P_rel in self.eta[0]]
        list_P_in_kW = [P_rel * self.P_out_rated / self.eta_ip(P_rel) for P_rel in self.eta[0]]
        # list_eta_in_kW = [ol / il * 100 if il != 0 else 0 for ol, il in
        #                   zip(list_P_out_kW, list_P_in_kW)]

        self.eta_P_in_kW_ip = interpolate.interp1d(
            list_P_in_kW,
            self.eta[1],
            kind='linear',
            bounds_error=False,
            fill_value=(self.eta[1][0],
                        self.eta[1][-1]))

        # Efficiency calculations - main conversion path
        # ---------------------------------------------------------

        # Interpolator eta_mc(output load [-]) [-]
        self.eta_mc_ip = interpolate.interp1d(self.eta_mc[0],
                                              self.eta_mc[1],
                                              kind='linear',
                                              bounds_error=False,
                                              fill_value=(self.eta_mc[1][0],
                                                          self.eta_mc[1][-1]))

        # Interpolator eta_mc(output load [kW]) [-]
        self.eta_mc_kW_ip = interpolate.interp1d(
            [e * self.P_out_rated for e in self.eta_mc[0]],
            self.eta_mc[1],
            kind='linear',
            bounds_error=False,
            fill_value=(self.eta_mc[1][0],
                        self.eta_mc[1][-1]))

        # Interpolator eta_mc(input load [kW]) [%]
        # list_P_out_kW = [ol_perc / 100 * self.P_out_rated for ol_perc in self.eta_mc[0]]
        list_P_in_mc_kW = [ol_perc * self.P_out_rated /
                           (self.eta_mc_ip(ol_perc)) for ol_perc in self.eta_mc[0]]
        # list_eta_in_kW = [ol / il * 100 if il != 0 else 0 for ol, il in
        #                   zip(list_P_out_kW, list_P_in_kW)]

        self.eta_mc_P_in_mc_kW_ip = interpolate.interp1d(
            list_P_in_mc_kW,
            self.eta_mc[1],
            kind='linear',
            bounds_error=False,
            fill_value=(self.eta_mc[1][0],
                        self.eta_mc[1][-1]))

        # Load change energy interpolator Energy_state=f(Load [%])
        # ---------------------------------------------------------
        self.E_loadchange_ip = interpolate.interp1d(self.E_loadchange[0],
                                                    self.E_loadchange[1],
                                                    kind='linear',
                                                    bounds_error=False,
                                                    fill_value=(self.E_loadchange[1][0],
                                                                self.E_loadchange[1][-1]))

        # Characteristic loads
        # ---------------------------------------------------------
        # https://stackoverflow.com/questions/2474015/
        # "Getting the index of the returned max or min item using max()/min() on a list"
        self.P_out_etamax_rel = self.eta[0][max(range(len(self.eta[1])),
                                                key=self.eta[1].__getitem__)]

        self.P_out_min = self.P_out_min_rel * self.P_out_rated
        self.P_out_etamax = self.P_out_etamax_rel * self.P_out_rated

        self.P_in_min = self.P_out_min / self.eta_ip(self.P_out_min_rel)
        self.P_in_max = self.P_out_rated / self.eta_ip(1)
        self.P_in_etamax = self.P_out_etamax / self.eta_ip(self.P_out_etamax)

        self.P_in_mc_min = self.P_out_min / self.eta_mc_ip(self.P_out_min_rel)
        self.P_in_mc_max = self.P_out_rated / self.eta_mc_ip(1)
        self.P_in_mc_etamax = self.P_out_etamax / self.eta_mc_ip(self.P_out_etamax_rel)

        self.split_P_sd1 = self.split_P_sd[0] / sum(self.split_P_sd)
        self.split_P_sd2 = self.split_P_sd[1] / sum(self.split_P_sd)


@dataclass(frozen=False)
class ECCState:
    """
    State definition of energy conversion component (ECC)
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

    # Heat
    P_heat: float = 0  # [kW]
    E_heat: float = 0  # [kWh]

    heatup: float = 0  # [-]
    eta: float = 0  # [-]
    eta_mc: float = 0  # [-]
    opex_Eur: float = 0  # [€]

    # Convergence
    E_balance: float = 0  # [kWh]

    # Following are not really state variables, could be implemented here for optimization / ML
    # capex_Eur: float = 0  # [€]
    # volume: float = 0     # [m^^3]
    # weight: float = 0     # [kg]

    # errorcode: int = 0  # not implemented yet


class EnergyConversionComponent:
    """
    Energy Conversion Component (ECC) class
    """

    def __init__(self, par: ECCParameter,
                 ts: float,
                 state: ECCState = ECCState(),
                 # debug: bool = False
                 ):
        """
        :param par:         ECCParameter dataclass object
        :param state:       ECCState dataclass object
        :param ts:          timestep [min]
        # :param debug:     bool, not implemented yet
        """

        self.par = par
        self.ts = ts
        self.state_initial = copy.deepcopy(state)  # Copy of initial state for reset()-method
        self.state = state
        self.logger = logging.getLogger(__name__)

    def step_action(self,
                    contr_val: float,
                    hypothetical_step: bool = False,
                    contr_type: str = "target",
                    contr_lim_min: float = 0.,
                    contr_lim_max: float = 1.):

        """
        Function to change the state of the EnergyConversionComponent (ECC) from t=i to t=i+ts



        :param contr_val:  float, control value
        :param hypothetical_step: bool, If True, run method without updating self.state

        :param contr_lim_max:   Maximum control value
        :param contr_lim_min:   Minimum control value

         :param contr_type: str, "target" (default) |"change"
            Two different ways of controlling the ECC are implemented (contr_type):

            contr_type = "target" (default)
                contr_val=contr_lim_min: Target power of component 0%
                contr_val=contr_lim_max: Target power of component 100%


            contr_type = "change" (no up-to-date implementation!)

                contr_val=contr_lim_min:   Maximum (possible) deloading,
                contr_val=mean(contr_lim_min,contr_lim_max):    Keep current state
                contr_val=contr_lim_max:    Maximum (possible) loading


         Structure:

         1.) State calculations prior to application of contr_val
         2.) Application of state change
         3.) Efficiency calculations
         4.) Calculation of updated state
         5.) Energy balance calculation
         6.) Update state variables

        """
        # error = 0  # Init error code

        # 1.) State calculations prior to application of contr_val
        # ---------------------------------------
        # Info: Below minimum power, the real component output load is zero.
        #       However for calculation of changes in heatup or cooldown states it is
        #       used as an artificial variable "P_out_rel_0"

        if self.state.heatup < 1:
            P_out_rel_0 = round(self.state.heatup * self.par.P_out_min_rel, 6)
        else:
            P_out_rel_0 = round(self.state.P_out / self.par.P_out_rated, 6)

        # 2.) Application of state change
        # ---------------------------------------------------------
        if not contr_type == "target":
            raise Exception('No up-to-date implementation of this contr_val type.')

        else:  # --> Control type: target

            # Limit input to valid contr_val range
            if contr_val > contr_lim_max:
                self.logger.warning('contr_val > contr_lim_max, corrected to '
                                    'contr_val=contr_lim_max')
                contr_val = contr_lim_max
            elif contr_val < contr_lim_min:
                self.logger.warning('contr_val < contr_lim_min, corrected to '
                                    'contr_val=contr_lim_min')
                contr_val = contr_lim_min

            # Denormalize contr_val to relative load based on defined control limits
            # (contr_lim_min & contr_lim_max)
            # Reason for implementation: Simple way to use different types of normalization for ML
            P_out_targ_rel = denorm(contr_val, {'n': [contr_lim_min, contr_lim_max],
                                                'r': [0, 1]})

        # Calculation of new heatup and output power
        (P_out_rel_1,
         heatup_1, operation_time) = self._calc_P_change(P_out_rel_targ=P_out_targ_rel)

        # 3.) Efficiency calculation (for step 1)
        # ---------------------------------------------------------
        if heatup_1 < 1:
            eta_1 = self.par.eta_start
            eta_mc_1 = 1
        else:
            eta_1 = self.par.eta_ip(P_out_rel_1).item(0)
            eta_mc_1 = self.par.eta_mc_ip(P_out_rel_1).item(0)

        # 4.) Energy Calculation
        # ---------------------------------------------------------
        state_1_dict = self._calc_E_change(P_out_rel_1,
                                           P_out_rel_0,
                                           heatup_1,
                                           operation_time,
                                           eta_1,
                                           eta_mc_1)

        # 6.) Update state
        # ---------------------------------------------------------

        state_1 = ECCState(E_in=state_1_dict["E_in"],
                           E_in_mc=state_1_dict["E_in_mc"],
                           E_in_sd1=state_1_dict["E_in_sd1"],
                           E_in_sd2=state_1_dict["E_in_sd2"],
                           E_out=state_1_dict["E_out"],
                           E_loss=state_1_dict["E_loss"],
                           E_heat=state_1_dict["E_heat"],
                           E_balance=state_1_dict["E_balance"],

                           P_in=state_1_dict["P_in"],
                           P_in_mc=state_1_dict["P_in_mc"],
                           P_in_sd1=state_1_dict["P_in_sd1"],
                           P_in_sd2=state_1_dict["P_in_sd2"],
                           P_out=state_1_dict["P_out"],
                           P_loss=state_1_dict["P_loss"],
                           P_heat=state_1_dict["P_heat"],

                           heatup=heatup_1,
                           eta=eta_1,
                           eta_mc=eta_mc_1,
                           opex_Eur=0)

        if not hypothetical_step:
            self.state = state_1

            pass

        else:
            return state_1

    def _calc_P_change(self, P_out_rel_targ) -> (float, float, float):
        """
        Calculate new output power P

        Considers different power change regions...
          - [0,self.par.P_out_min_rel):   Startup/Shutdown area   [S]
          - [self.par.P_out_min_rel,100]: Operation range         [O]

        results in 3 cases for load increase: [S->S, S->O, O->O],
        and 3 cases for load decrease:        [O->O, O->S, S->S].

        :param P_out_rel_targ: Target load [%]

        :return: P_out_rel_1  new P_out_rel [-]
        :return: heatup new heatup state [-]
        :return: operation_time time in operation [min]
        """
        # Initialization
        # ---------------------------------------
        # Additional state calculations prior to contr_val
        # Info: Below minimum load corner point, real component output load is zero.
        #               However for calculation of changes in heatup or cooldown states it is
        #               used as an artificial variable (for simplicity) and is therefore calculated
        #               below based on the below-load-operation state variable heatup_pct.
        #               It is used only internally.

        if self.state.heatup < 1:
            P_out_rel_0 = round(self.state.heatup * self.par.P_out_min_rel, 6)
        else:
            P_out_rel_0 = round(self.state.P_out / self.par.P_out_rated, 6)

        # Positive load changes & load holding
        # ---------------------------------------
        if P_out_rel_0 <= P_out_rel_targ:

            # [S->S]
            if P_out_rel_targ < self.par.P_out_min_rel:
                P_out_rel_1 = min(P_out_rel_targ,
                                  P_out_rel_0 + self.ts / self.par.t_start * self.par.P_out_min_rel)

                operation_time = 0

            # [S->O (potentially)]
            elif (P_out_rel_targ >= self.par.P_out_min_rel) and \
                    (P_out_rel_0 < self.par.P_out_min_rel):

                # P_rel to min. load
                start_P_delta_rel = self.par.P_out_min_rel - P_out_rel_0
                # time to min. load
                start_time = start_P_delta_rel / self.par.P_out_min_rel * self.par.t_start

                if start_time <= self.ts:  # --> "O" will be reached
                    operation_time = self.ts - start_time
                    P_out_rel_1 = min(P_out_rel_targ,
                                      self.par.P_out_min_rel + self.par.p_change_pos /
                                      100 * operation_time)
                else:  # --> "O" can't be reached
                    operation_time = 0
                    P_out_rel_1 = min(P_out_rel_targ,
                                      P_out_rel_0 + self.ts /
                                      self.par.t_start * self.par.P_out_min_rel)

            # [O->O]
            else:

                P_out_rel_1 = min(P_out_rel_targ,
                                  P_out_rel_0 + self.par.p_change_pos / 100 * self.ts)
                operation_time = self.ts

        # Negative load changes
        # ---------------------------------------
        else:
            # [O->O]
            if P_out_rel_targ >= self.par.P_out_min_rel:
                P_out_rel_1 = max(P_out_rel_targ,
                                  P_out_rel_0 - self.par.p_change_neg / 100 * self.ts)
                operation_time = self.ts

            # [O->S(potentially)]
            elif (P_out_rel_targ < self.par.P_out_min_rel) and \
                    (P_out_rel_0 >= self.par.P_out_min_rel):

                unload_P_delta_rel = P_out_rel_0 - self.par.P_out_min_rel  # P rel to min load
                unload_time = unload_P_delta_rel / (self.par.p_change_neg / 100)  # time to min load

                if unload_time < self.ts:  # --> shutdown mode reached
                    P_out_rel_1 = max(P_out_rel_targ,
                                      self.par.P_out_min_rel * (1 - (
                                              self.ts - unload_time) / self.par.t_cooldown))
                    operation_time = unload_time

                else:  # --> shutdown mode not reached
                    P_out_rel_1 = max(P_out_rel_targ,
                                      P_out_rel_0 - self.par.p_change_neg / 100 * self.ts)
                    operation_time = self.ts
            # [S->S]
            else:

                P_out_rel_1 = max(P_out_rel_targ,
                                  P_out_rel_0 - self.par.P_out_min_rel /
                                  self.par.t_cooldown * self.ts)
                operation_time = 0

        heatup = min(1, P_out_rel_1 / self.par.P_out_min_rel)

        if (heatup == 1) and (operation_time == 0):
            operation_time = 1e-5

        return P_out_rel_1, heatup, operation_time

    def _calc_E_change(self,
                       P_out_rel_1,
                       P_out_rel_0,
                       heatup_1,
                       operation_time,
                       eta_1,
                       eta_mc_1) -> dict:
        """
        Energy calculation from prior state P_out_0_pct to new state P_out_pct
        Case distinction required:
         - load operation -> load operation [L->L]
         - noLoad operation -> noLoad operation [NL->NL]
         - load operation -> noLoad operation [L->NL]
         - noLoad operation -> load operation [NL->L]

        :return: state_1: dict
        """

        # Init return dict
        state_1 = dict.fromkeys(['E_in', 'E_in_mc', 'E_loss', "E_in_sd1", "E_in_sd2", "E_out",
                                 "E_heat", "E_balance",
                                 'P_in', 'P_in_mc_op', 'P_loss', "P_in_sd1", "P_in_sd2", "P_out",
                                 "P_heat"])

        # [NL->NL], P_out_rel_1 >= P_out_rel_0
        # (if required) Energy amount for 'holding prior idle state (loss compensation)'
        if (heatup_1 < 1) and (P_out_rel_1 >= P_out_rel_0):
            E_in_mc_op = 0
            P_in_mc_op = 0

            # Calculation of additional energy amounts for compensating slower startups
            if P_out_rel_1 == P_out_rel_0 + self.ts / self.par.t_start * self.par.P_out_min_rel:
                # -> Maximum start/heatup speed
                # Loss during pure startup is expected to be included in given E_start
                # and therefore no additional compensation is required
                E_compens = 0
                # E_compens_loss = 0

            elif P_out_rel_1 - self.ts / self.par.t_start * self.par.P_out_min_rel < 0:
                # In low start/heatup state, compesation is neglected, which is
                # sufficient for rule based control (as this is no reasonable target state),
                # however needs to be refined for advanced control #IDEA
                E_compens = 0
                # E_compens_loss = 0

            elif P_out_rel_1 == P_out_rel_0:
                # calculate compensation energy and loss of it (just for holding the state)
                E_compens = self.ts / self.par.t_cooldown * self.par.E_start
                # E_compens_loss = E_compens

            else:
                P_out_rel_1_max = P_out_rel_0 + self.ts / self.par.t_start * self.par.P_out_min_rel
                fact = (P_out_rel_1 - P_out_rel_0) / (P_out_rel_1_max - P_out_rel_0)

                # calculate compensation energy and loss of it
                E_compens = fact * (self.ts / self.par.t_cooldown * self.par.E_start)
                # E_compens_loss = E_compens

            E_compens_loss = (1 - self.par.eta_start) * E_compens
            # Energy amount for 'changing heatup state'
            E_startup = (heatup_1 - self.state.heatup) * self.par.E_start
            E_startup_loss = (heatup_1 - self.state.heatup) * self.par.E_start_loss

            # Outlet
            E_out = 0
            P_out = 0

            # Inlet combined
            E_in_op = 0
            E_in_no = E_compens + E_startup
            P_in = E_in_no / (self.ts / 60)

            # Inlet secondary
            E_in_sd1_op = 0
            E_in_sd2_op = 0
            E_in_sd1_no = self.par.split_P_sd1 * E_in_no
            E_in_sd2_no = self.par.split_P_sd2 * E_in_no

            P_in_sd1 = E_in_sd1_no / (self.ts / 60)
            P_in_sd2 = E_in_sd2_no / (self.ts / 60)

            # Loss
            E_loss_op = 0
            E_loss_no = E_compens_loss + E_startup_loss
            P_loss = E_loss_no / (self.ts / 60)

        # [xx->NL] (Towards) No-load Operation
        elif (heatup_1 < 1) and (P_out_rel_1 < P_out_rel_0):
            P_out = 0
            P_in_mc_op = 0

            # Operation (_op) calculations
            if self.state.heatup == 1:
                # Load change adders
                E_loadchange = (self.par.E_loadchange_ip(self.par.P_out_min_rel) -
                                self.par.E_loadchange_ip(P_out_rel_0))

                E_in_loadchange = max(0, E_loadchange)
                E_loss_op_loadchange = abs(min(0, E_loadchange))

                # Outlet
                E_out = (self.state.P_out + self.par.P_out_min) / 2 * (
                        operation_time / 60)

                # Inlet main conversion
                E_in_mc_op = ((self.state.P_in_mc + self.par.P_in_mc_min) /
                              2 * (operation_time / 60))

                # Inlet combined
                E_in_op_wo_loadchange = ((self.state.P_in + self.par.P_in_min) / 2 *
                                         (operation_time / 60))
                E_in_op = E_in_op_wo_loadchange + E_in_loadchange

                # Inlet secondary
                E_in_sd_op_wo_loadchange = E_in_op - E_in_mc_op
                E_in_sd_op = E_in_sd_op_wo_loadchange + E_in_loadchange
                E_in_sd1_op = self.par.split_P_sd1 * E_in_sd_op
                E_in_sd2_op = self.par.split_P_sd2 * E_in_sd_op

                # Loss
                E_loss_op_wo_loadchange = E_in_op_wo_loadchange - E_out
                E_loss_op = E_loss_op_wo_loadchange + E_loss_op_loadchange

            else:
                E_in_op = 0
                E_in_mc_op = 0
                E_in_sd1_op = 0
                E_in_sd2_op = 0
                E_loss_op = 0
                E_out = 0

            # Non-operational (_no) calculations
            cooldown_time = self.ts - operation_time

            P_out_no_rel_st = min(P_out_rel_0, self.par.P_out_min_rel)  # PStart of coast down

            #  Max. (hypothetically) cooldown during given time:
            P_diff_no_rel_max = min(
                self.par.P_out_min_rel / self.par.t_cooldown * cooldown_time,
                P_out_no_rel_st)

            # If required calculate energy amount for coast down (for superposed energy input)
            if P_out_rel_1 > P_out_no_rel_st - P_diff_no_rel_max:
                P_diff_no = P_out_rel_1 - (P_out_no_rel_st - P_diff_no_rel_max)

                fact = P_diff_no / P_diff_no_rel_max

                # calculate compensation energy and loss of it
                E_in_no = fact * (cooldown_time / self.par.t_cooldown * self.par.E_start)

                E_in_sd1_no = self.par.split_P_sd1 * E_in_no
                E_in_sd2_no = self.par.split_P_sd2 * E_in_no

            else:
                E_in_no = 0
                E_in_sd1_no = 0
                E_in_sd2_no = 0

            P_in = E_in_no / (cooldown_time / 60)
            P_in_sd1 = E_in_sd1_no / (cooldown_time / 60)
            P_in_sd2 = E_in_sd2_no / (cooldown_time / 60)

            E_loss_no = (
                        cooldown_time / self.par.t_cooldown * self.par.E_start * self.par.eta_start +
                        E_in_no * (1 - self.par.eta_start))
            P_loss = E_loss_no / (cooldown_time / 60)

        # [xx->L] (Towards) Load Operation
        else:

            # Heatup (_no) calculations
            # ----------------------------
            if self.state.heatup < 1:
                E_in_no = ((heatup_1 - self.state.heatup) * self.par.E_start)
                E_in_sd1_no = self.par.split_P_sd1 * E_in_no
                E_in_sd2_no = self.par.split_P_sd2 * E_in_no
                E_loss_no = E_in_no * (1 - self.par.eta_start)

            else:
                E_in_no = 0
                E_loss_no = 0
                E_in_sd1_no = 0
                E_in_sd2_no = 0

            # Operation (_op) calculations with and without (wo) loadchange
            # ----------------------------
            # Load change adders
            E_loadchange = (self.par.E_loadchange_ip(P_out_rel_1) -
                            self.par.E_loadchange_ip(P_out_rel_0))
            E_in_loadchange = max(0, E_loadchange)
            E_loss_op_loadchange = abs(min(0, E_loadchange))

            P_in_loadchange = E_in_loadchange / (operation_time / 60)
            P_in_sd1_loadchange = self.par.split_P_sd1 * P_in_loadchange
            P_in_sd2_loadchange = self.par.split_P_sd2 * P_in_loadchange

            # Outlet
            P_out = self.par.P_out_rated * P_out_rel_1
            E_out = (max(self.state.P_out, self.par.P_out_min) + P_out) / 2 * (
                    operation_time / 60)

            # Inlet main conversion
            P_in_mc_op = P_out / eta_mc_1
            E_in_mc_op = ((max(self.state.P_in_mc, self.par.P_in_mc_min) + P_in_mc_op) /
                          2 * (operation_time / 60))

            # Inlet combined
            # Todo: erst mit P_in0 Ein_ges rechnen, dann von hier aufteilen
            E_in_op =  

            P_in_op_wo_loadchange = P_out / eta_1
            P_in = P_in_op_wo_loadchange + P_in_loadchange

            E_in_op_wo_loadchange = (max(self.state.P_in,
                                         self.par.P_in_min) + P_in_op_wo_loadchange) / 2 * (
                                            operation_time / 60)
            E_in_op = E_in_op_wo_loadchange + E_in_loadchange

            # Inlet secondary
            E_in_sd_op_wo_loadchange = E_in_op_wo_loadchange - E_in_mc_op
            E_in_sd_op = E_in_sd_op_wo_loadchange + E_in_loadchange
            E_in_sd1_op = self.par.split_P_sd1 * E_in_sd_op
            E_in_sd2_op = self.par.split_P_sd2 * E_in_sd_op

            P_in_sd1_op_wo_loadchange = (P_in_op_wo_loadchange - P_in_mc_op) * self.par.split_P_sd1
            P_in_sd2_op_wo_loadchange = (P_in_op_wo_loadchange - P_in_mc_op) * self.par.split_P_sd2
            P_in_sd1 = P_in_sd1_op_wo_loadchange + P_in_sd1_loadchange
            P_in_sd2 = P_in_sd2_op_wo_loadchange + P_in_sd2_loadchange

            # Loss
            E_loss_op_wo_loadchange = E_in_op_wo_loadchange - E_out
            P_loss_op_wo_loadchange = P_in_op_wo_loadchange - P_out
            E_loss_op = E_loss_op_wo_loadchange + E_loss_op_loadchange
            P_loss = P_loss_op_wo_loadchange + P_loss_op_wo_loadchange

        # Summation of operation and non-operation energy portions
        E_in = E_in_op + E_in_no
        E_in_sd1 = E_in_sd1_op + E_in_sd1_no
        E_in_sd2 = E_in_sd2_op + E_in_sd2_no
        E_loss = E_loss_op + E_loss_no

        E_heat = self.par.fact_P_heat_P_Loss * E_loss
        P_heat = self.par.fact_P_heat_P_Loss * P_loss

        # Balances
        tol = 1e-5

        if abs((E_in_op + E_in_no) - (E_in_mc_op + E_in_sd1 + E_in_sd2)) > tol:
            self.logger.warning(f"E_in deviation! Total: {E_in_op + E_in_no},"
                                f" splitted: {E_in_mc_op + E_in_sd1 + E_in_sd2}")

        if abs(P_in - (P_in_mc_op + P_in_sd1 + P_in_sd2)) > tol:
            self.logger.warning(f"P_in deviation! Total: {P_in},"
                                f" splitted: {P_in_mc_op + P_in_sd1 + P_in_sd2}")

        E_change_heatup = (heatup_1 - self.state.heatup) * self.par.E_start_heatup
        E_change_load = (self.par.E_loadchange_ip(max(self.par.P_out_min_rel, P_out_rel_1)) -
                         self.par.E_loadchange_ip(max(self.par.P_out_min_rel, P_out_rel_0)))

        E_balance = (E_in_mc_op + E_in_sd1 + E_in_sd2 -
                     E_change_heatup - E_change_load - E_out - E_loss)

        if abs(E_balance) > tol:
            self.logger.warning(f"Energy Balance deviation! {E_balance}")

        state_1.update(E_balance=E_balance,
                       E_in_mc=E_in_mc_op,
                       E_in=E_in,
                       E_in_sd1=E_in_sd1,
                       E_in_sd2=E_in_sd2,
                       E_loss=E_loss,
                       E_out=E_out,
                       P_in_mc=P_in_mc_op,
                       P_in=P_in,
                       P_in_sd1=P_in_sd1,
                       P_in_sd2=P_in_sd2,
                       P_loss=P_loss,
                       P_out=P_out,
                       E_heat=E_heat,
                       P_heat=P_heat
                       )

        return state_1

    def step_action_stationary(self,
                               contr_val: float,
                               max_iterations=100) -> None:
        """
        Performs step_action() until target "contr_val" is reached.
        Condition for stationarity:
        E_in @ t-1 == E_in @ t
        P_out @ t-1 == P_out @ t

        Parameters
        ----------
        :param contr_val:
        :param max_iterations:

        Returns
        -------


        """
        ct_iteration = 0

        # Denormalize contr_val to relative load based on defined control limits
        # (contr_lim_min & contr_lim_max)
        # Reason for implementation: Simple way to use different types of normalization for ML
        P_out_rel_targ = denorm(contr_val, {'n': [0, 1],
                                            'r': [0, 1]})

        P_out_rel_actual = self.state.P_out / self.par.P_out_rated

        E_cond = False
        while not ((P_out_rel_targ == P_out_rel_actual) and E_cond) and (
                ct_iteration <= max_iterations):
            E_in_0 = self.state.E_in
            self.step_action(contr_val)
            E_in_1 = self.state.E_in
            if E_in_0 == E_in_1:
                E_cond = True
            ct_iteration += 1

        # Final Step
        self.step_action(contr_val)

        if ct_iteration == 100:
            raise Exception("Target not reached.")
        pass

    def action_for_P_in_mc_target(self, P_in_mc_target: float) -> float:
        """
        Calculation of contr_val for step_action()-method equivalent to
        given main conversion input load requirement [kW]

        Only usable for load operation!
        Returns error if input_load < minimum input load.

        Solves:

            Find P_out for given P_in in:
            P_in * eta(P_out)/ 100 = P_out

        :param P_in_mc_target: float, Input load [kW]

        """

        if P_in_mc_target < self.par.P_in_mc_min:
            raise Exception("Input load too low for contr_val")
        elif P_in_mc_target > self.par.P_in_mc_max:
            raise Exception("Input load too high for contr_val")
        else:
            P_out_rel = (P_in_mc_target * self.par.eta_mc_kW_ip(P_in_mc_target) /
                         self.par.P_out_rated)

            return P_out_rel

    def action_for_E_in_mc_target(self, input_load: float) -> float:
        """
        Calculation of contr_val (= load target [0,1]) for step_action()-Method equivalent to
        given main conversion(!) input energy requirement [kWh]

        To be implemented
        """
        # To be implemented
        ...

    def P_in_mc_from_P_out(self, P_out: float) -> float:
        """
        Simple function that applies output load in kW and get equivalent main conversion
         input load [kW].
        Only usable for load operation
        Returns error if below minimum output load

        :param P_out:  Output load [kW]

        """

        # Check if P_in_mc_target is above required minimum
        if P_out < self.par.P_out_min:
            raise Exception("Output load too low for contr_val")
        elif P_out > self.par.P_out_rated:
            raise Exception("Output load too high for contr_val")
        else:
            P_in_mc = P_out / self.par.eta_mc_kW_ip(P_out)
            return P_in_mc

    def reset(self):
        """
        Reset to initial state
        (e.g. for ML/RL-Algorithms)

        :return:
        """
        self.state = copy.deepcopy(self.state_initial)


if __name__ == "__main__":
    """
    See /test for demonstration and example
    """
    ...
