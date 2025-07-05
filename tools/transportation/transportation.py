import json
import hashlib
import time
import pycountry
import searoute
from api import Q_
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import List, Optional, Dict, Any, Tuple, Literal
from pathlib import Path
from tools.emissions_factors.emissions_factors import emissions_factor_finder_tool
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Create cache directory for geocoding
CACHE_DIR = Path("cache/geocoding")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Global rate limiting for Nominatim API
_last_nominatim_call = 0

# Transport mode circuity factors (using 1.2 for all for now, but structured for future)
CIRCUITY_FACTORS = {
    "rail": 1.2,
    "truck": 1.2,
    "air": 1.0,  # Air routes are typically direct
    "ocean_freight": 1.0,  # Ocean routes calculated via searoute
}

class City(BaseModel):
    name: str = Field(description="English name of the city")
    country_code: str = Field(description="ISO 3166-1 alpha-2 country code")
    state_province: Optional[str] = Field(description="State, province, or region name/code (e.g., 'California', 'Ontario', 'NSW')", default=None)
    lat: float = Field(description="Latitude of the city center in decimal degrees")
    lon: float = Field(description="Longitude of the city center in decimal degrees")

class TransportationRoute(BaseModel):
    origin: City = Field(description="Origin city")
    destination: City = Field(description="Destination city")
    base_mode: Literal["ocean_freight", "rail", "truck", "air"] = Field(description="Base transportation mode for routing logic")
    mode: str = Field(description="Detailed transportation mode for emission factors (e.g., 'container ship', 'freight train', 'long-haul truck', 'cargo aircraft')")

class TransportationPlan(BaseModel):
    routes: List[TransportationRoute] = Field(description="List of origin-destination pairs with transportation modes")

class TransportationRouteAnalysis(BaseModel):
    origin: City
    destination: City
    base_mode: Literal["ocean_freight", "rail", "truck", "air"]
    mode: str
    distance_km: float
    carbon_emissions_kg_co2e: float
    geocoding_method: str  # "nominatim" or "llm_fallback"
    notes: Optional[str] = None

class TransportationAnalysisResult(BaseModel):
    total_distance_km: float
    total_carbon_emissions_kg_co2e: float
    route_details: List[TransportationRouteAnalysis]
    summary: str

def validate_iso_country_code(country_code: str) -> bool:
    """Validate ISO 3166-1 alpha-2 country code"""
    return pycountry.countries.get(alpha_2=country_code.upper()) is not None

def get_cache_key(city: str, country_code: str, state_province: Optional[str] = None) -> str:
    """Generate cache key for geocoding results"""
    key_parts = [city.lower(), country_code.upper()]
    if state_province:
        key_parts.append(state_province.lower())
    return hashlib.md5("_".join(key_parts).encode()).hexdigest()

