"""
Simple EnergyConversion()-Tests
"""

import pandas as pd
import plotly.graph_objects as go
import copy
from src.energysys_components.energy_conversion_classes import EConversionParams, EConversionState, EnergyConversion

# Example Definition
Cracker_fast = EConversionParams(P_out_rated=2000,
                                 P_out_min_pct=15,
                                 eta_pct=[
                                     [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85,
                                      90, 95, 100, 105, 110, 115, 120],
                                     [55, 56.43, 57.1, 57.37, 57.33, 57.08, 56.67, 56.12, 55.48,
                                      54.74, 53.93, 53.06, 52.14,
                                      51.18, 50.18, 49.16, 48.12, 47.07, 46.01, 44.94, 43.88,
                                      42.82]],
                                 p_change_pos=5,
                                 p_change_neg=5,
                                 t_preparation=30,
                                 W_preparation=250,
                                 t_cooldown=75,
                                 spec_invest_cost=100,
                                 spec_volume=0.0017,
                                 spec_mass=1,
                                 norm_limits=[0, 1],
                                 control_type_target=True)

off_state = EConversionState()
full_load_state = EConversionState(P_in=2000,
                                   heatup_pct=100)

if __name__ == "__main__":
    # Result DataFrame Initialization
    state_parms = [a for a in dir(EConversionState()) if not a.startswith('__')]
    df1 = pd.DataFrame(columns=state_parms)
    df1.loc[0] = vars(EConversionState())

    # Run different stationary cases for target output load
    targets = [0,
               0.5 * Cracker_fast.P_out_min_pct / 100,
               Cracker_fast.P_out_min_pct / 100,
               0.5,
               1]

    # number of time steps
    ts = 180

    for target in targets:
        # Initialization of component
        C1 = EnergyConversion(Cracker_fast, copy.deepcopy(off_state), ts=1)
        for t in range(ts):
            print(t)
            if t <= 90:
                C1.step_action(target)
            else:
                C1.step_action(0)
            df1.loc[t + 1] = vars(C1.state)

        # Create traces
        fig = go.Figure()
        for cl in df1.columns:
            fig.add_trace(go.Scatter(x=df1.index[1:], y=df1[cl][1:],

                                     mode='lines',
                                     name=cl))
            fig.update_layout(title=f"Target,rel: {target}")
        fig.show()