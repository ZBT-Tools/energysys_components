from dataclasses import dataclass

@dataclass(frozen=True)
class ECarrier:
    """
    Idea: add techno-economic properties as fuel costs etc.
    Idea: Restructure instead of dummy values for input
    """
    name: str
    hu_kWh_kg: float  # Lower heating value [kWh/kg]
    density_liq_kg_m3: float  # density in cooled liquid state at ambient pressure [kg/m³]
    energy_density_liq_kWh_m3: float  # Volumetric energy density in liquid state [kWh/m³]
    color: str  # Hexcode, examples: "#1982a8", is used for Sankey-Diagrams,...

    def tolist(self):
        """
        Required for encoding for plotly table function
         [https://plotly.com/python/table/#basic-table]
        """
        return self.name
