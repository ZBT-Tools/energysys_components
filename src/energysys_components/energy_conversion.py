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
    E_in_start: float  # Preparation Energy (from cold to idle) [kWh]
    eta_start: float  # For calculation of losses below operation [-]

    # Load Operation
    P_out_rated: float  # Rated Load [kW]
    P_out_min_rel: float  # Minimum operating load / rated power [-]

    p_change_pos: float  # [% output load/min]
    p_change_neg: float  # [% output load/min]

    E_loadchange: list  # load change dependent additional required energy
    # (examples: due to SOFC stack temperature increase)  [[load [-]],[Energy [kWh]]]

    # Overall component efficiency
    eta: list  # load dependent efficiency  [[load [-]],[efficiency [-]]]
    # Main conversion path efficiency
    eta_mc: list  # load dependent efficiency  [[load [-]],[efficiency [-]]]

    # Shutdown
    t_cooldown: float  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd: list  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio

    # Factor usable heat in loss
    fact_P_heat_P_Loss: float  # [0,1] Factor of usable heat energy in loss

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
        # Actual component energy increase during heatup [kWh]
        self.E_start_bulk = self.E_in_start * self.eta_start
        # Loss during heatup [kWh]
        self.E_start_loss = self.E_in_start * (1 - self.eta_start)

        # Shutdown calculations
        # ---------------------------------------------------------
        # Based on par.t_cooldown & par.min_load_perc calculate
        # cool down decrease per time [%/min]
        # Example:  min_load_perc = 5%, cooldown_time= 30min
        #           --> cooldown_decr =  2.5% / min
        # self.p_change_sd_pct = self.P_out_min_rel / self.t_cooldown

        # Efficiency calculations - overall component
        # ---------------------------------------------------------
        # Interpolator eta = f(output power rel [-]) [-]
        self.eta_ip_P_out_rel = interpolate.interp1d(self.eta[0],
                                                     self.eta[1],
                                                     kind='linear',
                                                     bounds_error=False,
                                                     fill_value=(self.eta[1][0],
                                                       self.eta[1][-1]))

        # Interpolator eta = f(output power [kW]) [-]
        self.eta_ip_P_out = interpolate.interp1d([e * self.P_out_rated for e in self.eta[0]],
                                                 self.eta[1],
                                                 kind='linear',
                                                 bounds_error=False,
                                                 fill_value=(self.eta[1][0],
                                                          self.eta[1][-1]))

        # Interpolator eta = f(input load [kW]) [-]
        list_P_in_kW = [e * self.P_out_rated / self.eta_ip_P_out_rel(e) for e in self.eta[0]]
        self.eta_ip_P_in = interpolate.interp1d(list_P_in_kW,
                                                self.eta[1],
                                                kind='linear',
                                                bounds_error=False,
                                                fill_value=(self.eta[1][0],
                                                               self.eta[1][-1]))

        # Efficiency calculations - main conversion path
        # ---------------------------------------------------------

        # Interpolator eta_mc = f(output load [-]) [-]
        self.eta_mc_ip_P_out_rel = interpolate.interp1d(self.eta_mc[0],
                                                        self.eta_mc[1],
                                                        kind='linear',
                                                        bounds_error=False,
                                                        fill_value=(self.eta_mc[1][0],
                                                          self.eta_mc[1][-1]))

        # Interpolator eta_mc = f(output load [kW]) [-]
        self.eta_mc_ip_P_out = interpolate.interp1d(
            [e * self.P_out_rated for e in self.eta_mc[0]],
            self.eta_mc[1],
            kind='linear',
            bounds_error=False,
            fill_value=(self.eta_mc[1][0],
                        self.eta_mc[1][-1]))

        # Interpolator eta_mc = f(input load [kW]) [-]
        list_P_in_mc_kW = [e * self.P_out_rated / self.eta_mc_ip_P_out_rel(e) for e in self.eta_mc[0]]
        self.eta_mc_ip_P_in_mc = interpolate.interp1d(list_P_in_mc_kW,
                                                      self.eta_mc[1],
                                                      kind='linear',
                                                      bounds_error=False,
                                                      fill_value=(self.eta_mc[1][0],
                                                                     self.eta_mc[1][-1]))

        # Load change energy interpolator Energy_state=f(Load [%])
        # ---------------------------------------------------------
        self.E_in_loadchange_ip = interpolate.interp1d(self.E_loadchange[0],
                                                       self.E_loadchange[1],
                                                       kind='linear',
                                                       bounds_error=False,
                                                       fill_value=(self.E_loadchange[1][0],
                                                                   self.E_loadchange[1][-1]))

        # Characteristic loads
        # ---------------------------------------------------------
        # https://stackoverflow.com/questions/2474015/
        # "Getting the index of the returned max or min item using max()/min() on a list"
        self.P_out_min = self.P_out_min_rel * self.P_out_rated
        self.P_out_etamax_rel = self.eta[0][max(range(len(self.eta[1])), key=self.eta[1].__getitem__)]
        self.P_out_etamax = self.P_out_etamax_rel * self.P_out_rated

        self.P_in_min = self.P_out_min / self.eta_ip_P_out_rel(self.P_out_min_rel)
        self.P_in_max = self.P_out_rated / self.eta_ip_P_out_rel(1)
        self.P_in_etamax = self.P_out_etamax / self.eta_ip_P_out_rel(self.P_out_etamax)

        self.P_in_mc_min = self.P_out_min / self.eta_mc_ip_P_out_rel(self.P_out_min_rel)
        self.P_in_mc_max = self.P_out_rated / self.eta_mc_ip_P_out_rel(1)
        self.P_in_mc_etamax = self.P_out_etamax / self.eta_mc_ip_P_out_rel(self.P_out_etamax_rel)

        self.split_P_sd1 = self.split_P_sd[0] / sum(self.split_P_sd)
        self.split_P_sd2 = self.split_P_sd[1] / sum(self.split_P_sd)


