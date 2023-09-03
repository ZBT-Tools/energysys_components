from dataclasses import dataclass, field


@dataclass(frozen=True)
class ECarrier:
    """
    """
    name: str
    color: str


NH3 = ECarrier(name="Ammonia", color="#19a844")
H2 = ECarrier(name="Hydrogen", color="#1982a8")
Electr = ECarrier(name="Electricity", color="#ccb80e")
Loss = ECarrier(name="Loss", color="#cc470e")
