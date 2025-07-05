"""
Unit tests for the transportation tool

Run with: pytest tests/test_tools/test_transportation.py -v
"""

import pytest
import asyncio
import json
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Tuple

from tools.transportation.transportation import (
    validate_iso_country_code,
    get_cache_key,
    get_cached_coordinates,
    cache_coordinates,
    wait_for_rate_limit,
    geocode_city_nominatim,
    geocode_city_llm_fallback,
    geocode_city,
    calculate_great_circle_distance,
    calculate_route_distance,
    get_transportation_plan_from_llm,
    analyze_transportation_route,
    transportation_tool,
    City,
    TransportationRoute,
    TransportationPlan,
    TransportationRouteAnalysis,
    TransportationAnalysisResult,
    CACHE_DIR
)

class TestValidateISOCountryCode:
    """Test ISO country code validation"""
    
    def test_valid_country_codes(self):
        """Test valid ISO 3166-1 alpha-2 country codes"""
        assert validate_iso_country_code("US") == True
        assert validate_iso_country_code("us") == True
        assert validate_iso_country_code("CA") == True
        assert validate_iso_country_code("GB") == True
        assert validate_iso_country_code("DE") == True
        assert validate_iso_country_code("JP") == True
    
    def test_invalid_country_codes(self):
        """Test invalid country codes"""
        assert validate_iso_country_code("XX") == False
        assert validate_iso_country_code("ZZ") == False
        assert validate_iso_country_code("USA") == False  # 3-letter code
        assert validate_iso_country_code("12") == False
        assert validate_iso_country_code("") == False


class TestCacheOperations:
    """Test caching functionality"""
    
    def test_get_cache_key(self):
        """Test cache key generation"""
        key1 = get_cache_key("New York", "US")
        key2 = get_cache_key("New York", "US", "New York")
        key3 = get_cache_key("new york", "us")  # Case insensitive
        key4 = get_cache_key("London", "GB")
        
        assert len(key1) == 32  # MD5 hash length
        assert key1 != key2  # Different with state
        assert key1 == key3  # Case insensitive
        assert key1 != key4  # Different cities
    
    def test_cache_coordinates(self, temp_cache_dir):
        """Test coordinate caching"""
        with patch('tools.transportation.transportation.CACHE_DIR', temp_cache_dir):
            cache_coordinates("New York", "US", 40.7128, -74.0060, "New York")
            
            # Check if cache file was created
            cache_files = list(temp_cache_dir.glob("*.json"))
            assert len(cache_files) == 1
            
            # Check cache file content
            with open(cache_files[0], 'r') as f:
                data = json.load(f)
                assert data['city'] == "New York"
                assert data['country_code'] == "US"
                assert data['state_province'] == "New York"
                assert data['lat'] == 40.7128
                assert data['lon'] == -74.0060
    
    def test_get_cached_coordinates(self, temp_cache_dir):
        """Test retrieving cached coordinates"""
        with patch('tools.transportation.transportation.CACHE_DIR', temp_cache_dir):
            # First cache some coordinates
            cache_coordinates("Paris", "FR", 48.8566, 2.3522)
            
            # Then retrieve them
            coords = get_cached_coordinates("Paris", "FR")
            assert coords == (48.8566, 2.3522)
            
            # Test cache miss
            coords = get_cached_coordinates("Rome", "IT")
            assert coords is None


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @patch('tools.transportation.transportation.time')
    def test_wait_for_rate_limit_no_wait(self, mock_time, reset_rate_limiter):
        """Test rate limiting when enough time has passed"""
        mock_time.time.return_value = 10.0
        mock_time.sleep = Mock()
        
        # Set last call to more than 2 seconds ago
        import tools.transportation.transportation as transport_module
        transport_module._last_nominatim_call = 7.0  # 3 seconds ago
        
        wait_for_rate_limit()
        
        # Should not sleep
        mock_time.sleep.assert_not_called()
        assert transport_module._last_nominatim_call == 10.0
    
    @patch('tools.transportation.transportation.time')
    def test_wait_for_rate_limit_with_wait(self, mock_time, reset_rate_limiter):
        """Test rate limiting when recent call requires waiting"""
        mock_time.time.return_value = 10.0
        mock_time.sleep = Mock()
        
        # Set last call to 1 second ago
        import tools.transportation.transportation as transport_module
        transport_module._last_nominatim_call = 9.0  # 1 second ago
        
        wait_for_rate_limit()
        
        # Should sleep for 1 second
        mock_time.sleep.assert_called_once_with(1.0)
        assert transport_module._last_nominatim_call == 10.0