@dataclass(frozen=False)
class ECCState:
    """
    State definition of energy conversion component (ECC)
    """

    # Bulk | Internal Energy
    E_bulk: float = 0  # [kWh]

    # Input
    P_in: float = 0  # [kW]
    E_in: float = 0  # [kWh]

    # Input, portion main conversion
    P_in_mc: float = 0  # [kW]
    E_in_mc: float = 0  # [kWh]

    # Input, portion secondary 1
    P_in_sd1: float = 0  # [kW]
    E_in_sd1: float = 0  # [kWh]

    # Input, portion secondary 2
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

    # Operation
    # f_operation: float = 1  # [-]
    heatup: float = 0  # [-]
    eta: float = 0  # [-]
    eta_mc: float = 0  # [-]
    opex_Eur: float = 0  # [€]

    # Health
    SoH: float = 1  # [-]

    # Convergence
    E_balance: float = 0  # [kWh]

    # Following are not really state variables, could be implemented here for optimization / ML
    # capex_Eur: float = 0  # [€]
    # volume: float = 0     # [m^^3]
    # weight: float = 0     # [kg]

    # errorcode: int = 0  # not implemented


class EnergyConversionComponent:
    """
    Energy Conversion Component (ECC) class
    """

    def __init__(self, par: ECCParameter,
                 ts: float,
                 state: ECCState = ECCState(),
                 ):
        """
        :param par:         ECCParameter dataclass object
        :param state:       ECCState dataclass object
        :param ts:          timestep [min]
        # :param debug:     bool, not implemented yet
        """
        if state is None:
            state: ECCState = ECCState()

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

         :param contr_type: str, "target" (default) |"change"
            Two different ways of controlling the ECC are implemented (contr_type):

            contr_type = "target" (default)
                contr_val=contr_lim_min: Target power of component 0% * P_rated
                contr_val=contr_lim_max: Target power of component 100% * P_rated


            contr_type = "change" (no up-to-date implementation!)
                contr_val=contr_lim_min:   Maximum (possible) deloading,
                contr_val=mean(contr_lim_min,contr_lim_max):    Keep current state
                contr_val=contr_lim_max:    Maximum (possible) loading

        # Idea: integrate into single "control_type" definition
        :param contr_lim_max:   Maximum control value
        :param contr_lim_min:   Minimum control value

         Structure:

         1.) Application of load change

         2.) Efficiency calculations

         3.) State change calculation

         4.) Update state variables

        """

        # 1.) Load change
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
            # Reason for implementation: Simple way to use different types of normalizations for ML
            P_out_rel_targ = denorm(contr_val, {'n': [contr_lim_min, contr_lim_max],
                                                'r': [0, 1]})

        # Calculation of new heatup state, output power and time in operation
        P_out_rel_1, heatup_1, t_op = self._calc_P_change(P_out_rel_targ=P_out_rel_targ)

        # 2.) Efficiency calculation
        # ---------------------------------------------------------
        if heatup_1 < 1:
            eta_1 = self.par.eta_start
            eta_mc_1 = 1
        else:
            eta_1 = self.par.eta_ip_P_out_rel(P_out_rel_1).item(0)
            eta_mc_1 = self.par.eta_mc_ip_P_out_rel(P_out_rel_1).item(0)

        # 3.) State change calculation
        # ---------------------------------------------------------
        state_1_dict = self._calc_state_change(P_out_rel_1=P_out_rel_1,
                                               heatup_1=heatup_1,
                                               t_op=t_op,
                                               eta_1=eta_1,
                                               eta_mc_1=eta_mc_1)

        # 4.) Update state
        # ---------------------------------------------------------
        state_1 = ECCState(**state_1_dict,
                           opex_Eur=0,
                           SoH=1)

        if not hypothetical_step:
            self.state = state_1
            return None

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

        :param P_out_rel_targ: Target load [-]

        :return: P_out_rel_1  new P_out_rel [-]
        :return: heatup_1 new heatup state [-]
        :return: t_op time in operation [min]
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

        heatup_1 = min(1, P_out_rel_1 / self.par.P_out_min_rel)

        if (heatup_1 == 1) and (operation_time == 0):
            operation_time = 1e-5

        return P_out_rel_1, heatup_1, operation_time

    def _calc_NL_NL_change(self,
                           heatup_0,
                           heatup_1,
                           dt,
                           include_power: bool
                           ):
        """
            Simple cases:
            - heatup with maximum energy input (NLNL1)
            - cooldown without any energy input (NLNL2)

            Compensation cases:
            - hold heatup/cooldown state (NLNL3)
            - increase heatup state less than max. energy (NLNL4)
            - cooldown with energy input (NLNL5)
        :param self:
        :return:
        """
        par = self.par

        # For all cases:
        # Energy amount for 'changing heatup state'
        E_in_no = max(0, (heatup_1 - heatup_0) * par.E_in_start)
        E_loss_no = max((heatup_0 - heatup_1) * par.E_start_bulk,  # cooldown
                        (heatup_1 - heatup_0) * par.E_start_loss)  # startup

        # Additional compensation energy calculations for NLNL3 - NLNL5
        # NLNL3
        if (heatup_1 == heatup_0) and (heatup_1 != 0):
            E_in_no_compens = min(1, dt / par.t_cooldown) * par.E_start_bulk
            E_loss_no_compens = E_in_no_compens

        # NLNL4
        elif (heatup_1 > heatup_0) and (heatup_1 < heatup_0 + dt / par.t_start):
            # Linear interpolation between NLNL1 and NLNL3
            fact = (heatup_1 - heatup_0) / (
                    min(1., heatup_0 + dt / par.t_start) - heatup_0)
            E_in_no_compens = (1 - fact) * (
                    min(1, dt / par.t_cooldown) * par.E_start_bulk)
            E_loss_no_compens = E_in_no_compens

        # NLNL5
        elif (heatup_1 < heatup_0) and (
                heatup_1 > heatup_0 - dt / par.t_cooldown):
            # Linear interpolation between NLNL2 and NLNL3
            fact = (heatup_0 - heatup_1) / (
                    heatup_0 - max(0., heatup_0 - dt / par.t_cooldown))
            E_in_no_compens = (1 - fact) * (
                    dt / par.t_cooldown * par.E_start_bulk)
            E_loss_no_compens = E_in_no_compens

        else:
            E_in_no_compens = 0
            E_loss_no_compens = 0

        # Inlet
        E_in = E_in_no + E_in_no_compens
        P_in = E_in / (dt / 60)

        # Inlet secondary
        E_in_sd1 = par.split_P_sd1 * E_in
        E_in_sd2 = par.split_P_sd2 * E_in

        P_in_sd1 = E_in_sd1 / (dt / 60)
        P_in_sd2 = E_in_sd2 / (dt / 60)

        # Loss
        E_loss = E_loss_no + E_loss_no_compens
        P_loss = E_loss / (dt / 60)

        E_heat = par.fact_P_heat_P_Loss * E_loss
        P_heat = par.fact_P_heat_P_Loss * P_loss

        return_dict = {"E_in_mc": 0,
                       "E_in": E_in,
                       "E_in_sd1": E_in_sd1,
                       "E_in_sd2": E_in_sd2,
                       "E_loss": E_loss,
                       "E_out": 0,
                       "E_heat": E_heat}

        if include_power:
            power_dict = {"P_in_mc": 0,
                          "P_in": P_in,
                          "P_in_sd1": P_in_sd1,
                          "P_in_sd2": P_in_sd2,
                          "P_loss": P_loss,
                          "P_out": 0,
                          "P_heat": P_heat}
            return_dict = return_dict | power_dict

        return return_dict

    def _calc_L_L_change(self,
                         P_out_rel_0,
                         P_out_rel_1,
                         dt,
                         eta_0,
                         eta_1,
                         eta_mc_0,
                         eta_mc_1,
                         include_power: bool):
        """

        :param P_out_rel_0:
        :param P_out_rel_1:
        :param dt:
        :param eta_0:
        :param eta_1:
        :param eta_mc_0:
        :param eta_mc_1:
        :param include_power:
        :return:
        """

        par = self.par

        # Load change
        # ------------
        E_loadchange = (par.E_in_loadchange_ip(P_out_rel_1) -
                        par.E_in_loadchange_ip(P_out_rel_0))
        E_in_sd_loadchange = max(0, E_loadchange)
        E_loss_loadchange = abs(min(0, E_loadchange))

        P_in_sd_loadchange = E_in_sd_loadchange / (dt / 60)
        P_loss_loadchange = E_loss_loadchange / (dt / 60)

        # Outlet
        P_out_0 = P_out_rel_0 * par.P_out_rated
        P_out_1 = P_out_rel_1 * par.P_out_rated
        E_out = (P_out_rel_0 + P_out_rel_1) / 2 * (dt / 60)

        # Inlet main conversion
        P_in_mc_1 = P_out_1 / eta_mc_1
        P_in_mc_0 = P_out_0 / eta_mc_0

        E_in_mc = (P_in_mc_0 + P_in_mc_1) / 2 * (dt / 60)

        # Inlet combined
        P_in_wo_lc_1 = P_out_1 / eta_1
        P_in_wo_lc_0 = P_out_0 / eta_0

        P_in = P_in_wo_lc_1 + P_in_sd_loadchange
        E_in_wo_lc = (P_in_wo_lc_1 + P_in_wo_lc_0) / 2 * (dt / 60)
        E_in = E_in_wo_lc + E_in_sd_loadchange

        # Inlet secondary
        E_in_sd = E_in - E_in_mc
        E_in_sd1 = par.split_P_sd1 * E_in_sd
        E_in_sd2 = par.split_P_sd2 * E_in_sd
        P_in_sd_wo_lc = P_in_wo_lc_1 - P_in_mc_1
        P_in_sd1 = par.split_P_sd1 * (P_in_sd_wo_lc + P_in_sd_loadchange)
        P_in_sd2 = par.split_P_sd2 * (P_in_sd_wo_lc + P_in_sd_loadchange)

        # Loss
        E_loss_wo_lc = E_in_wo_lc - E_out
        E_loss = E_loss_wo_lc + E_loss_loadchange
        P_loss_wo_lc = P_in_wo_lc_0 * (1 - eta_1)
        P_loss = P_loss_wo_lc + P_loss_loadchange

        E_heat = par.fact_P_heat_P_Loss * E_loss
        P_heat = par.fact_P_heat_P_Loss * P_loss

        return_dict = {"E_in_mc": E_in_mc,
                       "E_in": E_in,
                       "E_in_sd1": E_in_sd1,
                       "E_in_sd2": E_in_sd2,
                       "E_loss": E_loss,
                       "E_out": E_out,
                       "E_heat": E_heat}

        if include_power:
            power_dict = {"P_in_mc": P_in_mc_1,
                          "P_in": P_in,
                          "P_in_sd1": P_in_sd1,
                          "P_in_sd2": P_in_sd2,
                          "P_loss": P_loss,
                          "P_out": P_out_1,
                          "P_heat": P_heat}
            return_dict = return_dict | power_dict

        return return_dict

    def _calc_state_change(self,
                           P_out_rel_1,
                           heatup_1,
                           t_op,
                           eta_1,
                           eta_mc_1) -> dict:
        """
        Energy calculation from prior state  to new state P_out_rel_1
        Case distinction required:
         - noLoad operation -> noLoad operation [NL->NL]
         - load operation -> load operation [L->L]
         - load operation -> noLoad operation [L->NL]
         - noLoad operation -> load operation [NL->L]

        :return: state_1: dict
        """
        P_out_rel_0 = self.state.P_out / self.par.P_out_rated

        heatup_0 = self.state.heatup

        # noLoad operation -> noLoad operation [NL->NL]
        if (heatup_1 < 1) and (heatup_0 < 1):
            state_dict = self._calc_NL_NL_change(heatup_0=heatup_0,
                                                 heatup_1=heatup_1,
                                                 dt=self.ts,
                                                 include_power=True)

        # load operation -> load operation [L->L]
        elif (heatup_1 == 1) and (heatup_0 == 1):
            state_dict = self._calc_L_L_change(P_out_rel_0=P_out_rel_0,
                                               P_out_rel_1=P_out_rel_1,
                                               dt=self.ts,
                                               eta_0=self.state.eta,
                                               eta_1=eta_1,
                                               eta_mc_0=self.state.eta_mc,
                                               eta_mc_1=eta_mc_1,
                                               include_power=True)

        # load operation -> noLoad operation [L->NL]
        elif (heatup_0 == 1) and (heatup_1 < 1):
            if t_op > 0:
                state_dict_load = self._calc_L_L_change(
                    P_out_rel_0=P_out_rel_0,
                    P_out_rel_1=self.par.P_out_min_rel,
                    dt=t_op,
                    eta_0=self.state.eta,
                    eta_1=self.par.eta_ip_P_out_rel(self.par.P_out_min_rel),
                    eta_mc_0=self.state.eta_mc,
                    eta_mc_1=self.par.eta_mc_ip_P_out_rel(self.par.P_out_min_rel),
                    include_power=False)
            else:
                state_dict_load = dict()

            state_dict_noLoad = self._calc_NL_NL_change(heatup_0=1,
                                                        heatup_1=heatup_1,
                                                        dt=self.ts - t_op,
                                                        include_power=True)

            state_dict = {k: state_dict_load.get(k, 0) + state_dict_noLoad.get(k, 0) for k in
                          state_dict_load.keys() | state_dict_noLoad.keys()}

        # noLoad operation -> load operation [NL->L]
        elif (heatup_0 < 1) and (heatup_1 == 1):
            if self.ts - t_op > 0:
                state_dict_noLoad = self._calc_NL_NL_change(heatup_0=heatup_0,
                                                            heatup_1=1,
                                                            dt=self.ts - t_op,
                                                            include_power=False)
            else:
                state_dict_noLoad = dict()

            state_dict_load = self._calc_L_L_change(
                P_out_rel_0=self.par.P_out_min_rel,
                P_out_rel_1=P_out_rel_1,
                dt=t_op,
                eta_0=self.par.eta_ip_P_out_rel(self.par.P_out_min_rel),
                eta_1=eta_1,
                eta_mc_0=self.par.eta_mc_ip_P_out_rel(self.par.P_out_min_rel),
                eta_mc_1=eta_mc_1,
                include_power=True)

            state_dict = {k: state_dict_load.get(k, 0) + state_dict_noLoad.get(k, 0) for k in
                          state_dict_load.keys() | state_dict_noLoad.keys()}

        else:
            raise Exception("Error in state change.")

        # Bulk Energy
        # ----------------------------------------------------------------
        E_bulk_heatup = heatup_1 * self.par.E_start_bulk
        if heatup_1 ==1:
            E_bulk_op = self.par.E_in_loadchange_ip(P_out_rel_1)
        else:
            E_bulk_op = 0

        E_bulk = E_bulk_heatup + E_bulk_op

        dE_bulk_heatup = (heatup_1 - heatup_0) * self.par.E_start_bulk
        dE_bulk_loadchange = (
                self.par.E_in_loadchange_ip(max(self.par.P_out_min_rel, P_out_rel_1)) -
                self.par.E_in_loadchange_ip(max(self.par.P_out_min_rel, P_out_rel_0)))
        state_dict["E_bulk"] = E_bulk

        # Balances
        # ----------------------------------------------------------------
        tol = 1e-5
        sd = state_dict
        # Inlet energy check
        if abs(sd["E_in"] - (sd["E_in_mc"] + sd["E_in_sd1"] + sd["E_in_sd2"])) > tol:
            self.logger.warning(f"E_in deviation! Total: {sd['E_in']},"
                                f' splitted: {sd["E_in_mc"] + sd["E_in_sd1"] + sd["E_in_sd2"]}')

        # Inlet power check
        if abs(sd["P_in"] - (sd["P_in_mc"] + sd["P_in_sd1"] + sd["P_in_sd2"])) > tol:
            self.logger.warning(f"P_in deviation! Total: {sd['P_in']},"
                                f' splitted: {sd["P_in_mc"] + sd["P_in_sd1"] + sd["P_in_sd2"]}')

        E_balance = (sd["E_in"] - sd["E_out"] - sd["E_loss"]) - (
                dE_bulk_heatup + dE_bulk_loadchange)

        if abs(E_balance) > tol:
            self.logger.warning(f"Energy Balance deviation! {E_balance}")

        state_dict["E_balance"] = E_balance
        state_dict["heatup"]=heatup_1
        state_dict["eta"]=eta_1
        state_dict["eta_mc"] = eta_mc_1



        return state_dict

    def step_action_stationary(self,
                               contr_val: float,
                               max_iterations=100) -> None:
        """
        Performs step_action() until target "contr_val" is reached.
        Condition for stationary state:
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
        E_cond = False

        while not ((contr_val == self.state.P_out / self.par.P_out_rated) and E_cond) and (
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

    def get_P_out_for_P_in_mc_target(self, P_in_mc_target: float) -> float:
        """
        Calculation of contr_val for step_action()-method equivalent to
        given main conversion input load requirement [kW]

        Only usable for load operation!
        Returns error if P_in_mc_target < P_in_mc_target_min

        :param P_in_mc_target: float, Input load [kW]
        """

        if P_in_mc_target < self.par.P_in_mc_min:
            raise Exception("P_in_mc_target < self.par.P_in_mc_min")
        elif P_in_mc_target > self.par.P_in_mc_max:
            raise Exception("P_in_mc_target > self.par.P_in_mc_max")
        else:
            P_out_rel = (P_in_mc_target * self.par.eta_mc_ip_P_in_mc(P_in_mc_target) /
                         self.par.P_out_rated)

            return P_out_rel

    def get_P_in_mc_from_P_out(self, P_out_kW: float) -> float:
        """
        Calculation of main conversion input power [kW].
        Only to be used for load operation, throws error if below minimum output load

        :param P_out_kW:  Output load [kW]
        """

        # Check if P_in_mc_target is above required minimum
        if P_out_kW < self.par.P_out_min:
            raise Exception("P_out_kW < self.par.P_out_min")
        elif P_out_kW > self.par.P_out_rated:
            raise Exception("P_out_kW > self.par.P_out_rated")
        else:
            P_in_mc = P_out_kW / self.par.eta_mc_ip_P_out(P_out_kW)
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
    See /test for demonstration and examples
    """
    print("See /test for demonstration and examples")
