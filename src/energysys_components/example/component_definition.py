"""
Energy Conversion Component (ECC) and Energy Storage Component (ESC) definition examples
"""
from energysys_components.energy_conversion import ECCParameter
from energysys_components.example.energy_carrier import NH3, H2, Electr, Loss
from energysys_components.energy_storage import ESCParameter

# Ammonia Cracker
Cracker = ECCParameter(
    name="Example Ammonia Cracker",

    # Energy Carrier Definitions
    E_in_mc_type=NH3,
    E_in_sd1_type=NH3,
    E_in_sd2_type=Electr,
    E_out_type=H2,

    # Startup
    t_start=30,
    E_start=200,
    eta_start=.5,
    # Load Operation
    P_out_min_rel=0.15,  # Minimum operating load [% Load]
    P_out_rated=2000,  # Rated Load [kW]

    p_change_pos=5,  # [% output load/min]
    p_change_neg=5,  # [% output load/min]
    E_loadchange=[[0, 1], [0, 0]],  # [[load [-]],[Energy [kWh]]]

    # Overall component efficiency
    eta=[[.15, 1], [.75, .80]],
    eta_mc=[[.15, 1], [0.8 * 0.178 * 33.3 / 5.2, 0.8 * 0.178 * 33.3 / 5.2]],

    # Shutdown
    t_cooldown=60,

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd=[0.95, 0.05],  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio,
    fact_P_heat_P_Loss=0,

    # Techno-economic
    spec_invest_cost=200,  # [€/kW]
    spec_volume=0.005,  # [m^^3/kW]
    spec_mass=1)  # [kg/kW]

PEM = ECCParameter(
    name="Example PEM Fuel Cell",

    # Energy Carrier Definitions
    E_in_mc_type=H2,
    E_in_sd1_type=H2,
    E_in_sd2_type=Electr,
    E_out_type=Electr,

    # Startup
    t_start=5,
    E_start=20,
    eta_start=.50,

    # Load Operation
    P_out_min_rel=.15,
    P_out_rated=2000,  # Rated Load [kW]

    p_change_pos=20,  # [% output load/min]
    p_change_neg=20,  # [% output load/min]

    E_loadchange=[[0, 1.00], [0, 0]],  # [[load [%]],[Energy [kWh]]]

    # Overall component efficiency
    eta=[[.15, .20, .25, .30, .35, .40, .45, .50, .55, .60, .65, .70, .75, .80, .85,
          .90, .95, 1.00, 1.05, 1.10, 1.15, 1.20],
         [.55, .5643, .571, .5737, .5733, .5708, .5667, .5612, .5548,
          .5474, .5393, .5306, .5214,
          .5118, .5018, .4916, .4812, .4707, .4601, .4494, .4388,
          .4282]],
    # Main conversion path efficiency
    eta_mc=[[.15, .20, .25, .30, .35, .40, .45, .50, .55, .60, .65, .70, .75, .80, .85,
             .90, .95, 1.00, 1.05, 1.10, 1.15, 1.20],
            [.55, .5643, .571, .5737, .5733, .5708, .5667, .5612, .5548,
             .5474, .5393, .5306, .5214,
             .5118, .5018, .4916, .4812, .4707, .4601, .4494, .4388,
             .4282]],

    # Shutdown
    t_cooldown=60,  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd=[0, 1],  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio
    fact_P_heat_P_Loss=0,

    # Techno-economic
    spec_invest_cost=200,  # [€/kW]
    spec_volume=0.005,  # [m^^3/kW]
    spec_mass=1,  # [kg/kW]
)

Purification = ECCParameter(
    name="Example Hydrogen Purification",

    # Energy Carrier Definitions
    E_in_mc_type=H2,
    E_in_sd1_type=H2,
    E_in_sd2_type=Electr,
    E_out_type=H2,

    # Startup
    t_start=10,
    E_start=10,
    eta_start=.50,
    # Load Operation
    P_out_min_rel=.10,
    P_out_rated=2000,

    p_change_pos=5,  # [% output load/min]
    p_change_neg=5,  # [% output load/min]
    E_loadchange=[[0, 1.00], [0, 0]],  # [[load [%]],[Energy [kWh]]]

    # Overall component efficiency
    eta=[[.15, 1], [.90, .91]],  # load dependend efficiency
    # Main conversion path efficiency
    eta_mc=[[.15, 1], [.90, .91]],  # load

    # Shutdown
    t_cooldown=30,  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd=[0.95, 0.05],  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio
    fact_P_heat_P_Loss=0,

    # Techno-economic
    spec_invest_cost=200,  # [€/kW]
    spec_volume=0.005,  # [m^^3/kW]
    spec_mass=1,  # [kg/kW]
)

SOFC = ECCParameter(
    name="Example Solid Oxide Fuel Cell",

    # Energy Carrier Definitions
    E_in_mc_type=NH3,
    E_in_sd1_type=NH3,
    E_in_sd2_type=Electr,
    E_out_type=Electr,

    # Startup
    t_start=10,
    E_start=10,
    eta_start=.50,
    # Load Operation
    P_out_min_rel=.15,
    P_out_rated=2000,

    p_change_pos=5,
    p_change_neg=5,

    eta=[[.15, 1.00], [.90, .91]],
    eta_mc=[[.15, 1.00], [.90, .91]],
    E_loadchange=[[0, .15, 1.00], [0, 0, 20]],

    # Shutdown
    t_cooldown=10,  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd=[0.95, 0.05],  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio
    fact_P_heat_P_Loss=1,

    # Techno-economic
    spec_invest_cost=200,  # [€/kW]
    spec_volume=0.005,  # [m^^3/kW]
    spec_mass=1,  # [kg/kW]
)

Boiler = ECCParameter(
    name="Boiler for Heat Generation",

    # Energy Carrier Definitions
    E_in_mc_type=NH3,
    E_in_sd1_type=NH3,
    E_in_sd2_type=Electr,
    E_out_type=Loss,  # inhere arbitrary as E_out is 100% "Loss"

    # Startup
    t_start=1,  # Time until system is available [Minutes] ("idle")
    E_start=1,  # Preparation Energy [kWh] (from cold to idle)
    eta_start=0.5,  #
    # Load Operation
    P_out_min_rel=.10,  # Minimum operating load [% Load]
    P_out_rated=2000,  # Rated Load [kW]

    p_change_pos=100,  # [% output load/min]
    p_change_neg=100,  # [% output load/min]

    # Overall component efficiency
    # Note: For Heat Generation Boiler
    eta=[[.15, 1.00], [.85, .85]],  # load dependend efficiency  [[load [%]],[efficiency [%]]]
    # Main conversion path efficiency
    eta_mc=[[.15, 1.00], [.85, .85]],  # load
    E_loadchange=[[0, .15, 1.00], [0, 0, 0]],

    # Shutdown
    t_cooldown=1,  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    # here arbitrary:
    split_P_sd=[0.95, 0.05],  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio
    fact_P_heat_P_Loss=0,

    # Techno-economic
    spec_invest_cost=200,  # [€/kW]
    spec_volume=0.005,  # [m^^3/kW]
    spec_mass=1,  # [kg/kW]
)

Battery = ESCParameter(E_cap=1,
                       E_out_type=Electr,
                       E_in_sd1_type=Electr,
                       E_in_sd2_type=Electr,
                       E_in_mc_type=Electr,
                       spec_mass=1,
                       spec_volume=1,
                       autoIncrease=True,
                       C_rate=1,
                       spec_invest_cost=1,
                       eta=0.8,
                       name="Battery Test",
                       )