def get_cached_coordinates(city: str, country_code: str, state_province: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """Get cached coordinates if available"""
    cache_key = get_cache_key(city, country_code, state_province)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return (data['lat'], data['lon'])
        except (json.JSONDecodeError, KeyError):
            pass
    return None

def cache_coordinates(city: str, country_code: str, lat: float, lon: float, state_province: Optional[str] = None):
    """Cache coordinates for future use"""
    cache_key = get_cache_key(city, country_code, state_province)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    data = {
        'city': city,
        'country_code': country_code,
        'state_province': state_province,
        'lat': lat,
        'lon': lon,
        'timestamp': time.time()
    }
    
    with open(cache_file, 'w') as f:
        json.dump(data, f)

def wait_for_rate_limit():
    """Ensure 2-second gap between Nominatim API calls"""
    global _last_nominatim_call
    current_time = time.time()
    time_since_last_call = current_time - _last_nominatim_call
    
    if time_since_last_call < 2.0:
        sleep_time = 2.0 - time_since_last_call
        print(f"Rate limiting: waiting {sleep_time:.1f} seconds before Nominatim call")
        time.sleep(sleep_time)
    
    _last_nominatim_call = time.time()

async def geocode_city_nominatim(city: str, country_code: str, state_province: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """Geocode city using Nominatim with enhanced location resolution"""
    try:        
        # Check cache first
        cached = get_cached_coordinates(city, country_code, state_province)
        if cached:
            return cached
        
        geolocator = Nominatim(user_agent="footprint-any-product")
        
        # Strategy A: Try with state/province first if available
        if state_province:
            # Try with state/province in query
            enhanced_query = f"{city}, {state_province}, {country_code}"
            wait_for_rate_limit()  # Rate limit before API call
            location = geolocator.geocode(
                enhanced_query,
                country_codes=[country_code.lower()],
                timeout=10,
                addressdetails=True  # Get detailed address info
            )
            
            if location:
                lat, lon = location.latitude, location.longitude
                cache_coordinates(city, country_code, lat, lon, state_province)
                print(f"Geocoded {city} with state/province: {enhanced_query}")
                return (lat, lon)
            
            # Try alternative format: "City, State/Province"
            alt_query = f"{city}, {state_province}"
            wait_for_rate_limit()  # Rate limit before API call
            location = geolocator.geocode(
                alt_query,
                country_codes=[country_code.lower()],
                timeout=10,
                addressdetails=True
            )
            
            if location:
                lat, lon = location.latitude, location.longitude
                cache_coordinates(city, country_code, lat, lon, state_province)
                print(f"Geocoded {city} with alternative format: {alt_query}")
                return (lat, lon)
        
        # Fallback: Try with just city and country
        wait_for_rate_limit()  # Rate limit before API call
        location = geolocator.geocode(
            city, 
            country_codes=[country_code.lower()], 
            timeout=10,
            addressdetails=True
        )
        
        if location:
            lat, lon = location.latitude, location.longitude
            # If we have addressdetails, try to extract state/province for better caching
            if hasattr(location, 'raw') and 'address' in location.raw:
                address = location.raw['address']
                detected_state = address.get('state') or address.get('province') or address.get('region')
                if detected_state and not state_province:
                    state_province = detected_state
            
            cache_coordinates(city, country_code, lat, lon, state_province)
            print(f"Geocoded {city} with basic query, detected state: {state_province}")
            return (lat, lon)
            
        return None
        
    except (ImportError, GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Nominatim geocoding failed for {city}, {country_code}, {state_province}: {e}")
        return None

async def geocode_city_llm_fallback(city: str, country_code: str, state_province: Optional[str] = None) -> Tuple[float, float]:
    """Use LLM to estimate city coordinates as fallback"""
    
    class CityCoordinates(BaseModel):
        latitude: float = Field(description="Latitude of the city center in decimal degrees")
        longitude: float = Field(description="Longitude of the city center in decimal degrees")
    
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0).with_structured_output(CityCoordinates)
    
    if state_province:
        prompt = f"""
        Provide the approximate latitude and longitude coordinates for the city center of {city} 
        in {state_province}, {country_code}.
        
        Return coordinates in decimal degrees (positive for North/East, negative for South/West).
        """
    else:
        prompt = f"""
        Provide the approximate latitude and longitude coordinates for the city center of {city} in {country_code}.
        
        If there are multiple cities with the same name in this country, choose the largest/most important one
        that would be relevant for freight transportation (prefer major cities, ports, or industrial centers).
        Return coordinates in decimal degrees (positive for North/East, negative for South/West).
        """
    
    response: CityCoordinates = llm.invoke([{"role": "user", "content": prompt}])
    
    # Cache the LLM result too
    cache_coordinates(city, country_code, response.latitude, response.longitude, state_province)
    
    return (response.latitude, response.longitude)

async def geocode_city(city: str, country_code: str, state_province: Optional[str] = None) -> Tuple[Tuple[float, float], str]:
    """
    Geocode a city with enhanced state/province support, trying Nominatim first, then LLM fallback.
    Returns (lat, lon), method_used
    """
    coords = await geocode_city_nominatim(city, country_code, state_province)
    if coords:
        return coords, "nominatim"
    
    coords = await geocode_city_llm_fallback(city, country_code, state_province)
    return coords, "llm_fallback"

def calculate_great_circle_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great circle distance between two points in kilometers using GeoPy"""
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)
    return geodesic(point1, point2).kilometers

async def calculate_route_distance(origin_coords: Tuple[float, float],
                                   dest_coords: Tuple[float, float], 
                                   base_mode: str) -> float:
    """Calculate distance in km between two points based on base transportation mode"""
    
    if base_mode == "ocean_freight":
        print(f"TOOL Transportation: Calculating ocean freight distance for origin_coords: {origin_coords} and dest_coords: {dest_coords}")
        # searoute expects [lon, lat] format
        origin_point = [origin_coords[1], origin_coords[0]]
        dest_point = [dest_coords[1], dest_coords[0]]
        
        route = searoute.searoute(origin_point, dest_point, units="km", append_orig_dest=True)
        distance_km = route['properties']['length']
        
        return distance_km
    else:
        print(f"TOOL Transportation: Calculating great circle distance for origin_coords: {origin_coords} and dest_coords: {dest_coords}")
        # Land-based transportation modes
        great_circle_distance = calculate_great_circle_distance(origin_coords[0], origin_coords[1], 
                                                              dest_coords[0], dest_coords[1])
        circuity_factor = CIRCUITY_FACTORS.get(base_mode, 1.2)
        return great_circle_distance * circuity_factor

async def get_transportation_plan_from_llm(origin: str, destination: str) -> TransportationPlan:
    """Get transportation plan from LLM with structured output"""
    
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0).with_structured_output(TransportationPlan)
    
    prompt = f"""
    I'm shipping freight from {origin} to {destination}. What are the likely origin-destination pairs 
    and transportation modes I would use to minimize costs? Just give me the OD pairs and modes. 
    Make reasonable assumptions. Provide a single, end-to-end set.
    
    For each city, provide:
    - The English name of the city
    - The ISO 3166-1 alpha-2 country code
    - The state, province, or region name (VERY IMPORTANT for countries like US, Canada, Australia to avoid ambiguity)
      Examples: "California", "Ontario", "New South Wales", "Texas", "Alberta"
    
    For transportation modes, provide BOTH:
    - base_mode: Must be exactly one of: "ocean_freight", "rail", "truck", "air"
    - mode: More detailed description for accurate emissions (e.g., "container ship", "freight train", "long-haul truck", "cargo aircraft")
    
    Examples of mode pairs:
    - base_mode: "ocean_freight", mode: "container ship"
    - base_mode: "rail", mode: "freight train"  
    - base_mode: "truck", mode: "long-haul truck"
    - base_mode: "air", mode: "cargo aircraft"
    
    Focus on the most cost-effective route that would typically be used for freight shipping.
    Be specific about states/provinces to avoid ambiguous city names (e.g., Portland, Oregon vs Portland, Maine).
    """
    
    response: TransportationPlan = llm.invoke([{"role": "user", "content": prompt}])
    return response

async def analyze_transportation_route(
        origin: str, 
        destination: str,
        weight_kg: float,
        dimensions_m: Optional[Tuple[float, float, float]] = None
    ) -> TransportationAnalysisResult:
    """
    Main function to analyze transportation between two cities.
    
    Args:
        origin: Origin city name
        destination: Destination city name
        weight_kg: Weight of the shipment in kilograms
        dimensions_m: Dimensions of the shipment in meters (length, width, height)
    Returns:
        TransportationAnalysisResult with complete analysis
    """
    
    # Get transportation plan from LLM
    plan = await get_transportation_plan_from_llm(origin, destination)
    
    route_analyses = []
    total_distance = 0.0
    total_emissions = 0.0
    
    for route in plan.routes:
        # Validate country codes
        if not validate_iso_country_code(route.origin.country_code):
            raise ValueError(f"Invalid country code: {route.origin.country_code}")
        if not validate_iso_country_code(route.destination.country_code):
            raise ValueError(f"Invalid country code: {route.destination.country_code}")
        
        # Geocode cities with state/province support
        origin_coords, origin_method = await geocode_city(
            route.origin.name, 
            route.origin.country_code, 
            route.origin.state_province
        )
        dest_coords, dest_method = await geocode_city(
            route.destination.name, 
            route.destination.country_code, 
            route.destination.state_province
        )
        
        # Calculate distance using base_mode
        distance_km = await calculate_route_distance(origin_coords, dest_coords, route.base_mode)
        
        # Get emissions factor using detailed mode for more accurate emissions
        ef_result = await emissions_factor_finder_tool.ainvoke({
            "process_desc": f"{route.mode}", 
            "phase": "transportation"
        })
        
        # Calculate emissions (assuming emissions factor is in kg CO2e per km)
        ef = Q_(ef_result["CO2e_factor"], ef_result["units"]).to("kgCO2/(kg*km)").magnitude
        emissions = ef * distance_km * weight_kg
        
        # Determine geocoding method and notes
        geocoding_method = "nominatim" if origin_method == "nominatim" and dest_method == "nominatim" else "llm_fallback"
        notes = None
        if geocoding_method == "llm_fallback":
            notes = "Used LLM fallback for coordinate estimation"
        
        route.origin.lat = origin_coords[0]
        route.origin.lon = origin_coords[1]
        route.destination.lat = dest_coords[0]
        route.destination.lon = dest_coords[1]

        route_analysis = TransportationRouteAnalysis(
            origin=route.origin,
            destination=route.destination,
            base_mode=route.base_mode,
            mode=route.mode,
            distance_km=distance_km,
            carbon_emissions_kg_co2e=emissions,
            geocoding_method=f"origin: {origin_method}, destination: {dest_method}",
            notes=notes
        )
        
        route_analyses.append(route_analysis)
        total_distance += distance_km
        total_emissions += emissions
    
    # Generate summary
    route_summary = " → ".join([f"{r.origin.name} ({r.mode})" for r in route_analyses] + 
                               [route_analyses[-1].destination.name])
    
    summary = f"Transportation from {origin} to {destination}: {route_summary}. " \
             f"Total distance: {total_distance:.0f} km, Total emissions: {total_emissions:.2f} kg CO2e."
    
    return TransportationAnalysisResult(
        total_distance_km=total_distance,
        total_carbon_emissions_kg_co2e=total_emissions,
        route_details=route_analyses,
        summary=summary
    )

class TransportationToolSchema(BaseModel):
    """
    Analyze transportation routes and carbon emissions between two cities.
    
    Args:
        origin: Origin city details
        destination: Destination city details
        weight_kg: Weight of the shipment in kilograms
        
    Returns:
        Dictionary with transportation analysis including routes, distances, and emissions
    """
    origin: str = Field(description="Origin city, country, and optionally state/province")
    destination: str = Field(description="Destination city, country, and optionally state/province")
    weight_kg: float = Field(description="Weight of the shipment in kilograms")

@tool(args_schema=TransportationToolSchema)
async def transportation_tool(origin: str, destination: str, weight_kg: float) -> Dict[str, Any]:
    result = await analyze_transportation_route(origin, destination, weight_kg)
    return result.model_dump()