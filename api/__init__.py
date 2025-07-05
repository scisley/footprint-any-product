from pint import UnitRegistry, set_application_registry
from api.units import lca_units

ureg = UnitRegistry()
set_application_registry(ureg)

for unit in lca_units:
    ureg.define(unit)

Q_ = ureg.Quantity