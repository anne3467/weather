#!/usr/bin/env python3
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.sax.saxutils
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8765
SCRIPT_DIR = Path(__file__).resolve().parent

OLD_TILE_ICON_BY_ICON = {
    1: "1",
    2: "3",
    3: "3",
    8: "8",
    15: "15",
    16: "16",
    19: "23",
    20: "20",
    23: "23",
    24: "24",
    25: "27",
    26: "27",
    27: "27",
    29: "30",
    30: "30",
    31: "30",
    50: "50",
}

OLD_TILE_BACKGROUND_BY_ICON = {
    "1": "1",
    "3": "3",
    "8": "8",
    "15": "15",
    "16": "15",
    "20": "8",
    "23": "19",
    "24": "19",
    "27": "27",
    "30": "30",
    "50": "8",
}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "OpenMeteoBingWeatherAdapter/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def qs_value(query, name, default=""):
    vals = query.get(name) or query.get(name.lower()) or query.get(name.upper())
    return vals[0] if vals else default


def iso_with_offset(value, offset_seconds):
    if not value:
        return ""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(seconds=offset_seconds)))
    return dt.isoformat()


def day_iso(value, offset_seconds):
    dt = datetime.fromisoformat(value).replace(tzinfo=timezone(timedelta(seconds=offset_seconds)))
    return dt.isoformat()


def uv_desc(uv):
    if uv is None:
        return ""
    if uv < 3:
        return "Low"
    if uv < 6:
        return "Moderate"
    if uv < 8:
        return "High"
    if uv < 11:
        return "Very high"
    return "Extreme"


def wind_text(speed):
    if speed is None:
        return ""
    if speed < 6:
        return "Light"
    if speed < 20:
        return "Breeze"
    if speed < 39:
        return "Windy"
    return "Strong"


def code_info(code, is_day=1):
    table = {
        0: ("Sunny" if is_day else "Clear", 1 if is_day else 31, "d1000" if is_day else "n1000", "CLR"),
        1: ("Mostly sunny" if is_day else "Mostly clear", 2 if is_day else 29, "d1000" if is_day else "n1000", "SCT"),
        2: ("Partly sunny" if is_day else "Partly cloudy", 3 if is_day else 30, "d2000" if is_day else "n2000", "SCT"),
        3: ("Cloudy", 8, "d3000" if is_day else "n3000", "OVC"),
        45: ("Fog", 20, "d4000" if is_day else "n4000", "FG"),
        48: ("Fog", 20, "d4000" if is_day else "n4000", "FG"),
        51: ("Light rain showers", 19, "d3100" if is_day else "n3100", "-RA"),
        53: ("Rain showers", 23, "d2200" if is_day else "n2200", "RA"),
        55: ("Heavy rain", 24, "d4300" if is_day else "n4300", "RA"),
        61: ("Light rain", 19, "d3100" if is_day else "n3100", "-RA"),
        63: ("Rain", 23, "d2200" if is_day else "n2200", "RA"),
        65: ("Heavy rain", 24, "d4300" if is_day else "n4300", "RA"),
        71: ("Light snow", 25, "d4100" if is_day else "n4100", "-SN"),
        73: ("Snow", 26, "d4200" if is_day else "n4200", "SN"),
        75: ("Heavy snow", 27, "d4300" if is_day else "n4300", "SN"),
        80: ("Light rain showers", 19, "d3100" if is_day else "n3100", "SHRA"),
        81: ("Rain showers", 23, "d2200" if is_day else "n2200", "SHRA"),
        82: ("Heavy rain showers", 24, "d4300" if is_day else "n4300", "SHRA"),
        95: ("Thunderstorms", 15, "d2400" if is_day else "n2400", "TSRA"),
        96: ("Thunderstorms", 15, "d2400" if is_day else "n2400", "TSRA"),
        99: ("Severe thunderstorms", 16, "d2400" if is_day else "n2400", "TSRA"),
    }
    return table.get(int(code or 0), table[3])


