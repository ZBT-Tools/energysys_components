"""
Functions for generation of component Sankey diagram
"""

import plotly.graph_objects as go
import pandas as pd
from energysys_components.examples.component_definition import PEM
from energysys_components.examples.energy_carrier import Loss
from energysys_components.energy_conversion import ECCParameter


def sankey_component_input_dicts(res: pd.Series, comp: ECCParameter) -> (dict, dict):
    """
    Creates input dicts for plotly dash sankey diagram

    "node"-dict with keys:
        color:  list,   colors for each
        label:  list,   the shown name of the node

    "link"-dict with keys:
        color:  list,   colors for each link
        label:  list,   the shown name of the link
        source: list,   an integer number `[0..nodes.length - 1]` that represents the source node
        target: list,   as source
        value:  list,   flow value

    :return: "node" and  "link"-dict
    """

    # !!id key is just for information!
    node_def = [dict(label=f"Source_mc",
                     color=comp.E_in_mc_type.color, id=0),
                dict(label=f"Source_sd1",
                     color=comp.E_in_sd1_type.color, id=1),
                dict(label=f"Source_sd2",
                     color=comp.E_in_sd2_type.color, id=2),
                dict(label="Comp", color="#9e9da1", id=3),
                dict(label=f"Output",
                     color=comp.E_out_type.color, id=4),
                dict(label="Loss", color=Loss.color, id=5)]

    # Plotly node format
    node = dict(label=[dct["label"] for dct in node_def],
                color=[dct["color"] for dct in node_def])

    # Get index function
    def gx(label: str) -> int:
        return node["label"].index(label)

    # Flow  definitions
    flow_def = [
        dict(label=f"Input main conversion: {comp.E_in_mc_type.name}",
             source=gx("Source_mc"),
             target=gx("Comp"),
             value=res.P_in_mc,
             color=comp.E_in_mc_type.color),

        dict(label=f"Input secondary 1: {comp.E_in_sd1_type.name}",
             source=gx("Source_sd1"),
             target=gx("Comp"),
             value=res.P_in_sd1,
             color=comp.E_in_sd1_type.color),

        dict(label=f"Input secondary 2: {comp.E_in_sd2_type.name}",
             source=gx("Source_sd2"),
             target=gx("Comp"),
             value=res.P_in_sd2,
             color=comp.E_in_sd2_type.color),

        dict(label="Loss",
             source=gx("Comp"),
             target=gx("Loss"),
             value=res.P_loss,
             color=Loss.color),

        dict(label=f"Output {comp.E_out_type.name}",
             source=gx("Comp"),
             target=gx("Output"),
             value=res.P_out,
             color=comp.E_out_type.color)]

    # Plotly link format
    link = dict(label=[dct["label"] for dct in flow_def],
                color=[dct["color"] for dct in flow_def],
                source=[dct["source"] for dct in flow_def],
                target=[dct["target"] for dct in flow_def],
                value=[dct["value"] for dct in flow_def])

    return node, link


if __name__ == "__main__":
    # Create dummy results
    component = PEM

    # Dummy result data
    d = {'P_in_mc': 1070.597827,
         'P_in_sd1': 1070.597827,
         'P_in_sd2': 100,
         'P_out': 614.141414,
         'P_loss': 456.456413}
    data = pd.Series(data=d, index=['P_in_mc', 'P_in_sd1', 'P_in_sd2', "P_out", "P_loss"])

    # Create plotly formatted input
    data_node, data_link = sankey_component_input_dicts(data, comp=PEM)

    fig = go.Figure(data=[go.Sankey(
        valueformat=".0f",
        valuesuffix="kW",
        # Define nodes
        node=dict(
            pad=15,
            thickness=40,
            line=dict(color="black", width=0.5),
            label=data_node['label'],
            color=data_node['color']),
        link=data_link)])

    fig.update_layout(
        title_text=f"Simple component sankey diagram of {component.name}",
        font_size=10)
    fig.show()