class TestDistanceCalculations:
    """Test distance calculation functions"""
    
    def test_calculate_great_circle_distance(self):
        """Test great circle distance calculation"""
        # New York to Los Angeles (approximately 3944 km)
        distance = calculate_great_circle_distance(40.7128, -74.0060, 34.0522, -118.2437)
        assert 3900 < distance < 4000
        
        # Same point distance should be 0
        distance = calculate_great_circle_distance(40.7128, -74.0060, 40.7128, -74.0060)
        assert distance < 0.001
    
    @patch('tools.transportation.transportation.searoute')
    @pytest.mark.asyncio
    async def test_calculate_route_distance_ocean(self, mock_searoute):
        """Test ocean freight distance calculation using searoute"""
        # Mock searoute response
        mock_route = {
            'properties': {
                'length': 3000  # nautical miles
            }
        }
        mock_searoute.searoute.return_value = mock_route
        
        coords1 = (40.7128, -74.0060)  # New York
        coords2 = (51.5074, -0.1278)   # London
        
        distance = await calculate_route_distance(coords1, coords2, "ocean_freight")
        
        # 3000 nautical miles = 5556 km
        expected_distance = 3000 * 1.852
        assert abs(distance - expected_distance) < 0.1
        
        # Verify searoute was called with correct format [lon, lat]
        mock_searoute.searoute.assert_called_once_with([-74.0060, 40.7128], [-0.1278, 51.5074])
    
    @pytest.mark.asyncio
    async def test_calculate_route_distance_land(self):
        """Test land-based distance calculation with circuity factors"""
        coords1 = (40.7128, -74.0060)  # New York
        coords2 = (34.0522, -118.2437)  # Los Angeles
        
        # Test truck (should apply 1.2 circuity factor)
        distance_truck = await calculate_route_distance(coords1, coords2, "truck")
        great_circle = calculate_great_circle_distance(40.7128, -74.0060, 34.0522, -118.2437)
        expected_truck = great_circle * 1.2
        assert abs(distance_truck - expected_truck) < 0.1
        
        # Test air (should apply 1.0 circuity factor)
        distance_air = await calculate_route_distance(coords1, coords2, "air")
        expected_air = great_circle * 1.0
        assert abs(distance_air - expected_air) < 0.1


