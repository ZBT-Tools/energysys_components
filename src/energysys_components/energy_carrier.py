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


NH3 = ECarrier(name="Ammonia", color="#19a844",
               hu_kWh_kg=5.2,
               density_liquid_cool=682.78,
               vol_energy_density_kWh_m3=5.2 * 682.78)

H2 = ECarrier(name="Hydrogen", color="#1982a8",
              hu_kWh_kg=33.33,
              density_liquid_cool=70.79,  # -253,15°C
              vol_energy_density_kWh_m3=5.2 * 682.78)

Electr = ECarrier(name="Electricity", color="#ccb80e",
                  hu_kWh_kg=0,
                  density_liquid_cool=0,  # -253,15°C
                  vol_energy_density_kWh_m3=0)
Loss = ECarrier(name="Loss", color="#cc470e",
                hu_kWh_kg=0,
                density_liquid_cool=0,  # -253,15°C
                vol_energy_density_kWh_m3=0)
