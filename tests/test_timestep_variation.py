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
from cProfile import Profile
from pstats import SortKey, Stats

if __name__ == "__main__":
    path_ecarrier = Path.cwd().parent / Path("src/energysys_components/energycarrier/energycarrier.yaml")
    ec_dict = ECarrier.from_yaml(path_ecarrier)
    components = ECCParameter.from_yaml(Path.cwd().parent / Path("src/energysys_components/components/fuel_cell_SOFC.yaml"), ecarrier=ec_dict)
    component = components["SOFC"]

    list_timestep_s = [0.5,1,2,5,10,20,30,60]

    # Load profile


    target = 1
        # [0,
        #        0.5 * component.P_out_min_rel,
        #        component.P_out_min_rel,
        #        0.5,
        #        1]
    loadprofiles = []


    for timestep_s in list_timestep_s:
        n_ts = int(7200/ timestep_s)  # number of time steps
        lp = []
        for t in range(n_ts):
            if t <= n_ts / 2:
                lp.append(target)
            else:
                lp.append(0)
        loadprofiles.append(lp)

    # with Profile() as profile:
    #     for lp in loadprofiles:
    #         sim = Simulation(component_parameter=component,
    #                          timestep_s=timestep_s,
    #                          loadprofile=lp)
    #         sim.run()
    #     (Stats(profile)
    #      .strip_dirs()
    #      .sort_stats(SortKey.CALLS)
    #      .print_stats()
    #      )

    # Run simulations
    fig = go.Figure()
    for lp,ts in zip(loadprofiles,list_timestep_s):



        sim = Simulation(component_parameter=component,
                         timestep_s=ts,
                         loadprofile=lp)

        sim.run()

        # Plot results

        for cl in sim.results.columns:
            fig.add_trace(go.Scatter(x=sim.results.time_s[:],
                                     y=sim.results[cl][:],
                                     mode='lines',
                                     legendgroup=str(cl),
                                     name=f"{cl}, {ts}s"))

    fig.update_layout(title=f"Target,rel: {sim.loadprofile[0]}",
                      xaxis_title="Time (s)"
                      )
    fig.show()
