from dataclasses import dataclass


@dataclass(frozen=True)
class ECarrier:
    """
    Idea: add techno-economic properties as fuel costs etc.
    Idea: Restructure instead of dummy values for input
    """
    name: str
    hu_kWh_kg: float  # Lower heating value [kWh/kg]
    density_liquid_cool: float  # density in cooled liquid state at ambient pressure [kg/m³]
    vol_energy_density_kWh_m3: float  # Volumetric energy density in liquid state [kWh/m³]
    color: str

    def tolist(self):
        """
        Required for encoding for plotly table function
         [https://plotly.com/python/table/#basic-table]

        :return:
        """
        return self.name


NH3 = ECarrier(
    # https://www.peacesoftware.de/einigewerte/nh3.html
    # Agg. Gas, p 1bar, T 20degC, 1536 	[kJ/kg]
    # Agg. Liq, p 1bar, T -33degC, 46 [kJ/kg]

    name="Ammonia", color="#19a844",
    hu_kWh_kg=5.2,
    density_liquid_cool=682.78,
    vol_energy_density_kWh_m3=5.2 * 682.78)

H2 = ECarrier(name="Hydrogen", color="#1982a8",
              hu_kWh_kg=33.33,
              density_liquid_cool=70.79,  # -253,15°C
              vol_energy_density_kWh_m3=33.33 * 70.79)  # Volumetric energy density in liquid state [kWh/m³]

LNG = ECarrier(name="LNG", color="#1982a8",
               hu_kWh_kg=13.98,
               #kWh/kg https://totalenergies.de/sites/g/files/wompnd2336/f/atoms/files/lng_fluessiges_erdgas_pdf_produktbroschuere.pdf
               density_liquid_cool=450,  # -161 °C
               vol_energy_density_kWh_m3=13.98 * 450)  # Volumetric energy density in liquid state [kWh/m³]

Electr = ECarrier(name="Electricity", color="#ccb80e",
                  hu_kWh_kg=0,
                  density_liquid_cool=0,
                  vol_energy_density_kWh_m3=0)
Loss = ECarrier(name="Loss", color="#cc470e",
                hu_kWh_kg=0,
                density_liquid_cool=0,
                vol_energy_density_kWh_m3=0)

Seawater = ECarrier(
    # cp: 	4,18 kJ/kg/K
    name="Seawater", color="#0e8acc",
    hu_kWh_kg=0,
    density_liquid_cool=999,  # -253,15°C
    vol_energy_density_kWh_m3=0)
