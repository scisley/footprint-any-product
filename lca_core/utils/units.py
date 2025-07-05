# Special LCA specific units for using the Pint library.
lca_units = [
    'kgCO2e = kilogram = kgCO2',
    'lbCO2e = pound = lbCO2',
    'gCO2e  = gram     = gCO2',
    'tCO2e  = tonne    = tonne_CO2e = tCO2',
    'vehicle_mile = mile',
    'passenger_mile = mile',
    'mmBtu = 1e6 * Btu',
    'scf = foot ** 3', # standard cubic foot 
    'CO2e = [] = CO2', # dimensionalless tag lets 'kg * CO2e' parse fine
]