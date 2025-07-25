"""
Simple EnergyConversionComponent()-Tests
"""

import plotly.graph_objects as go
from energysys_components.simulation import Simulation
from energysys_components.examples.example_component_definition import SOFC

if __name__ == "__main__":
    component = SOFC
    timestep_s = 1

    # Load profile
    n_ts = int(180 / timestep_s)  # number of time steps

    targets = [0,
               0.5 * component.P_out_min_rel,
               component.P_out_min_rel,
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
                         timestep=timestep_s,
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