def source(lat, lon, timezone_name, offset_seconds, country=""):
    hours = int(offset_seconds // 3600)
    minutes = int(abs(offset_seconds) % 3600 // 60)
    sign = "+" if offset_seconds >= 0 else "-"
    return {
        "id": "open-meteo",
        "coordinates": {"lat": lat, "lon": lon},
        "location": {
            "Name": "",
            "StateCode": "",
            "CountryName": country,
            "CountryCode": "",
            "TimezoneName": timezone_name,
            "TimezoneOffset": f"{sign}{abs(hours):02d}:{minutes:02d}:00",
        },
        "utcOffset": f"{sign}{abs(hours):02d}:{minutes:02d}:00",
        "countryCode": "",
    }


def units(units_param):
    imperial = str(units_param).upper().startswith("F")
    return {
        "system": "Imperial" if imperial else "Metric",
        "pressure": "in" if imperial else "mb",
        "temperature": "°F" if imperial else "°C",
        "speed": "mph" if imperial else "km/h",
        "height": "in" if imperial else "cm",
        "distance": "mi" if imperial else "km",
        "time": "s",
    }


def forecast_url(lat, lon, units_param):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "is_day",
                "precipitation",
                "weather_code",
                "cloud_cover",
                "pressure_msl",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
            ]
        ),
        "hourly": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation_probability",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            ]
        ),
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_direction_10m_dominant",
                "uv_index_max",
                "sunrise",
                "sunset",
            ]
        ),
        "timezone": "auto",
        "forecast_days": "10",
        "wind_speed_unit": "mph" if str(units_param).upper().startswith("F") else "kmh",
    }
    if str(units_param).upper().startswith("F"):
        params["temperature_unit"] = "fahrenheit"
        params["precipitation_unit"] = "inch"
    return "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)


def current_block(data):
    cur = data["current"]
    cap, icon, symbol, sky = code_info(cur.get("weather_code"), cur.get("is_day", 1))
    return {
        "baro": cur.get("pressure_msl"),
        "cap": cap,
        "capAbbr": cap,
        "daytime": "d" if cur.get("is_day", 1) else "n",
        "dewPt": None,
        "feels": cur.get("apparent_temperature"),
        "rh": cur.get("relative_humidity_2m"),
        "icon": icon,
        "symbol": symbol,
        "pvdrIcon": str(icon),
        "urlIcon": "",
        "wx": "",
        "sky": sky,
        "temp": cur.get("temperature_2m"),
        "tempDesc": 0,
        "utci": cur.get("apparent_temperature"),
        "uv": None,
        "uvDesc": "",
        "vis": None,
        "windDir": cur.get("wind_direction_10m"),
        "windSpd": cur.get("wind_speed_10m"),
        "windTh": None,
        "windGust": cur.get("wind_gusts_10m"),
        "created": iso_with_offset(cur.get("time"), data.get("utc_offset_seconds", 0)),
        "pvdrCap": cap,
        "pvdrWindDir": str(cur.get("wind_direction_10m") or ""),
        "pvdrWindSpd": wind_text(cur.get("wind_speed_10m")),
        "richCaps": [],
        "cloudCover": cur.get("cloud_cover"),
    }


def simple_days(data):
    daily = data["daily"]
    offset = data.get("utc_offset_seconds", 0)
    days = []
    for idx, date in enumerate(daily["time"]):
        cap, icon, symbol, _ = code_info(daily["weather_code"][idx], 1)
        days.append(
            {
                "cap": cap,
                "pvdrCap": cap,
                "pvdrWindDir": str(daily["wind_direction_10m_dominant"][idx]),
                "pvdrWindSpd": wind_text(daily["wind_speed_10m_max"][idx]),
                "valid": day_iso(date, offset),
                "icon": icon,
                "pvdrIcon": str(icon),
                "precip": daily["precipitation_probability_max"][idx],
                "tempHi": daily["temperature_2m_max"][idx],
                "tempLo": daily["temperature_2m_min"][idx],
                "created": iso_with_offset(data["current"]["time"], offset),
            }
        )
    return days


