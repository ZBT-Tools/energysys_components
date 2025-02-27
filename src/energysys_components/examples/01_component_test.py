"""
Simple EnergyConversionComponent()-Tests
"""

import pandas as pd
import plotly.graph_objects as go
import copy

from energysys_components.simulation import Simulation
from src.energysys_components.energy_conversion import ECCState, EnergyConversionComponent
from energysys_components.examples.example_component_definition import SOFC

if __name__ == "__main__":
    # Example Definition
    # ------------------
    component = SOFC
    # Load profile
    ts = 1
    n_ts = int(180 / ts)  # number of time steps
    targets = [0,
               0.5 * component.P_out_min_rel / 100,
               component.P_out_min_rel / 100,
               0.5,
               1]
    loadprofiles = []
    for targ in targets:
        lp = []
        for t in range(n_ts):
            if t <= n_ts / 2:
                lp.append(targ)
            else:
                lp.append(0)
        loadprofiles.append(lp)

    # Run simulations
    for lp in loadprofiles:

        sim = Simulation(component_parameter=component,
                         timestep=1,
                         loadprofile=lp)

        sim.run()

        # Plot results
        fig = go.Figure()
        for cl in sim.results.columns:
            fig.add_trace(go.Scatter(x=sim.results.index[:],
                                     y=sim.results[cl][:],
                                     mode='lines',
                                     name=cl))
            fig.update_layout(title=f"Target,rel: {sim.loadprofile[0]}")
        fig.show()
