import pandas as pd
import plotly.graph_objects as go
import copy
import numpy as np
from src.energysys_components.energy_conversion import ECCState, EnergyConversionComponent
from energysys_components.examples.component_definition import PEM, SOFC

# Select component
component = PEM

off_state = ECCState()

if __name__ == "__main__":
    # Result DataFrame Initialization
    state_parms = [a for a in dir(ECCState()) if not a.startswith('__')]
    df1 = pd.DataFrame(columns=state_parms)
    df1.loc[0] = vars(ECCState())

    # Run different stationary cases for target output load
    targets = np.linspace(0, 1., 100)

    for ct, t in enumerate(targets):
        # Initialization of component
        print("ct", ct)
        C1_state = ECCState()
        C1 = EnergyConversionComponent(par=component,
                                       ts=1,
                                       state=copy.deepcopy(C1_state))
        C1.step_action_stationary(t)
        df1.loc[ct + 1] = vars(C1.state)
        df1.loc[ct + 1, "Target"] = t

    # Create traces
    fig = go.Figure()

    # Create traces
    for cl in df1.columns:
        fig.add_trace(go.Scatter(x=df1.Target[1:], y=df1[cl][1:],
                                 mode='lines',
                                 name=cl))
    fig.update_layout(xaxis_title="Target rel. output load [-]",
                      # yaxis_title="Y Axis Title",
                      )
    fig.update_layout(
        autosize=False,
        width=1400,
        height=1000)
    fig.show()