def detailed_days(data):
    daily = data["daily"]
    offset = data.get("utc_offset_seconds", 0)
    result = []
    for idx, date in enumerate(daily["time"]):
        cap, icon, symbol, sky = code_info(daily["weather_code"][idx], 1)
        precip = daily["precipitation_probability_max"][idx]
        wind_dir = daily["wind_direction_10m_dominant"][idx]
        wind_speed = daily["wind_speed_10m_max"][idx]
        hi = daily["temperature_2m_max"][idx]
        lo = daily["temperature_2m_min"][idx]
        uv = daily["uv_index_max"][idx]
        day_part = {
            "cap": cap,
            "pvdrCap": cap,
            "pvdrWindDir": str(wind_dir),
            "pvdrWindSpd": str(wind_speed),
            "icon": icon,
            "symbol": symbol,
            "pvdrIcon": str(icon),
            "urlIcon": "",
            "precip": precip,
            "sky": sky,
            "windDir": wind_dir,
            "windSpd": wind_speed,
            "summary": cap,
            "summaries": [cap, f" The high will be {round(hi)}°."],
        }
        night_cap, night_icon, night_symbol, night_sky = code_info(daily["weather_code"][idx], 0)
        night_part = dict(day_part)
        night_part.update(
            {
                "cap": night_cap,
                "pvdrCap": night_cap,
                "icon": night_icon,
                "symbol": night_symbol,
                "pvdrIcon": str(night_icon),
                "sky": night_sky,
                "summaries": [night_cap, f" The low will be {round(lo)}°."],
            }
        )
        result.append(
            {
                "daily": {
                    "day": day_part,
                    "night": night_part,
                    "pvdrCap": cap,
                    "pvdrWindDir": str(wind_dir),
                    "pvdrWindSpd": wind_text(wind_speed),
                    "valid": day_iso(date, offset),
                    "icon": icon,
                    "symbol": symbol,
                    "pvdrIcon": str(icon),
                    "iconUrl": "",
                    "precip": precip,
                    "windMax": wind_speed,
                    "windMaxDir": wind_dir,
                    "windTh": None,
                    "rhHi": None,
                    "rhLo": None,
                    "tempHi": hi,
                    "tempLo": lo,
                    "uv": uv,
                    "uvDesc": uv_desc(uv),
                    "created": iso_with_offset(data["current"]["time"], offset),
                    "rainAmount": 0.0,
                    "snowAmount": 0.0,
                },
                "almanac": {
                    "valid": day_iso(date, offset),
                    "sunrise": iso_with_offset(daily["sunrise"][idx], offset),
                    "sunset": iso_with_offset(daily["sunset"][idx], offset),
                    "moonPhase": "",
                    "moonPhaseCode": "",
                },
            }
        )
    return result


def hourly_trend(data):
    hourly = data["hourly"]
    offset = data.get("utc_offset_seconds", 0)
    hours = []
    for idx, stamp in enumerate(hourly["time"][:72]):
        cap, icon, symbol, sky = code_info(hourly["weather_code"][idx], 1)
        hours.append(
            {
                "valid": iso_with_offset(stamp, offset),
                "cap": cap,
                "pvdrCap": cap,
                "icon": icon,
                "symbol": symbol,
                "pvdrIcon": str(icon),
                "temp": hourly["temperature_2m"][idx],
                "rh": hourly["relative_humidity_2m"][idx],
                "precip": hourly["precipitation_probability"][idx],
                "windSpd": hourly["wind_speed_10m"][idx],
                "windDir": hourly["wind_direction_10m"][idx],
                "sky": sky,
            }
        )
    return hours


def weather_response(path, query):
    match = re.search(r"/weather/([^/]+)/(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", path)
    if not match:
        match = re.search(r"/weather/forecast/([^/]+)/(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", path)
    if not match:
        raise ValueError("missing coordinates")
    kind = match.group(1)
    lat = float(match.group(2))
    lon = float(match.group(3))
    units_param = qs_value(query, "units", "C")
    data = fetch_json(forecast_url(lat, lon, units_param))
    base = {
        "responses": [
            {
                "weather": [],
                "source": source(lat, lon, data.get("timezone", ""), data.get("utc_offset_seconds", 0)),
            }
        ],
        "units": units(units_param),
        "copyright": "Weather data by Open-Meteo.com.",
    }
    if kind == "current":
        base["responses"][0]["weather"].append(
            {
                "alerts": [],
                "current": current_block(data),
                "nowcasting": {"summary": "", "shortSummary": "", "enableRainSignal": False},
                "contentdata": [],
                "provider": {"name": "Open-Meteo", "url": "https://open-meteo.com/"},
            }
        )
    elif kind == "summary":
        base["responses"][0]["weather"].append(
            {
                "alerts": 0,
                "current": current_block(data),
                "forecast": {"days": simple_days(data)},
                "provider": {"name": "Open-Meteo", "url": "https://open-meteo.com/"},
            }
        )
    elif kind == "daily":
        base["responses"][0]["weather"].append(
            {"days": detailed_days(data), "provider": {"name": "Open-Meteo", "url": "https://open-meteo.com/"}}
        )
    elif kind == "trend":
        base["responses"][0]["weather"].append(
            {"hours": hourly_trend(data), "provider": {"name": "Open-Meteo", "url": "https://open-meteo.com/"}}
        )
    elif kind == "alerts":
        base["responses"][0]["weather"].append({"alerts": []})
    elif kind == "average":
        base["responses"][0]["weather"].append({"averages": []})
    else:
        base["responses"][0]["weather"].append(
            {"current": current_block(data), "forecast": {"days": simple_days(data)}}
        )
    return base


