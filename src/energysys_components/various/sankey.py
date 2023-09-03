import plotly.graph_objects as go
import pandas as pd
from energysys_components.energy_carrier import H2, NH3, Loss, Electr


def sankey_input_single(res: pd.Series, comptype="PEM") -> (dict, dict):
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

    # Definition of flowtypes
    if comptype == "PEM":
        prop = dict(Source_mc=H2,
                    Source_sd1=H2,
                    Source_sd2=Electr,
                    Output=Electr,
                    Loss=Loss)
    elif comptype == "Cracker":
        prop = dict(Source_mc=NH3,
                    Source_sd1=NH3,
                    Source_sd2=Electr,
                    Output=H2,
                    Loss=Loss)
    elif comptype == "SOFC":
        prop = dict(Source_mc=NH3,
                    Source_sd1=NH3,
                    Source_sd2=Electr,
                    Output=Electr,
                    Loss=Loss)
    else:
        prop = dict(Source_mc=NH3,
                    Source_sd1=NH3,
                    Source_sd2=Electr,
                    Output=Electr,
                    Loss=Loss)

    # !!id key is just for information!
    node_def = [dict(label="Source_mc", color=prop["Source_mc"].color, id=0),
                dict(label="Source_sd1", color=prop["Source_sd1"].color, id=1),
                dict(label="Source_sd2", color=prop["Source_sd2"].color, id=2),
                dict(label="Comp", color="#9e9da1", id=3),
                dict(label="Output", color=prop["Output"].color, id=4),
                dict(label="Loss", color=prop["Loss"].color, id=5)]

    # Plotly node format
    node = dict(label=[dct["label"] for dct in node_def],
                color=[dct["color"] for dct in node_def])

    # Get index function
    def gx(label: str) -> int:
        return node["label"].index(label)

    # Flow  definition
    flow_def = [
        dict(label="Input main conversion",
             source=gx("Source_mc"),
             target=gx("Comp"),
             value=res.P_in_mc,
             color=prop["Source_mc"].color),

        dict(label="Input secondary 1",
             source=gx("Source_sd1"),
             target=gx("Comp"),
             value=res.P_in_sd1,
             color=prop["Source_sd1"].color),

        dict(label="Input secondary 2",
             source=gx("Source_sd2"),
             target=gx("Comp"),
             value=res.P_in_sd2,
             color=prop["Source_sd2"].color),

        dict(label="Loss",
             source=gx("Comp"),
             target=gx("Loss"),
             value=res.P_loss,
             color=prop["Loss"].color),

        dict(label="Output",
             source=gx("Comp"),
             target=gx("Output"),
             value=res.P_out,
             color=prop["Output"].color)
    ]

    # Plotly link format
    link = dict(label=[dct["label"] for dct in flow_def],
                color=[dct["color"] for dct in flow_def],
                source=[dct["source"] for dct in flow_def],
                target=[dct["target"] for dct in flow_def],
                value=[dct["value"] for dct in flow_def])

    return node, link


if __name__ == "__main__":
    # Dummy result data
    d = {'P_in_mc': 1070.597827,
         'P_in_sd1': 1070.597827,
         'P_in_sd2': 100,
         'P_out': 614.141414,
         'P_loss': 456.456413}
    data = pd.Series(data=d, index=['P_in_mc', 'P_in_sd1', 'P_in_sd2', "P_out", "P_loss"])

    # Create plotly formatted input
    data_node, data_link = sankey_input_single(data,comptype="Cracker")

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
        title_text="Simple component sankey diagram",
        font_size=10)
    fig.show()