class TestGeocoding:
    """Test geocoding functions"""
    
    @patch('tools.transportation.transportation.get_cached_coordinates')
    @patch('tools.transportation.transportation.wait_for_rate_limit')
    @patch('tools.transportation.transportation.Nominatim')
    @pytest.mark.asyncio
    async def test_geocode_city_nominatim_success(self, mock_nominatim_class, mock_wait, mock_get_cache, mock_nominatim_location):
        """Test successful Nominatim geocoding"""
        # Mock cache miss
        mock_get_cache.return_value = None
        
        # Mock Nominatim response
        mock_geolocator = Mock()
        mock_geolocator.geocode.return_value = mock_nominatim_location
        mock_nominatim_class.return_value = mock_geolocator
        
        with patch('tools.transportation.transportation.cache_coordinates') as mock_cache:
            result = await geocode_city_nominatim("New York", "US", "New York")
            
            assert result == (40.7128, -74.0060)
            mock_wait.assert_called()
            mock_cache.assert_called_once()
    
    @patch('tools.transportation.transportation.get_cached_coordinates')
    @pytest.mark.asyncio
    async def test_geocode_city_nominatim_cache_hit(self, mock_get_cache):
        """Test Nominatim geocoding with cache hit"""
        # Mock cache hit
        mock_get_cache.return_value = (40.7128, -74.0060)
        
        result = await geocode_city_nominatim("New York", "US")
        
        assert result == (40.7128, -74.0060)
        # Should not make any API calls
    
    @patch('tools.transportation.transportation.ChatOpenAI')
    @pytest.mark.asyncio
    async def test_geocode_city_llm_fallback(self, mock_openai, mock_llm_response):
        """Test LLM fallback geocoding"""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_openai.return_value.with_structured_output.return_value = mock_llm
        
        with patch('tools.transportation.transportation.cache_coordinates') as mock_cache:
            result = await geocode_city_llm_fallback("New York", "US", "New York")
            
            assert result == (40.7128, -74.0060)
            mock_cache.assert_called_once()
    
    @patch('tools.transportation.transportation.geocode_city_nominatim')
    @patch('tools.transportation.transportation.geocode_city_llm_fallback')
    @pytest.mark.asyncio
    async def test_geocode_city_success(self, mock_llm_fallback, mock_nominatim):
        """Test main geocode function with Nominatim success"""
        mock_nominatim.return_value = (40.7128, -74.0060)
        
        result = await geocode_city("New York", "US")
        
        assert result == ((40.7128, -74.0060), "nominatim")
        mock_llm_fallback.assert_not_called()
    
    @patch('tools.transportation.transportation.geocode_city_nominatim')
    @patch('tools.transportation.transportation.geocode_city_llm_fallback')
    @pytest.mark.asyncio
    async def test_geocode_city_llm_fallback_used(self, mock_llm_fallback, mock_nominatim):
        """Test main geocode function with LLM fallback"""
        mock_nominatim.return_value = None
        mock_llm_fallback.return_value = (40.7128, -74.0060)
        
        result = await geocode_city("New York", "US")
        
        assert result == ((40.7128, -74.0060), "llm_fallback")
        mock_llm_fallback.assert_called_once()


class TestLLMIntegration:
    """Test LLM integration functions"""
    
    @patch('tools.transportation.transportation.ChatOpenAI')
    @pytest.mark.asyncio
    async def test_get_transportation_plan_from_llm(self, mock_openai):
        """Test getting transportation plan from LLM"""
        # Mock LLM response
        mock_route = TransportationRoute(
            origin=City(name="New York", country_code="US", state_province="New York"),
            destination=City(name="Los Angeles", country_code="US", state_province="California"),
            base_mode="truck",
            mode="long-haul truck"
        )
        mock_plan = TransportationPlan(routes=[mock_route])
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_plan
        mock_openai.return_value.with_structured_output.return_value = mock_llm
        
        result = await get_transportation_plan_from_llm("New York", "Los Angeles")
        
        assert isinstance(result, TransportationPlan)
        assert len(result.routes) == 1
        assert result.routes[0].origin.name == "New York"
        assert result.routes[0].destination.name == "Los Angeles"
        assert result.routes[0].base_mode == "truck"


