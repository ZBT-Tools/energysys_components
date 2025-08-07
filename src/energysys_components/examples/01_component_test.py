"""
Simple EnergyConversionComponent()-Tests
"""
from pathlib import Path

import plotly.graph_objects as go
from energysys_components.energy_carrier import ECarrier
from energysys_components.energy_conversion import ECCParameter
from energysys_components.simulation import Simulation
import plotly.io as pio
pio.renderers.default = "browser"

if __name__ == "__main__":
    path_ecarrier = Path.cwd().parent / Path("energycarrier/energycarrier.yaml")
    ec_dict = ECarrier.from_yaml(path_ecarrier)

    components = ECCParameter.from_yaml(Path.cwd() / Path("../components/fuel_cell_SOFC.yaml"), ecarrier=ec_dict)
    component = components["SOFC"]

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
