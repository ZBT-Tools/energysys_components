"""
Simple EnergyConversionComponent()-Tests
"""

import pandas as pd
import plotly.graph_objects as go
import copy
from src.energysys_components.energy_conversion import ECCState, EnergyConversionComponent
from energysys_components.example.component_definition import SOFC

# Example Definition
component = SOFC

off_state = ECCState()
full_load_state = ECCState(P_in=2000,
                           heatup=1)

if __name__ == "__main__":
    # Result DataFrame Initialization
    state_attr = [a for a in dir(ECCState()) if not a.startswith('__')]
    df1 = pd.DataFrame(columns=state_attr)
    # Initial state
    df1.loc[0] = vars(ECCState())

    # Run different stationary cases for target output load
    targets = [#0,
               #0.5 * component.P_out_min_rel / 100,
               #component.P_out_min_rel / 100,
               #0.5,
               1
               ]

    ts = 1 # min
    # number of time steps
    n_ts = int(180/ts)

    for target in targets:
        # Initialization of component
        C1 = EnergyConversionComponent(par=component,
                                       ts=ts,
                                       state=copy.deepcopy(off_state))
        for t in range(n_ts):
            print(t)
            if t <= n_ts/2:
                C1.step_action(target)
            else:
                C1.step_action(0)
            df1.loc[t + 1] = vars(C1.state)

        # Create traces
        fig = go.Figure()
        for cl in df1.columns:
            fig.add_trace(go.Scatter(x=df1.index[:], y=df1[cl][:],
                                     mode='lines',
                                     name=cl))
            fig.update_layout(title=f"Target,rel: {target}")
        fig.show()