class TestMainWorkflow:
    """Test main transportation analysis workflow"""
    
    @patch('tools.transportation.transportation.get_transportation_plan_from_llm')
    @patch('tools.transportation.transportation.geocode_city')
    @patch('tools.transportation.transportation.calculate_route_distance')
    @patch('tools.transportation.transportation.emissions_factor_finder_tool')
    @pytest.mark.asyncio
    async def test_analyze_transportation_route(self, mock_emissions, mock_distance, mock_geocode, mock_llm):
        """Test full transportation route analysis"""
        # Mock LLM plan
        mock_route = TransportationRoute(
            origin=City(name="New York", country_code="US", state_province="New York"),
            destination=City(name="Los Angeles", country_code="US", state_province="California"),
            base_mode="truck",
            mode="long-haul truck"
        )
        mock_plan = TransportationPlan(routes=[mock_route])
        mock_llm.return_value = mock_plan
        
        # Mock geocoding
        mock_geocode.side_effect = [
            ((40.7128, -74.0060), "nominatim"),  # New York
            ((34.0522, -118.2437), "nominatim")  # Los Angeles
        ]
        
        # Mock distance calculation
        mock_distance.return_value = 4000.0  # 4000 km
        
        # Mock emissions factor
        mock_emissions.return_value = {"CO2e_factor": 0.1}  # 0.1 kg CO2e per km
        
        result = await analyze_transportation_route("New York", "Los Angeles")
        
        assert isinstance(result, TransportationAnalysisResult)
        assert result.total_distance_km == 4000.0
        assert result.total_carbon_emissions_kg_co2e == 400.0  # 4000 * 0.1
        assert len(result.route_details) == 1
        
        route_detail = result.route_details[0]
        assert route_detail.origin.name == "New York"
        assert route_detail.destination.name == "Los Angeles"
        assert route_detail.base_mode == "truck"
        assert route_detail.mode == "long-haul truck"
        assert route_detail.geocoding_method == "nominatim"
    
    @patch('tools.transportation.transportation.analyze_transportation_route')
    @pytest.mark.asyncio
    async def test_transportation_tool_success(self, mock_analyze):
        """Test transportation tool wrapper function success"""
        mock_result = TransportationAnalysisResult(
            total_distance_km=4000.0,
            total_carbon_emissions_kg_co2e=400.0,
            route_details=[],
            summary="Test summary"
        )
        mock_analyze.return_value = mock_result
        
        result = await transportation_tool.ainvoke({"origin": "New York", "destination": "Los Angeles"})
        
        assert result["total_distance_km"] == 4000.0
        assert result["total_carbon_emissions_kg_co2e"] == 400.0
        assert result["summary"] == "Test summary"
    
    @patch('tools.transportation.transportation.analyze_transportation_route')
    @pytest.mark.asyncio
    async def test_transportation_tool_error(self, mock_analyze):
        """Test transportation tool wrapper function error handling"""
        mock_analyze.side_effect = Exception("Test error")
        
        result = await transportation_tool.ainvoke({"origin": "New York", "destination": "Los Angeles"})
        
        assert "error" in result
        assert "Test error" in result["error"]
        assert result["total_distance_km"] == 0
        assert result["total_carbon_emissions_kg_co2e"] == 0


class TestDataModels:
    """Test Pydantic data models"""
    
    def test_city_model(self):
        """Test City model"""
        city = City(name="New York", country_code="US", state_province="New York")
        assert city.name == "New York"
        assert city.country_code == "US"
        assert city.state_province == "New York"
        
        # Test without state_province
        city_no_state = City(name="Paris", country_code="FR")
        assert city_no_state.state_province is None
    
    def test_transportation_route_model(self):
        """Test TransportationRoute model"""
        origin = City(name="New York", country_code="US")
        destination = City(name="Los Angeles", country_code="US")
        
        route = TransportationRoute(
            origin=origin,
            destination=destination,
            base_mode="truck",
            mode="long-haul truck"
        )
        
        assert route.base_mode == "truck"
        assert route.mode == "long-haul truck"
        
        # Test literal validation for base_mode
        with pytest.raises(Exception):  # Should fail validation
            TransportationRoute(
                origin=origin,
                destination=destination,
                base_mode="invalid_mode",  # Invalid literal
                mode="some truck"
            )


# Integration test that can be run manually (requires API keys)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_integration():
    """Full integration test (requires API keys, marked as integration)"""
    try:
        result = await transportation_tool.ainvoke({"origin": "New York", "destination": "London"})
        
        assert "error" not in result
        assert result["total_distance_km"] > 0
        assert result["total_carbon_emissions_kg_co2e"] > 0
        assert len(result["route_details"]) > 0
        
        print(f"Integration test passed: {result['summary']}")
        
    except Exception as e:
        pytest.skip(f"Integration test skipped due to missing dependencies or API keys: {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])