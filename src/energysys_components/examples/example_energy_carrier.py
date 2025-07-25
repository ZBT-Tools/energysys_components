from energysys_components.energy_carrier import ECarrier

NH3 = ECarrier(
    # https://www.peacesoftware.de/einigewerte/nh3.html
    # Agg. Gas, p 1bar, T 20degC, 1536 	[kJ/kg]
    # Agg. Liq, p 1bar, T -33degC, 46 [kJ/kg]

    name="Ammonia",
    color="#19a844",
    hu_kWh_kg=5.2,
    density_liq_kg_m3=682.78,
    energy_density_liq_kWh_m3=5.2 * 682.78)

H2 = ECarrier(
    name="Hydrogen",
    color="#1982a8",
    hu_kWh_kg=33.33,
    density_liq_kg_m3=70.79,  # -253,15°C
    energy_density_liq_kWh_m3=33.33 * 70.79)

LNG = ECarrier(
    # https://totalenergies.de/sites/g/files/wompnd2336/f/atoms/files/
    # lng_fluessiges_erdgas_pdf_produktbroschuere.pdf

    name="LNG",
    color="#1982a8",
    hu_kWh_kg=13.98,

    density_liq_kg_m3=450,  # @ -161 °C
    energy_density_liq_kWh_m3=13.98 * 450)

Electr = ECarrier(
    name="Electricity",
    color="#ccb80e",
    hu_kWh_kg=0,
    density_liq_kg_m3=0,
    energy_density_liq_kWh_m3=0)

Loss = ECarrier(
    name="Loss", color="#cc470e",
    hu_kWh_kg=0,
    density_liq_kg_m3=0,
    energy_density_liq_kWh_m3=0)

Seawater = ECarrier(
    name="Seawater",
    color="#0e8acc",
    hu_kWh_kg=0,
    density_liq_kg_m3=999,  # -253,15°C
    energy_density_liq_kWh_m3=0)
