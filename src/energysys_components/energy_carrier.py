from dataclasses import dataclass
from pathlib import Path

import yaml


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


    @staticmethod
    def from_yaml(yaml_file_path: Path) ->dict[str,"ECarrier"]:
        """
        Returns one or multiple ECarriers objects from a yaml file.
        :param yaml_file_path:
        :return:
        """
        carriers = dict()
        if Path.is_file(yaml_file_path):
            with open(yaml_file_path, "r") as f:
                dictionary = yaml.safe_load(f)
                for k,v in dictionary.items():
                    carriers[k] = ECarrier(**v)
                return carriers

        else:
            raise FileNotFoundError(f"File {yaml_file_path} not found.")

if __name__ == "__main__":
    path = Path.cwd() / Path("energycarrier/energycarrier.yaml")
    ec_dict = ECarrier.from_yaml(path)