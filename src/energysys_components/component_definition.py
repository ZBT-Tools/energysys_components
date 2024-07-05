"""
Component definition examples
"""

from energysys_components.energy_conversion import EConversionParams
from energysys_components.energy_carrier import NH3, H2, Electr
from energysys_components.energy_storage import StorageParams

# Ammonia Cracker
Cracker = EConversionParams(
    name="Example Ammonia Cracker",

    # Energy Carrier Definitions
    E_in_mc_type=NH3,
    E_in_sd1_type=NH3,
    E_in_sd2_type=Electr,
    E_out_type=H2,

    # Startup
    t_preparation=30,  # Time until system is available [Minutes] ("idle")
    E_preparation=200,  # Preparation Energy [kWh] (from cold to idle)
    eta_preparation=50,  # [%] For calculation of losses below operation
    # Load Operation
    P_out_min_pct=15,  # Minimum operating load [% Load]
    P_out_rated=2000,  # Rated Load [kW]

    p_change_pos=5,  # [% output load/min]
    p_change_neg=5,  # [% output load/min]
    E_loadchange=[[0, 100], [0, 0]],  # [[load [%]],[Energy [kWh]]]

    # Overall component efficiency
    eta_pct=[[15, 100], [75, 80]],  # load dependend efficiency  [[load [%]],[efficiency [%]]]
    # Main conversion path efficiency
    eta_mc_pct=[[15, 100], [0.8 * 100 * 0.178 * 33.3 / 5.2, 0.8 * 100 * 0.178 * 33.3 / 5.2]],
    # load
    # dependend efficiency  [[load [%]],[efficiency [%]]]

    # Shutdown
    t_cooldown=60,  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd=[0.95, 0.05],  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio,
    fact_P_Loss_P_heat=0,

    # Techno-economic
    spec_invest_cost=200,  # [€/kW]
    spec_volume=0.005,  # [m^^3/kW]
    spec_mass=1,  # [kg/kW]

    # Control Settins
    control_type_target=True,  # If true, input is load target
    norm_limits=[0, 1])

PEM = EConversionParams(
    name="Example PEM Fuel Cell",

    # Energy Carrier Definitions
    E_in_mc_type=H2,
    E_in_sd1_type=H2,
    E_in_sd2_type=Electr,
    E_out_type=Electr,

    # Startup
    t_preparation=5,  # Time until system is available [Minutes] ("idle")
    E_preparation=20,  # Preparation Energy [kWh] (from cold to idle)
    eta_preparation=50,  # [%] For calculation of losses below operation

    # Load Operation
    P_out_min_pct=15,  # Minimum operating load [% Load]
    P_out_rated=2000,  # Rated Load [kW]

    p_change_pos=20,  # [% output load/min]
    p_change_neg=20,  # [% output load/min]

    E_loadchange=[[0, 100], [0, 0]],  # [[load [%]],[Energy [kWh]]]

    # Overall component efficiency
    eta_pct=[[15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85,
              90, 95, 100, 105, 110, 115, 120],
             [55, 56.43, 57.1, 57.37, 57.33, 57.08, 56.67, 56.12, 55.48,
              54.74, 53.93, 53.06, 52.14,
              51.18, 50.18, 49.16, 48.12, 47.07, 46.01, 44.94, 43.88,
              42.82]],  # load dependend efficiency  [[load [%]],[efficiency [%]]]
    # Main conversion path efficiency
    eta_mc_pct=[[15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85,
                 90, 95, 100, 105, 110, 115, 120],
                [55, 56.43, 57.1, 57.37, 57.33, 57.08, 56.67, 56.12, 55.48,
                 54.74, 53.93, 53.06, 52.14,
                 51.18, 50.18, 49.16, 48.12, 47.07, 46.01, 44.94, 43.88,
                 42.82]],  # load
    # dependend efficiency  [[load [%]],[efficiency [%]]]

    # Shutdown
    t_cooldown=60,  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd=[0, 1],  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio
    fact_P_Loss_P_heat=0,

    # Techno-economic
    spec_invest_cost=200,  # [€/kW]
    spec_volume=0.005,  # [m^^3/kW]
    spec_mass=1,  # [kg/kW]

    # Control Settins
    control_type_target=True,  # If true, input is load target
    norm_limits=[0, 1])