def geocode_response(path, query):
    parts = [p for p in path.split("/") if p]
    term = ""
    if "search" in parts:
        idx = parts.index("search")
        if idx + 1 < len(parts):
            term = urllib.parse.unquote(parts[idx + 1])
    term = term or qs_value(query, "q") or qs_value(query, "query") or qs_value(query, "locality")
    lat = qs_value(query, "latitude")
    lon = qs_value(query, "longitude")
    if lat and lon and not term:
        loc = {
            "name": f"{lat},{lon}",
            "nameid": f"{lat},{lon}",
            "displayName": f"{lat},{lon}",
            "locality": "",
            "adminDistrict": "",
            "countryRegion": "",
            "countryCode": "",
            "dataSources": [{"id": "open-meteo", "coordinates": {"lat": float(lat), "lon": float(lon)}, "provider": "Open-Meteo", "distance": 0}],
            "entityType": "PopulatedPlace",
            "confidence": "High",
            "coordinates": {"lat": float(lat), "lon": float(lon)},
        }
        return {"responses": [{"locations": [loc]}], "units": units("C"), "copyright": "Geocoding by Open-Meteo.com."}
    if not term:
        return {"responses": [{"locations": []}], "units": units("C"), "copyright": "Geocoding by Open-Meteo.com."}
    culture = parts[0] if parts else "en-us"
    lang = culture.split("-")[0]
    url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
        {"name": term, "count": "8", "language": lang, "format": "json"}
    )
    data = fetch_json(url)
    locations = []
    for item in data.get("results", []):
        name = item.get("name", "")
        admin = item.get("admin1", "")
        country = item.get("country", "")
        latv = item.get("latitude")
        lonv = item.get("longitude")
        locations.append(
            {
                "name": ", ".join(x for x in (name, admin, country) if x),
                "nameid": " ".join(x for x in (name, admin, country) if x),
                "displayName": name,
                "locality": name,
                "adminDistrict": admin,
                "countryRegion": country,
                "countryCode": item.get("country_code", ""),
                "dataSources": [{"id": str(item.get("id", "open-meteo")), "coordinates": {"lat": latv, "lon": lonv}, "provider": "Open-Meteo", "distance": 0}],
                "entityType": "PopulatedPlace",
                "confidence": "High",
                "coordinates": {"lat": latv, "lon": lonv},
            }
        )
    return {"responses": [{"locations": locations}], "units": units("C"), "copyright": "Geocoding by Open-Meteo.com."}


def virtual_earth_response(path, query):
    term = qs_value(query, "query") or qs_value(query, "q")
    geo = geocode_response(path + "/" + urllib.parse.quote(term), query)
    resources = []
    for loc in geo["responses"][0]["locations"]:
        lat = loc["coordinates"]["lat"]
        lon = loc["coordinates"]["lon"]
        resources.append(
            {
                "__type": "Location:http://schemas.microsoft.com/search/local/ws/rest/v1",
                "bbox": [lat - 0.03, lon - 0.03, lat + 0.03, lon + 0.03],
                "name": loc["name"],
                "point": {"type": "Point", "coordinates": [lat, lon]},
                "address": {
                    "adminDistrict": loc.get("adminDistrict", ""),
                    "countryRegion": loc.get("countryRegion", ""),
                    "formattedAddress": loc["name"],
                    "locality": loc.get("locality", ""),
                    "countryRegionIso2": loc.get("countryCode", ""),
                },
                "confidence": loc.get("confidence", "High"),
                "entityType": loc.get("entityType", "PopulatedPlace"),
                "geocodePoints": [
                    {
                        "type": "Point",
                        "coordinates": [lat, lon],
                        "calculationMethod": "Rooftop",
                        "usageTypes": ["Display"],
                    }
                ],
                "matchCodes": ["Good"],
            }
        )
    return {
        "authenticationResultCode": "ValidCredentials",
        "brandLogoUri": "",
        "copyright": "Geocoding by Open-Meteo.com.",
        "resourceSets": [{"estimatedTotal": len(resources), "resources": resources}],
        "statusCode": 200,
        "statusDescription": "OK",
        "traceId": "open-meteo",
    }


