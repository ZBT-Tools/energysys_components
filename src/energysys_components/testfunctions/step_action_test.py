"""
Simple EnergyConversion()-Tests
"""

import pandas as pd
import plotly.graph_objects as go
import copy
from src.energysys_components.energy_conversion import EConversionState, EnergyConversion
from src.energysys_components.component_definition import PEM, Cracker

# Example Definition
component = PEM
# component = Cracker

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
               0.5 * component.P_out_min_pct / 100,
               component.P_out_min_pct / 100,
               0.5,
               1
               ]

    # number of time steps
    ts = 180

    for target in targets:
        # Initialization of component
        C1 = EnergyConversion(component, copy.deepcopy(off_state), ts=1)
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
