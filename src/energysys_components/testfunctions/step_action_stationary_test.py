import pandas as pd
import plotly.graph_objects as go
import copy
import numpy as np
from src.energysys_components.energy_conversion import EConversionState, EnergyConversion
from src.energysys_components.component_definition import PEM, Cracker

# Select component
component = Cracker

off_state = EConversionState()
full_load_state = EConversionState(P_in=2000,
                                   heatup_pct=100)

if __name__ == "__main__":
    # Result DataFrame Initialization
    state_parms = [a for a in dir(EConversionState()) if not a.startswith('__')]
    df1 = pd.DataFrame(columns=state_parms)
    df1.loc[0] = vars(EConversionState())

    # Run different stationary cases for target output load
    targets = np.linspace(component.P_out_min_pct / 100, 1., 100)

    for ct, t in enumerate(targets):
        # Initialization of component
        C1_state = EConversionState()
        C1 = EnergyConversion(component, copy.deepcopy(C1_state), ts=1)
        C1.step_action_stationary(t)
        df1.loc[ct + 1] = vars(C1.state)

    # Create traces
    fig = go.Figure()

    # Create traces
    for cl in df1.columns:
        fig.add_trace(go.Scatter(x=df1.P_out[1:], y=df1[cl][1:],
                                 mode='lines',
                                 name=cl))
    fig.update_layout(xaxis_title="Output Load [kW]",
                      # yaxis_title="Y Axis Title",
                      )
    fig.update_layout(
        autosize=False,
        width=1400,
        height=1000)
    fig.show()