def qsonhs_response(path, query):
    term = qs_value(query, "q") or qs_value(query, "query")
    geo = geocode_response("/en-us/locations/search/" + urllib.parse.quote(term), query)
    suggests = []
    for idx, loc in enumerate(geo["responses"][0]["locations"][: int(qs_value(query, "count", "5") or 5)]):
        suggests.append(
            {
                "Txt": loc["name"],
                "Type": "AS",
                "Sk": f"AS{idx + 1}",
                "HCS": 0,
                "Lat": loc["coordinates"]["lat"],
                "Long": loc["coordinates"]["lon"],
                "Country": loc.get("countryRegion", ""),
                "AdminDistrict": loc.get("adminDistrict", ""),
                "Locality": loc.get("locality", ""),
            }
        )
    return {
        "AS": {
            "Query": term,
            "FullResults": 1 if suggests else 0,
            "Results": [{"Type": "AS", "Suggests": suggests}] if suggests else [],
        }
    }


def bing_geo_autosuggest_response(path, query):
    term = qs_value(query, "q") or qs_value(query, "query")
    geo = geocode_response("/en-us/locations/search/" + urllib.parse.quote(term), query)
    values = []
    for loc in geo["responses"][0]["locations"]:
        values.append(
            {
                "@type": "s:Place",
                "s:name": loc["name"],
                "s:address": {
                    "@type": "s:PostalAddress",
                    "s:addressLocality": loc.get("locality", ""),
                    "s:addressRegion": loc.get("adminDistrict", ""),
                    "s:addressCountry": loc.get("countryCode", ""),
                },
                "s:geo": {
                    "@type": "s:GeoCoordinates",
                    "s:latitude": loc["coordinates"]["lat"],
                    "s:longitude": loc["coordinates"]["lon"],
                },
                "b:entityType": loc.get("entityType", "PopulatedPlace"),
                "b:confidence": loc.get("confidence", "High"),
            }
        )
    return {
        "@context": {"s": "http://schema.org/", "b": "http://platform.bing.com/geo/"},
        "@type": "b:Places",
        "b:value": values,
    }


