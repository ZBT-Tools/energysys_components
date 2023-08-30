import plotly.graph_objects as go
import pandas as pd


def sankey_input_single(res: pd.Series) -> (dict, dict):
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

    # Node definition
    # !!id key is just for information!
    node_def = [dict(label="Source", color="rgba(0,0,0,0)", id=0),
                dict(label="Start Source", color="rgba(0,0,0,0)", id=1),
                dict(label="Comp", color="#9e9da1", id=2),
                dict(label="Output", color="rgba(0,0,0,0)", id=3),
                dict(label="Loss", color="rgba(255,255,255,0)", id=4)]

    # Plotly node format
    node = dict(label=[dct["label"] for dct in node_def],
                color=[dct["color"] for dct in node_def])

    def gx(label: str) -> int:
        return node["label"].index(label)

    # Flow  definition
    flow_def = [
        dict(label="Input", source=gx("Source"), target=gx("Comp"), value=res.P_in_op, color="#3ec757"),
        dict(label="Input Start", source=gx("Start Source"), target=gx("Comp"), value=res.P_in_hp,
             color="#3ec757"),
        dict(label="Loss", source=gx("Comp"), target=gx("Loss"), value=res.P_loss, color="#c75e3e"),
        dict(label="Output", source=gx("Comp"), target=gx("Output"), value=res.P_out, color="#3e9ec7")
    ]

    # Plotly link format
    link = dict(label=[dct["label"] for dct in flow_def],
                color=[dct["color"] for dct in flow_def],
                source=[dct["source"] for dct in flow_def],
                target=[dct["target"] for dct in flow_def],
                value=[dct["value"] for dct in flow_def])

    return node, link


if __name__ == "__main__":
    # Contruct dummy result data
    d = {'P_in': 1070.597827, 'P_out': 614.141414, 'P_loss': 456.456413}
    data = pd.Series(data=d, index=['P_in', 'P_out', 'P_loss'])

    # Create plotly formatted input
    data_node, data_link = sankey_input_single(data)

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
