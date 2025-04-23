from __future__ import annotations as _annotations

import os
from typing import Any
import requests
from pydantic_ai import Agent, ModelRetry, RunContext
from dotenv import load_dotenv

load_dotenv()

weather_agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt=(
        'Be concise, reply with one sentence.'
        'Use the `get_lat_lng` tool to get the latitude and longitude of the locations, '
        'then use the `get_weather` tool to get the weather.'
    ),
    retries=2,
    instrument=True,
)


@weather_agent.tool
def get_lat_lng(
    ctx: RunContext, 
    location_description: str
) -> dict[str, float]:
    """Get the latitude and longitude of a location.

    Args:
        ctx: The context.
        location_description: A description of a location.
    """
    if os.getenv('GEOCODING_API_KEY') is None:
        # if no API key is provided, return a dummy response (London)
        return {'lat': 51.1, 'lng': -0.1}

    params = {
        'q': location_description,
        'api_key': os.getenv('GEOCODING_API_KEY')
    }
    r = requests.get(
        'https://geocode.maps.co/search', 
        params=params
    )
    r.raise_for_status()
    data = r.json()

    if data:
        return {'lat': float(data[0]['lat']), 'lng': float(data[0]['lon'])}
    else:
        raise ModelRetry('Could not find the location')


@weather_agent.tool
def get_weather(
    ctx: RunContext, 
    lat: float, 
    lng: float
) -> dict[str, Any]:
    """Get the weather at a location.

    Args:
        ctx: The context.
        lat: Latitude of the location.
        lng: Longitude of the location.
    """
    if os.getenv('WEATHER_API_KEY') is None:
        # if no API key is provided, return a dummy response
        return {'temperature': '21 °C', 'description': 'Sunny'}

    params = {
        'apikey': os.getenv('WEATHER_API_KEY'),
        'location': f'{lat},{lng}',
        'units': 'metric',
    }
    r = requests.get(
        'https://api.tomorrow.io/v4/weather/realtime', 
        params=params
    )
    r.raise_for_status()
    data = r.json()

    values = data['data']['values']
    # https://docs.tomorrow.io/reference/data-layers-weather-codes
    code_lookup = {
        1000: 'Clear, Sunny',
        1100: 'Mostly Clear',
        1101: 'Partly Cloudy',
        1102: 'Mostly Cloudy',
        1001: 'Cloudy',
        2000: 'Fog',
        2100: 'Light Fog',
        4000: 'Drizzle',
        4001: 'Rain',
        4200: 'Light Rain',
        4201: 'Heavy Rain',
        5000: 'Snow',
        5001: 'Flurries',
        5100: 'Light Snow',
        5101: 'Heavy Snow',
        6000: 'Freezing Drizzle',
        6001: 'Freezing Rain',
        6200: 'Light Freezing Rain',
        6201: 'Heavy Freezing Rain',
        7000: 'Ice Pellets',
        7101: 'Heavy Ice Pellets',
        7102: 'Light Ice Pellets',
        8000: 'Thunderstorm',
    }
    return {
        'temperature': f'{values["temperatureApparent"]:0.0f}°C',
        'description': code_lookup.get(values['weatherCode'], 'Unknown'),
    }

if __name__ == '__main__':
    res = weather_agent.run_sync(
        'What is the weather in Tokyo?'
    )
    print(res.data)