def tile_xml(path, query):
    if "/DesktopTile/Badge" in path:
        return """<?xml version="1.0" encoding="utf-8"?><badge value="available"/>"""

    match = re.search(r"/livetile/(?:front|back)/(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", path)
    lat = float(match.group(1)) if match else float(qs_value(query, "latitude", "39.9042"))
    lon = float(match.group(2)) if match else float(qs_value(query, "longitude", "116.4074"))
    units_param = qs_value(query, "units", qs_value(query, "unit", "C"))
    location = (
        qs_value(query, "locationName", "")
        or qs_value(query, "displayName", "")
        or qs_value(query, "location", "")
        or qs_value(query, "city", "")
        or "天气"
    )
    location = urllib.parse.unquote(location)

    try:
        data = fetch_json(forecast_url(lat, lon, units_param))
        hourly = data.get("hourly", {})
        items = []
        for idx, stamp in enumerate(hourly.get("time", [])[:3]):
            when = datetime.fromisoformat(stamp)
            temp = hourly.get("temperature_2m", [])[idx]
            code = hourly.get("weather_code", [0])[idx]
            cap, icon, _, _ = code_info(code, 1)
            items.append(
                {
                    "time": when.strftime("%H:00"),
                    "temp": f"{round(temp)}°",
                    "icon": OLD_TILE_ICON_BY_ICON.get(icon, "8"),
                    "alt": cap,
                }
            )
    except Exception:
        items = [
            {"time": "--:--", "temp": "--°", "icon": "23", "alt": "Weather"},
            {"time": "--:--", "temp": "--°", "icon": "3", "alt": "Weather"},
            {"time": "--:--", "temp": "--°", "icon": "3", "alt": "Weather"},
        ]

    while len(items) < 3:
        items.append(items[-1])

    def esc(value):
        return xml.sax.saxutils.escape(str(value))

    def col(item):
        icon = f"http://127.0.0.1:{PORT}/assets/WeatherIcons/30x30/{item['icon']}.png"
        return f"""
        <subgroup hint-weight="1">
          <text hint-align="center" hint-style="caption" hint-maxLines="1">{esc(item['time'])}</text>
          <image src="{esc(icon)}" alt="{esc(item['alt'])}" hint-align="center"/>
          <text hint-align="center" hint-style="base" hint-maxLines="1">{esc(item['temp'])}</text>
        </subgroup>"""

    columns = "".join(col(item) for item in items[:3])
    loc = esc(location)
    bg_icon = OLD_TILE_BACKGROUND_BY_ICON.get(str(items[0]["icon"]), "8")
    bg_medium = esc(f"http://127.0.0.1:{PORT}/assets/WeatherImages/210x173/{bg_icon}.jpg")
    bg_wide = esc(f"http://127.0.0.1:{PORT}/assets/WeatherImages/423x173/{bg_icon}.jpg")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<tile>
  <visual branding="none" displayName="{loc}">
    <binding template="TileMedium" hint-textStacking="center">
      <image src="{bg_medium}" placement="background" hint-overlay="0"/>
      <group>{columns}
      </group>
      <text hint-style="base" hint-maxLines="1">{loc}</text>
    </binding>
    <binding template="TileWide">
      <image src="{bg_wide}" placement="background" hint-overlay="0"/>
      <group>{columns}
      </group>
      <text hint-style="base" hint-maxLines="1">{loc}</text>
    </binding>
    <binding template="TileLarge">
      <image src="{bg_wide}" placement="background" hint-overlay="0"/>
      <group>{columns}
      </group>
      <text hint-style="base" hint-maxLines="1">{loc}</text>
    </binding>
  </visual>
</tile>"""


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_text(self, payload, content_type="text/plain; charset=utf-8", status=200):
        raw = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_file(self, path, content_type):
        raw = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        path = parsed.path
        try:
            if path == "/health":
                self.send_json({"ok": True, "provider": "Open-Meteo", "time": int(time.time())})
            elif "/qsonhs.aspx" in path:
                self.send_json(qsonhs_response(path, query))
            elif "/geo/AutoSuggest" in path:
                self.send_json(bing_geo_autosuggest_response(path, query))
            elif "/REST/v1/Locations" in path:
                self.send_json(virtual_earth_response(path, query))
            elif "/configcontainer/" in path or path.endswith("/Patches.diff"):
                self.send_text("", "text/plain; charset=utf-8", 404)
            elif "/locations/search" in path:
                self.send_json(geocode_response(path, query))
            elif "/weather/" in path:
                self.send_json(weather_response(path, query))
            elif path.startswith("/assets/WeatherIcons/") and path.endswith(".png"):
                name = Path(path).name
                size = "30x30" if "/30x30/" in path else "106"
                icon_path = SCRIPT_DIR / "WeatherIcons" / size / name
                if icon_path.exists():
                    self.send_file(icon_path, "image/png")
                else:
                    self.send_json({"error": "icon not found", "path": path}, 404)
            elif path.startswith("/assets/WeatherImages/") and path.endswith(".jpg"):
                name = Path(path).name
                size = "423x173" if "/423x173/" in path else "210x173"
                image_path = SCRIPT_DIR / "WeatherImages" / size / name
                if image_path.exists():
                    self.send_file(image_path, "image/jpeg")
                else:
                    self.send_json({"error": "background not found", "path": path}, 404)
            elif "/livetile/" in path or "/DesktopTile/Badge" in path:
                self.send_text(tile_xml(path, query), "application/xml; charset=utf-8")
            else:
                self.send_json({"error": "not found", "path": path}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc), "path": path}, 500)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Open-Meteo MSN adapter running at http://127.0.0.1:{PORT}/health")
    server.serve_forever()


if __name__ == "__main__":
    main()
