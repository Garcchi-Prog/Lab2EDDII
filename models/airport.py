class Airport:
    """
    Representa un aeropuerto con su información geográfica e identificadora.
    """
    def __init__(self, code, name, city, country, lat, lon):
        self.code    = code
        self.name    = name
        self.city    = city
        self.country = country
        self.lat     = float(lat)
        self.lon     = float(lon)

    def __repr__(self):
        return f"{self.code} ({self.city}, {self.country})"