Purification = EConversionParams(
    name="Example Hydrogen Purification",

    # Energy Carrier Definitions
    E_in_mc_type=H2,
    E_in_sd1_type=H2,
    E_in_sd2_type=Electr,
    E_out_type=H2,

    # Startup
    t_preparation=10,  # Time until system is available [Minutes] ("idle")
    E_preparation=10,  # Preparation Energy [kWh] (from cold to idle)
    eta_preparation=50,  # [%] For calculation of losses below operation
    # Load Operation
    P_out_min_pct=10,  # Minimum operating load [% Load]
    P_out_rated=2000,  # Rated Load [kW]

    p_change_pos=5,  # [% output load/min]
    p_change_neg=5,  # [% output load/min]
    E_loadchange=[[0, 100], [0, 0]],  # [[load [%]],[Energy [kWh]]]

    # Overall component efficiency
    eta_pct=[[15, 100], [90, 91]],  # load dependend efficiency  [[load [%]],[efficiency [%]]]
    # Main conversion path efficiency
    eta_mc_pct=[[15, 100], [90, 91]],  # load
    # dependend efficiency  [[load [%]],[efficiency [%]]]

    # Shutdown
    t_cooldown=30,  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd=[0.95, 0.05],  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio
    fact_P_Loss_P_heat=0,

    # Techno-economic
    spec_invest_cost=200,  # [€/kW]
    spec_volume=0.005,  # [m^^3/kW]
    spec_mass=1,  # [kg/kW]

    # Control Settins
    control_type_target=True,  # If true, input is load target
    norm_limits=[0, 1])

SOFC = EConversionParams(
    name="Example Solid Oxide Fuel Cell",

    # Energy Carrier Definitions
    E_in_mc_type=NH3,
    E_in_sd1_type=NH3,
    E_in_sd2_type=Electr,
    E_out_type=Electr,

    # Startup
    t_preparation=10,  # Time until system is available [Minutes] ("idle")
    E_preparation=10,  # Preparation Energy [kWh] (from cold to idle)
    eta_preparation=50,  # [%] For calculation of losses below operation
    # Load Operation
    P_out_min_pct=15,  # Minimum operating load [% Load]
    P_out_rated=2000,  # Rated Load [kW]

    p_change_pos=5,  # [% output load/min]
    p_change_neg=5,  # [% output load/min]

    # Overall component efficiency
    eta_pct=[[15, 100], [90, 91]],  # load dependend efficiency  [[load [%]],[efficiency [%]]]
    # Main conversion path efficiency
    eta_mc_pct=[[15, 100], [90, 91]],  # load
    # dependend efficiency  [[load [%]],[efficiency [%]]]
    E_loadchange=[[0, 15, 100], [0, 0, 20]],  # [[load [%]],[Energy [kWh]]]

    # Shutdown
    t_cooldown=10,  # Time until system cooled down [Minutes] ("idle to cool")

    # Secondary energy ratios
    # 1: input flow, 2: electric
    split_P_sd=[0.95, 0.05],  # split of secondary energies, eg. [0.2,0.8] for 2:8 ratio
    fact_P_Loss_P_heat=0,

    # Techno-economic
    spec_invest_cost=200,  # [€/kW]
    spec_volume=0.005,  # [m^^3/kW]
    spec_mass=1,  # [kg/kW]

    # Control Settins
    control_type_target=True,  # If true, input is load target
    norm_limits=[0, 1])

Battery = StorageParams(E_cap=1,
                        E_out_type=Electr,
                        E_in_sd1_type=Electr,
                        E_in_sd2_type=Electr,
                        E_in_mc_type=Electr,
                        spec_mass=1,
                        spec_volume=1,
                        autoIncrease=True,
                        C_rate_charge=1,
                        spec_invest_cost=1,
                        eta=0.8,
                        name="Battery Test",
                        )
