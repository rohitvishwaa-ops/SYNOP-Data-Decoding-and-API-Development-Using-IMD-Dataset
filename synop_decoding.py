"""
╔══════════════════════════════════════════════════════════╗
║   IMD SYNOP DECODER — Interactive Menu-Driven Tool       ║
║   FM-12 Surface Synoptic Code  |  IMD Meenambakkam       ║
╚══════════════════════════════════════════════════════════╝

Usage:
    python synop_decoder.py
"""

import re, math, os, json, datetime
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ANSI colour helpers
# ═══════════════════════════════════════════════════════════
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
MAGENTA= "\033[95m"
WHITE  = "\033[97m"
DIM    = "\033[2m"

def c(text, colour): return f"{colour}{text}{RESET}"
def header(text):    print(f"\n{BOLD}{CYAN}{text}{RESET}")
def sep(char="─", n=58): print(c(char * n, DIM))
def ok(text):        print(f"  {GREEN}✔{RESET}  {text}")
def warn(text):      print(f"  {YELLOW}⚠{RESET}  {text}")
def err(text):       print(f"  {RED}✖{RESET}  {text}")
def info(text):      print(f"  {BLUE}ℹ{RESET}  {text}")

# ═══════════════════════════════════════════════════════════
# DATA CLASS
# ═══════════════════════════════════════════════════════════
@dataclass
class SynopData:
    station_id: Optional[str]   = None
    day: Optional[int]          = None
    utc_hour: Optional[int]     = None
    wind_unit: Optional[str]    = None

    precip_included: Optional[bool]  = None
    station_type: Optional[str]      = None
    cloud_base_height_m: Optional[float] = None
    visibility_km: Optional[float]   = None
    cloud_cover_oktas: Optional[int] = None
    wind_direction_deg: Optional[int]= None
    wind_speed: Optional[float]      = None
    wind_speed_unit: Optional[str]   = None
    temperature_c: Optional[float]   = None
    dewpoint_c: Optional[float]      = None
    rel_humidity_pct: Optional[float]= None
    pressure_station_hpa: Optional[float] = None
    pressure_msl_hpa: Optional[float]     = None
    present_weather: Optional[str]        = None
    present_weather_code: Optional[int]   = None
    past_weather_1: Optional[str]         = None
    past_weather_2: Optional[str]         = None
    cloud_low_type: Optional[str]         = None
    cloud_mid_type: Optional[str]         = None
    cloud_high_type: Optional[str]        = None
    low_cloud_cover: Optional[int]        = None
    max_temperature_c: Optional[float]    = None
    min_temperature_c: Optional[float]    = None
    thunderstorm: bool      = False
    thunderstorm_rain: bool = False
    raw_groups: list  = field(default_factory=list)
    warnings: list    = field(default_factory=list)

# ═══════════════════════════════════════════════════════════
# LOOKUP TABLES
# ═══════════════════════════════════════════════════════════
H_TABLE = {0:0, 1:50, 2:100, 3:200, 4:300, 5:600, 6:1000, 7:1500, 8:2000, 9:None}

# Extended Visibility Table (from FM-12 SYNOP Code)
VISIBILITY_TABLE = {
    # Codes 00-50: 0.0 to 5.0 km
    0: 0.0, 1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4, 5: 0.5, 6: 0.6, 7: 0.7, 8: 0.8, 9: 0.9,
    10: 1.0, 11: 1.1, 12: 1.2, 13: 1.3, 14: 1.4, 15: 1.5, 16: 1.6, 17: 1.7, 18: 1.8, 19: 1.9,
    20: 2.0, 21: 2.1, 22: 2.2, 23: 2.3, 24: 2.4, 25: 2.5, 26: 2.6, 27: 2.7, 28: 2.8, 29: 2.9,
    30: 3.0, 31: 3.1, 32: 3.2, 33: 3.3, 34: 3.4, 35: 3.5, 36: 3.6, 37: 3.7, 38: 3.8, 39: 3.9,
    40: 4.0, 41: 4.1, 42: 4.2, 43: 4.3, 44: 4.4, 45: 4.5, 46: 4.6, 47: 4.7, 48: 4.8, 49: 4.9,
    50: 5.0,
    # Codes 51-80: 5.5 to 30+ km
    51: 5.5, 52: 6.0, 53: 6.5, 54: 7.0, 55: 7.5, 56: 8.0, 57: 8.5, 58: 9.0, 59: 9.5,
    60: 10.0, 61: 11.0, 62: 12.0, 63: 13.0, 64: 14.0, 65: 15.0, 66: 16.0, 67: 17.0, 68: 18.0, 69: 19.0,
    70: 20.0, 71: 22.0, 72: 24.0, 73: 26.0, 74: 28.0,
    # Codes 75-80: Not used (reserved)
    75: None, 76: None, 77: None, 78: None, 79: None, 80: None,
    # Codes 81-88: 35-70 km
    81: 35.0, 82: 40.0, 83: 45.0, 84: 50.0, 85: 55.0, 86: 60.0, 87: 65.0, 88: 70.0,
    # Codes 89-99: Special meanings (extreme visibility/obstruction)
    89: 70.0,          # > 70 km (Greater than 70 km)
    90: 0.05,          # < 50 m (Less than 50 m)
    91: 0.05,          # 50 m
    92: 0.05,          # 50 m
    93: 0.26,          # 260 m
    94: 0.5,           # 500 m
    95: 1.0,           # 1000 m (1 km)
    96: 4.0,           # 4000 m (4 km)
    97: 10.0,          # 10 kms (10 km)
    98: 20.0,          # 20 kms (20 km)
    99: 50.0,          # 50 kms or more (≥50 km)
}

def decode_visibility(vv: int) -> Optional[float]:
    """Decode visibility from VV code using extended visibility table."""
    return VISIBILITY_TABLE.get(vv, None)

WW_DESC = {
    **{i: "Cloud development not observed / fair weather" for i in range(0,4)},
    4: "Smoke/haze", 5: "Haze", 6: "Dust/sand raised", 7: "Dust/sandstorm",
    8: "Dust/sand whirls", 9: "Dust/sandstorm (severe)",
    10: "Mist", 11: "Patches of shallow fog", 12: "Continuous shallow fog",
    13: "Lightning visible, no thunder", 14: "Precipitation not reaching ground",
    15: "Distant precipitation reaching ground", 16: "Precipitation near station",
    17: "Thunderstorm without precipitation", 18: "Squalls", 19: "Funnel cloud(s)",
    20: "Drizzle (not freezing, intermittent)", 21: "Rain (not freezing, intermittent)",
    22: "Snow (intermittent)", 23: "Rain and snow (intermittent)",
    24: "Freezing drizzle or rain", 25: "Shower(s) of rain",
    26: "Shower(s) of snow/rain-snow", 27: "Shower(s) of hail",
    28: "Fog or ice fog", 29: "Thunderstorm (past hour)",
    30: "Slight/moderate duststorm (decreasing)", 31: "Slight/moderate duststorm (no change)",
    32: "Slight/moderate duststorm (increasing)", 33: "Severe duststorm (decreasing)",
    34: "Severe duststorm (no change)", 35: "Severe duststorm (increasing)",
    40: "Fog at distance", 41: "Fog in patches", 42: "Fog (sky visible, thinning)",
    43: "Fog (sky obscured, thinning)", 44: "Fog (sky visible, no change)",
    45: "Fog (sky obscured, no change)", 46: "Fog (sky visible, thickening)",
    47: "Fog (sky obscured, thickening)", 48: "Fog depositing rime (sky visible)",
    49: "Fog depositing rime (sky obscured)",
    50: "Light intermittent drizzle", 51: "Light continuous drizzle",
    53: "Moderate continuous drizzle", 55: "Heavy continuous drizzle",
    60: "Light intermittent rain", 61: "Light continuous rain",
    63: "Moderate continuous rain", 65: "Heavy continuous rain",
    71: "Light intermittent snow", 73: "Moderate continuous snow",
    75: "Heavy continuous snow",
    80: "Slight rain shower(s)", 81: "Moderate/heavy rain shower(s)",
    82: "Violent rain shower(s)", 83: "Slight rain-and-snow shower(s)",
    84: "Moderate/heavy rain-and-snow shower(s)",
    85: "Slight snow shower(s)", 86: "Moderate/heavy snow shower(s)",
    87: "Slight hail shower(s)", 88: "Moderate/heavy hail shower(s)",
    89: "Slight hail shower(s) without thunder", 90: "Moderate/heavy hail without thunder",
    91: "Slight rain — thunderstorm in past hour",
    92: "Moderate/heavy rain — thunderstorm in past hour",
    93: "Slight snow/rain-snow — thunderstorm in past hour",
    94: "Moderate/heavy snow — thunderstorm in past hour",
    95: "Thunderstorm — slight/moderate (TS)",
    96: "Thunderstorm with hail (TSGR)",
    97: "Heavy thunderstorm (TS)", 98: "Thunderstorm with dust/sandstorm",
    99: "Heavy thunderstorm with large hail (TSRA)",
}
THUNDERSTORM_CODES = {17, 29} | set(range(91, 100))
TSRA_CODES         = {91, 92, 93, 94, 95, 96, 97, 98, 99}

CL_TABLE = {0:"No low cloud",1:"Cu (fair weather)",2:"Cu (towering/mediocris)",
            3:"Cb (no anvil)",4:"Sc (from Cu spreading)",5:"Sc (other)",
            6:"St or FrSt",7:"FrSt/FrCu (bad weather)",
            8:"Cu and Sc (different levels)",9:"Cb (anvil)","/":"Unknown"}
CM_TABLE = {0:"No medium cloud",1:"As (thin)",2:"As (thick)/Ns",
            3:"Ac (thin, single layer)",4:"Ac patches (changing)",
            5:"Ac (semi-transparent, bands)",6:"Ac from Cb",
            7:"Ac (double layer)",8:"Ac (turreted/castellanus)",
            9:"Ac (chaotic sky)","/":"Unknown"}
CH_TABLE = {0:"No high cloud",1:"Ci (filaments)",2:"Dense Ci",
            3:"Ci (anvil remnant)",4:"Ci/Cs (increasing)",
            5:"Ci/Cs (not increasing, <45°)",6:"Ci/Cs (>45°)",
            7:"Cs (entire sky)",8:"Cs (not entire sky)",9:"Cc","/":"Unknown"}

COVER_MAP = {0:"Clear (0/8)",1:"1/8",2:"2/8",3:"3/8",
             4:"Half covered (4/8)",5:"5/8",6:"6/8",7:"7/8",
             8:"Overcast (8/8)",9:"Sky obscured"}

WIND_DIR_COMPASS = {
    0:"Variable/Calm", 36:"N", 45:"NE", 54:"NE",
    63:"ENE", 72:"E", 90:"E", 108:"ESE", 126:"SE",
    135:"SE", 144:"SE", 162:"SSE", 180:"S",
    198:"SSW", 216:"SW", 225:"SW", 234:"SW",
    252:"WSW", 270:"W", 288:"WNW", 306:"NW",
    315:"NW", 324:"NW", 342:"NNW", 360:"N",
}

def deg_to_compass(deg: int) -> str:
    if deg == 0: return "Variable/Calm"
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    idx = round(deg / 22.5) % 16
    return dirs[idx]

def rh_from_t_td(t: float, td: float) -> float:
    a, b = 17.625, 243.04
    rh = 100.0 * math.exp((a*td/(b+td)) - (a*t/(b+t)))
    return round(min(rh, 100.0), 1)

# ═══════════════════════════════════════════════════════════
# CORE DECODER
# ═══════════════════════════════════════════════════════════
def decode_synop(raw_message: str) -> SynopData:
    data  = SynopData()
    text  = raw_message.upper().replace('\n', ' ').replace('=', '').strip()
    tokens = text.split()
    data.raw_groups = tokens
    idx   = 0

    def peek():  return tokens[idx] if idx < len(tokens) else None
    def consume():
        nonlocal idx
        t = tokens[idx]; idx += 1; return t

    # ── Section 0: AAXX YYGGiw ──────────────────────────────
    while idx < len(tokens) and tokens[idx] != 'AAXX':
        idx += 1
    if idx >= len(tokens):
        data.warnings.append("AAXX header not found — check input.")
        return data
    consume()  # AAXX

    if idx < len(tokens):
        yyggi = consume()
        if len(yyggi) == 5:
            try:
                data.day      = int(yyggi[0:2])  # 01-31: day of month
                data.utc_hour = int(yyggi[2:4])  # 00-23: time in GMT (hours)
                iw            = int(yyggi[4])     # 0,1=m/s or 3,4=knots
                data.wind_unit = 'knots' if iw in (3, 4) else 'm/s'
            except: data.warnings.append(f"YYGGiw parse error: {yyggi}")

    # ── Station ID ───────────────────────────────────────────
    if idx < len(tokens):
        data.station_id = consume()

    # ── Group iR ix h VV ────────────────────────────────────
    # Format: iR(1) + ix(1) + h(1) + V(1) + V(1) = 5 digits
    # iR: Precipitation included (0-9)
    # ix: Type of station (0-9)
    # h: Cloud base height (0-9)
    # VV: Visibility code (00-99, as 2 digits)
    if idx < len(tokens) and re.match(r'^\d{5}$', tokens[idx]):
        g = consume()
        try:
            iR = int(g[0])      # Precipitation indicator
            ix = int(g[1])      # Type of station
            h = int(g[2])       # Cloud base height code
            VV = int(g[3:5])    # Visibility code (2 digits: positions 3-4)
            
            data.precip_included = iR in (1, 2)
            ix_map = {1:"Manned (all groups)",2:"Manned (sec 3 omitted)",
                      3:"Manned (no precip)",4:"Auto (all)",
                      5:"Auto (no precip)",6:"Auto (no precip/cloud)",7:"Auto (full)"}
            data.station_type        = ix_map.get(ix, f"Code {ix}")
            data.cloud_base_height_m = H_TABLE.get(h)
            data.visibility_km       = decode_visibility(VV)
            
        except Exception as e: data.warnings.append(f"iR ix h VV: {e}")

    # ── Group Nddff ──────────────────────────────────────────
    if idx < len(tokens) and re.match(r'^\d{5}$', tokens[idx]):
        g = consume()
        try:
            n, dd, ff = int(g[0]), int(g[1:3]), int(g[3:5])
            data.cloud_cover_oktas  = n
            data.wind_direction_deg = dd * 10 if dd not in (0, 99) else (0 if dd==0 else None)
            data.wind_speed         = float(ff)
            data.wind_speed_unit    = data.wind_unit or 'knots'
        except Exception as e: data.warnings.append(f"Nddff: {e}")

    # ── Group 1SnTTT ─────────────────────────────────────────
    if idx < len(tokens) and re.match(r'^1\d{4}$', tokens[idx]):
        g = consume()
        try:
            sn  = int(g[1]); ttt = int(g[2:5])
            data.temperature_c = (-ttt if sn == 1 else ttt) / 10.0
        except Exception as e: data.warnings.append(f"1SnTTT: {e}")

    # ── Group 2SnTdTd ────────────────────────────────────────
    if idx < len(tokens) and re.match(r'^2\d{4}$', tokens[idx]):
        g = consume()
        try:
            sn = int(g[1]); tdt = int(g[2:5])
            if sn == 9:
                data.rel_humidity_pct = tdt / 10.0 if tdt > 100 else float(tdt)
            else:
                td = (-tdt if sn == 1 else tdt) / 10.0
                data.dewpoint_c = td
                if data.temperature_c is not None:
                    data.rel_humidity_pct = rh_from_t_td(data.temperature_c, td)
        except Exception as e: data.warnings.append(f"2SnTdTd: {e}")

    # ── Group 3PPPP (station pressure) ───────────────────────
    if idx < len(tokens) and re.match(r'^3\d{4}$', tokens[idx]):
        g = consume()
        try:
            p = int(g[1:5]) / 10.0
            data.pressure_station_hpa = p + (1000.0 if p < 500 else 0)
        except Exception as e: data.warnings.append(f"3PPPP: {e}")

    # ── Group 4PPPP (MSL pressure) ───────────────────────────
    if idx < len(tokens) and re.match(r'^4\d{4}$', tokens[idx]):
        g = consume()
        try:
            p = int(g[1:5]) / 10.0
            data.pressure_msl_hpa = p + (1000.0 if p < 500 else 0)
        except Exception as e: data.warnings.append(f"4PPPP: {e}")

    # Skip groups 5 & 6
    while idx < len(tokens) and re.match(r'^[56]\d{4}$', tokens[idx]):
        consume()

    # ── Group 7wwW1W2 ────────────────────────────────────────
    if idx < len(tokens) and re.match(r'^7\d{4}$', tokens[idx]):
        g = consume()
        try:
            ww, w1, w2 = int(g[1:3]), int(g[3]), int(g[4])
            data.present_weather_code = ww
            data.present_weather      = WW_DESC.get(ww, f"Code {ww}")
            data.thunderstorm         = ww in THUNDERSTORM_CODES
            data.thunderstorm_rain    = ww in TSRA_CODES
            data.past_weather_1       = WW_DESC.get(w1 * 10, f"W1={w1}")
            data.past_weather_2       = WW_DESC.get(w2 * 10, f"W2={w2}")
        except Exception as e: data.warnings.append(f"7wwW1W2: {e}")

    # ── Group 8NhCLCMCH ──────────────────────────────────────
    if idx < len(tokens) and re.match(r'^8\d{4}$', tokens[idx]):
        g = consume()
        try:
            nh = int(g[1]); cl, cm, ch = g[2], g[3], g[4]
            data.low_cloud_cover = nh
            data.cloud_low_type  = CL_TABLE.get(int(cl) if cl.isdigit() else cl, cl)
            data.cloud_mid_type  = CM_TABLE.get(int(cm) if cm.isdigit() else cm, cm)
            data.cloud_high_type = CH_TABLE.get(int(ch) if ch.isdigit() else ch, ch)
        except Exception as e: data.warnings.append(f"8NhCLCMCH: {e}")

    # ── Section 3 (after 333) ────────────────────────────────
    while idx < len(tokens) and tokens[idx] != '333':
        idx += 1
    if idx < len(tokens) and tokens[idx] == '333':
        idx += 1
        while idx < len(tokens) and tokens[idx] != '555':
            g = tokens[idx]
            if re.match(r'^1\d{4}$', g):
                try:
                    sn = int(g[1]); tx = int(g[2:5]) / 10.0
                    data.max_temperature_c = -tx if sn == 1 else tx
                except Exception as e: data.warnings.append(f"Sec3 Tmax: {e}")
            elif re.match(r'^2\d{4}$', g):
                try:
                    sn = int(g[1]); tn = int(g[2:5]) / 10.0
                    data.min_temperature_c = -tn if sn == 1 else tn
                except Exception as e: data.warnings.append(f"Sec3 Tmin: {e}")
            idx += 1

    return data

# ═══════════════════════════════════════════════════════════
# DISPLAY FUNCTIONS
# ═══════════════════════════════════════════════════════════
def fmt(val, unit="", na="N/A", decimals=1):
    if val is None: return c(na, DIM)
    return f"{val:.{decimals}f} {unit}".strip() if isinstance(val, float) else f"{val} {unit}".strip()

def print_full_report(data: SynopData):
    os.system('cls' if os.name == 'nt' else 'clear')
    ts  = "YES ⚡" if data.thunderstorm      else "No"
    tsr = "YES ⛈ " if data.thunderstorm_rain else "No"
    compass = deg_to_compass(data.wind_direction_deg) if data.wind_direction_deg is not None else "—"

    print(f"\n{BOLD}{CYAN}╔{'═'*56}╗{RESET}")
    print(f"{BOLD}{CYAN}║{'IMD SYNOP DECODED REPORT':^56}║{RESET}")
    print(f"{BOLD}{CYAN}╚{'═'*56}╝{RESET}")

    # Station Info
    print(f"\n{BOLD}{BLUE}  🏢  STATION INFO{RESET}")
    sep()
    print(f"  {'Station ID':<22}: {c(str(data.station_id), WHITE)}")
    print(f"  {'Observation Day':<22}: {fmt(data.day)} (day of month)")
    time_str = f"{data.utc_hour:02d}:00 GMT" if data.utc_hour is not None else "N/A"
    print(f"  {'Observation Time':<22}: {c(time_str, WHITE)}")
    print(f"  {'Wind Unit':<22}: {fmt(data.wind_unit)}")
    print(f"  {'Station Type':<22}: {fmt(data.station_type)}")

    # Temperature
    print(f"\n{BOLD}{RED}  🌡  TEMPERATURE{RESET}")
    sep()
    print(f"  {'Temperature':<22}: {c(fmt(data.temperature_c, '°C'), YELLOW)}")
    print(f"  {'Dew Point':<22}: {c(fmt(data.dewpoint_c, '°C'), CYAN)}")
    print(f"  {'Max Temperature':<22}: {c(fmt(data.max_temperature_c, '°C'), RED)}")
    print(f"  {'Min Temperature':<22}: {c(fmt(data.min_temperature_c, '°C'), BLUE)}")

    # Humidity
    print(f"\n{BOLD}{CYAN}  💧  HUMIDITY{RESET}")
    sep()
    rh = data.rel_humidity_pct
    rh_col = GREEN if rh and rh >= 60 else (YELLOW if rh and rh >= 40 else RED)
    print(f"  {'Relative Humidity':<22}: {c(fmt(rh, '%'), rh_col)}")

    # Cloud Cover
    print(f"\n{BOLD}{WHITE}  ☁  CLOUD COVER{RESET}")
    sep()
    print(f"  {'Total Cover (N)':<22}: {c(fmt(data.cloud_cover_oktas, 'oktas'), WHITE)}")
    if data.cloud_cover_oktas is not None:
        print(f"  {'  Description':<22}: {c(COVER_MAP.get(data.cloud_cover_oktas,'?'), DIM)}")
    print(f"  {'Low Cloud Amount':<22}: {fmt(data.low_cloud_cover, 'oktas')}")
    print(f"  {'Low Cloud Type':<22}: {fmt(data.cloud_low_type)}")
    print(f"  {'Medium Cloud Type':<22}: {fmt(data.cloud_mid_type)}")
    print(f"  {'High Cloud Type':<22}: {fmt(data.cloud_high_type)}")
    print(f"  {'Cloud Base Height':<22}: {fmt(data.cloud_base_height_m, 'm', decimals=0)}")

    # Wind
    print(f"\n{BOLD}{GREEN}  🌬  WIND{RESET}")
    sep()
    print(f"  {'Wind Direction':<22}: {c(fmt(data.wind_direction_deg, '°'), GREEN)}  ({c(compass, CYAN)})")
    print(f"  {'Wind Speed':<22}: {c(fmt(data.wind_speed, data.wind_speed_unit or ''), GREEN)}")

    # Visibility & Pressure
    print(f"\n{BOLD}{MAGENTA}  👁  VISIBILITY & PRESSURE{RESET}")
    sep()
    vis = round(data.visibility_km, 2) if data.visibility_km is not None else None
    print(f"  {'Visibility':<22}: {fmt(vis, 'km')}")
    print(f"  {'Station Pressure':<22}: {fmt(data.pressure_station_hpa, 'hPa')}")
    print(f"  {'MSL Pressure':<22}: {fmt(data.pressure_msl_hpa, 'hPa')}")

    # Present Weather
    print(f"\n{BOLD}{YELLOW}  ⛅  PRESENT WEATHER{RESET}")
    sep()
    if data.present_weather_code is not None:
        print(f"  {'ww Code':<22}: {data.present_weather_code}")
        print(f"  {'Description':<22}: {c(str(data.present_weather), YELLOW)}")
    else:
        print(f"  {'Present Weather':<22}: {c('N/A (no group 7 in message)', DIM)}")
    print(f"  {'Thunderstorm (TS)':<22}: {c(ts,  GREEN if not data.thunderstorm else YELLOW)}")
    print(f"  {'TS + Rain (TSRA)':<22}: {c(tsr, GREEN if not data.thunderstorm_rain else RED)}")

    # Warnings
    if data.warnings:
        print(f"\n{BOLD}{YELLOW}  ⚠  PARSE WARNINGS{RESET}")
        sep()
        for w in data.warnings:
            warn(w)

    print(f"\n{c('═'*58, DIM)}\n")

def print_specific(data: SynopData, choice: str):
    """Print only the requested parameter group."""
    compass = deg_to_compass(data.wind_direction_deg) if data.wind_direction_deg is not None else "—"
    sep()
    if choice == '1':
        header("🌡  TEMPERATURE")
        sep()
        print(f"  Temperature     : {c(fmt(data.temperature_c,'°C'), YELLOW)}")
        print(f"  Dew Point       : {c(fmt(data.dewpoint_c,'°C'), CYAN)}")
        print(f"  Max Temperature : {c(fmt(data.max_temperature_c,'°C'), RED)}")
        print(f"  Min Temperature : {c(fmt(data.min_temperature_c,'°C'), BLUE)}")
    elif choice == '2':
        header("💧  HUMIDITY")
        sep()
        print(f"  Relative Humidity : {c(fmt(data.rel_humidity_pct,'%'), CYAN)}")
    elif choice == '3':
        header("☁  CLOUD COVER")
        sep()
        print(f"  Total Cover (N)   : {fmt(data.cloud_cover_oktas,'oktas')}")
        if data.cloud_cover_oktas is not None:
            print(f"  Description       : {COVER_MAP.get(data.cloud_cover_oktas,'?')}")
        print(f"  Low Cloud Amount  : {fmt(data.low_cloud_cover,'oktas')}")
        print(f"  Low Cloud Type    : {fmt(data.cloud_low_type)}")
        print(f"  Medium Cloud Type : {fmt(data.cloud_mid_type)}")
        print(f"  High Cloud Type   : {fmt(data.cloud_high_type)}")
        print(f"  Cloud Base Height : {fmt(data.cloud_base_height_m,'m',decimals=0)}")
    elif choice == '4':
        header("🌬  WIND")
        sep()
        print(f"  Wind Direction : {c(fmt(data.wind_direction_deg,'°'), GREEN)} ({c(compass, CYAN)})")
        print(f"  Wind Speed     : {c(fmt(data.wind_speed, data.wind_speed_unit or ''), GREEN)}")
    elif choice == '5':
        header("⛅  PRESENT WEATHER")
        sep()
        if data.present_weather_code is not None:
            print(f"  ww Code      : {data.present_weather_code}")
            print(f"  Description  : {c(str(data.present_weather), YELLOW)}")
        else:
            print(f"  Present Weather : {c('N/A', DIM)}")
        ts  = "YES ⚡" if data.thunderstorm      else "No"
        tsr = "YES ⛈ " if data.thunderstorm_rain else "No"
        print(f"  TS           : {c(ts, YELLOW if data.thunderstorm else GREEN)}")
        print(f"  TSRA         : {c(tsr, RED if data.thunderstorm_rain else GREEN)}")
    elif choice == '6':
        header("👁  VISIBILITY & PRESSURE")
        sep()
        vis = round(data.visibility_km, 2) if data.visibility_km is not None else None
        print(f"  Visibility       : {fmt(vis,'km')}")
        print(f"  Station Pressure : {fmt(data.pressure_station_hpa,'hPa')}")
        print(f"  MSL Pressure     : {fmt(data.pressure_msl_hpa,'hPa')}")
    sep()

# ═══════════════════════════════════════════════════════════
# EXPORT HELPERS
# ═══════════════════════════════════════════════════════════
def export_json(data: SynopData, filename: str):
    d = {k: v for k, v in data.__dict__.items() if k not in ('raw_groups',)}
    with open(filename, 'w') as f:
        json.dump(d, f, indent=2, default=str)
    ok(f"Exported to {c(filename, CYAN)}")

def export_csv(data: SynopData, filename: str):
    time_str = f"{data.utc_hour:02d}:00 GMT" if data.utc_hour is not None else None
    rows = [
        ("Station ID", data.station_id),
        ("Day (UTC)", data.day),
        ("Hour (GMT)", time_str),
        ("Wind Unit", data.wind_unit),
        ("Temperature (°C)", data.temperature_c),
        ("Dew Point (°C)", data.dewpoint_c),
        ("Max Temperature (°C)", data.max_temperature_c),
        ("Min Temperature (°C)", data.min_temperature_c),
        ("Relative Humidity (%)", data.rel_humidity_pct),
        ("Cloud Cover (oktas)", data.cloud_cover_oktas),
        ("Low Cloud Cover (oktas)", data.low_cloud_cover),
        ("Low Cloud Type", data.cloud_low_type),
        ("Medium Cloud Type", data.cloud_mid_type),
        ("High Cloud Type", data.cloud_high_type),
        ("Cloud Base Height (m)", data.cloud_base_height_m),
        ("Wind Direction (°)", data.wind_direction_deg),
        ("Wind Speed", data.wind_speed),
        ("Wind Speed Unit", data.wind_speed_unit),
        ("Visibility (km)", data.visibility_km),
        ("Station Pressure (hPa)", data.pressure_station_hpa),
        ("MSL Pressure (hPa)", data.pressure_msl_hpa),
        ("Present Weather Code", data.present_weather_code),
        ("Present Weather", data.present_weather),
        ("Thunderstorm (TS)", data.thunderstorm),
        ("TS with Rain (TSRA)", data.thunderstorm_rain),
    ]
    with open(filename, 'w') as f:
        f.write("Parameter,Value\n")
        for name, val in rows:
            f.write(f'"{name}","{val}"\n')
    ok(f"Exported to {c(filename, CYAN)}")

def export_txt(data: SynopData, filename: str):
    compass = deg_to_compass(data.wind_direction_deg) if data.wind_direction_deg is not None else "—"
    time_str = f"{data.utc_hour:02d}:00 GMT" if data.utc_hour is not None else "N/A"
    lines = [
        "=" * 55,
        "  IMD SYNOP DECODED REPORT",
        f"  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 55,
        f"  Station ID         : {data.station_id}",
        f"  Day (day of month) : {data.day}",
        f"  Hour (GMT)         : {time_str}",
        "-" * 55,
        f"  Temperature        : {data.temperature_c} °C",
        f"  Dew Point          : {data.dewpoint_c} °C",
        f"  Max Temperature    : {data.max_temperature_c} °C",
        f"  Min Temperature    : {data.min_temperature_c} °C",
        f"  Relative Humidity  : {data.rel_humidity_pct} %",
        "-" * 55,
        f"  Cloud Cover (N)    : {data.cloud_cover_oktas} oktas  [{COVER_MAP.get(data.cloud_cover_oktas,'?') if data.cloud_cover_oktas is not None else 'N/A'}]",
        f"  Low Cloud          : {data.cloud_low_type}",
        f"  Medium Cloud       : {data.cloud_mid_type}",
        f"  High Cloud         : {data.cloud_high_type}",
        f"  Cloud Base Height  : {data.cloud_base_height_m} m",
        "-" * 55,
        f"  Wind Direction     : {data.wind_direction_deg}° ({compass})",
        f"  Wind Speed         : {data.wind_speed} {data.wind_speed_unit}",
        f"  Visibility         : {round(data.visibility_km,2) if data.visibility_km else 'N/A'} km",
        f"  Station Pressure   : {data.pressure_station_hpa} hPa",
        f"  MSL Pressure       : {data.pressure_msl_hpa} hPa",
        "-" * 55,
        f"  Present Weather    : {data.present_weather} (code {data.present_weather_code})",
        f"  Thunderstorm (TS)  : {'YES' if data.thunderstorm else 'No'}",
        f"  TS with Rain(TSRA) : {'YES' if data.thunderstorm_rain else 'No'}",
        "=" * 55,
    ]
    with open(filename, 'w') as f:
        f.write('\n'.join(lines))
    ok(f"Exported to {c(filename, CYAN)}")

# ═══════════════════════════════════════════════════════════
# INPUT HELPERS
# ═══════════════════════════════════════════════════════════
def get_synop_input() -> str:
    """Prompt user for SYNOP message (multi-line until blank line or '=')."""
    print(f"\n{c('Enter your SYNOP message below.', CYAN)}")
    print(f"{c('  • You can paste the entire message (multi-line).', DIM)}")
    print(f"{c('  • Press ENTER on a blank line when done.', DIM)}")
    print(f"{c('  • Or type = at the end of your message.', DIM)}\n")
    lines = []
    while True:
        try:
            line = input(f"  {CYAN}>{RESET} ")
        except EOFError:
            break
        if line.strip() == '' and lines:
            break
        if line.strip().endswith('='):
            lines.append(line.replace('=', ''))
            break
        lines.append(line)
    return '\n'.join(lines)

def prompt(msg, colour=CYAN):
    return input(f"\n{colour}{msg}{RESET} ").strip()

def pause():
    input(f"\n  {DIM}Press ENTER to continue...{RESET}")

# ═══════════════════════════════════════════════════════════
# SYNOP CODE HANDLING (FILE LIST MODE)
# ═══════════════════════════════════════════════════════════
def extract_synop_codes(text: str) -> list[str]:
    """Extract all SYNOP codes (starting with AAXX) from text."""
    codes = []
    # Split by whitespace and find tokens starting with AAXX
    tokens = text.split()
    current_code = []
    
    for token in tokens:
        if token.upper().startswith('AAXX'):
            if current_code:
                codes.append(' '.join(current_code))
            current_code = [token]
        elif current_code:
            current_code.append(token)
        # Stop at 333 or 555 (end markers)
        if token in ['333', '555'] and current_code:
            codes.append(' '.join(current_code))
            current_code = []
    
    if current_code:
        codes.append(' '.join(current_code))
    
    return codes

def validate_vomm_filename(filename: str) -> tuple[bool, str]:
    """Validate VOMM filename format and check file exists.
    Format: VOMM + YYYYMMDD (e.g., VOMM20260507)
    Returns: (is_valid, error_message)
    """
    base_path = r"D:\IMD INTERNSHIP"
    
    # Check basic format
    pattern = r'^VOMM(\d{4})(\d{2})(\d{2})$'
    match = re.match(pattern, filename)
    
    if not match:
        return False, f"Invalid format. Expected: VOMM + YYYYMMDD (e.g., VOMM20260507)"
    
    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
    
    # Validate date components
    if month < 1 or month > 12:
        return False, f"Invalid month: {month}. Must be 01-12"
    
    if day < 1 or day > 31:
        return False, f"Invalid day: {day}. Must be 01-31"
    
    # Check if it's a valid date
    try:
        datetime.datetime(year, month, day)
    except ValueError as e:
        return False, f"Invalid date: {e}"
    
    # Check if file exists
    filepath = os.path.join(base_path, f"{filename}.txt")
    if not os.path.isfile(filepath):
        return False, f"File not found: {filepath}"
    
    return True, ""

def decode_synop_list(synop_codes: list[str]) -> list[tuple[str, SynopData]]:
    """Decode a list of SYNOP codes. Returns list of (raw, decoded_data) tuples."""
    results = []
    for code in synop_codes:
        data = decode_synop(code)
        results.append((code, data))
    return results

def filter_by_station(results: list[tuple[str, SynopData]], station_id: str) -> list[tuple[str, SynopData]]:
    """Filter decoded results by station ID."""
    return [(raw, data) for raw, data in results if data.station_id == station_id]

def menu_synop_list_options(synop_codes: list[str]):
    """Menu for handling SYNOP code list from file."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{BOLD}SYNOP CODE LIST — Found {len(synop_codes)} code(s){RESET}")
        sep()
        print(f"  {GREEN}1{RESET}. Decode fully (all codes)")
        print(f"  {GREEN}2{RESET}. Enter station number and decode all codes for it")
        print(f"  {GREEN}3{RESET}. Load from VOMM file (format: VOMM20260507)")
        print(f"  {RED}0{RESET}. Back to main menu")
        sep()
        choice = prompt("Enter choice [0-3] →")
        
        if choice == '1':
            menu_decode_all_synops(synop_codes)
        elif choice == '2':
            menu_decode_by_station(synop_codes)
        elif choice == '3':
            menu_decode_from_vomm()
        elif choice == '0':
            break
        else:
            err("Invalid choice. Please try again.")
            pause()

def display_decoded_results_summary(results: list[tuple[str, SynopData]]):
    """Display all decoded results in a navigable summary view with export option."""
    if not results:
        err("No results to display.")
        pause()
        return
    
    current_idx = 0
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        raw, data = results[current_idx]
        
        print(f"\n{BOLD}DECODED RESULTS — Entry {current_idx + 1}/{len(results)}{RESET}")
        sep()
        
        # Display current report
        print_full_report(data)
        
        # Navigation prompt
        if len(results) > 1:
            nav_msg = ""
            if current_idx > 0:
                nav_msg += f"{GREEN}[P]{RESET}revious  "
            if current_idx < len(results) - 1:
                nav_msg += f"{GREEN}[N]{RESET}ext  "
            nav_msg += f"{GREEN}[S]{RESET}ave all to JSON  "
            nav_msg += f"{RED}[E]{RESET}xit to menu"
            
            print(f"  {nav_msg}")
            choice = input(f"\n{CYAN}Enter choice (P/N/S/E) →{RESET} ").strip().upper()
            
            if choice == 'N':
                if current_idx < len(results) - 1:
                    current_idx += 1
                else:
                    warn("This is the end. No more codes to display.")
                    pause()
            elif choice == 'P':
                if current_idx > 0:
                    current_idx -= 1
                else:
                    warn("This is the beginning. No previous codes.")
                    pause()
            elif choice == 'S':
                export_all_results_menu(results)
            elif choice == 'E':
                break
            else:
                continue
        else:
            nav_msg = f"{GREEN}[S]{RESET}ave to JSON  {RED}[E]{RESET}xit to menu"
            print(f"  {nav_msg}")
            choice = input(f"\n{CYAN}Enter choice (S/E) →{RESET} ").strip().upper()
            
            if choice == 'S':
                export_all_results_menu(results)
            elif choice == 'E':
                break
            else:
                continue

def export_all_results_menu(results: list[tuple[str, SynopData]]):
    """Export all decoded results to JSON/CSV/TXT."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{BOLD}EXPORT ALL RESULTS{RESET}")
    sep()
    print(f"  {GREEN}1{RESET}. Export as JSON")
    print(f"  {GREEN}2{RESET}. Export as CSV")
    print(f"  {GREEN}3{RESET}. Export as Plain Text")
    print(f"  {RED}0{RESET}. Cancel")
    sep()
    choice = prompt("Enter format [0-3] →")
    if choice == '0': return

    ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"synop_batch_{len(results)}codes_{ts_str}"
    name = prompt(f"Filename (without extension) [default: {default_name}] →") or default_name

    if choice == '1':
        export_all_json(results, name + ".json")
    elif choice == '2':
        export_all_csv(results, name + ".csv")
    elif choice == '3':
        export_all_txt(results, name + ".txt")
    else:
        err("Invalid choice.")
    
    pause()

def export_all_json(results: list[tuple[str, SynopData]], filename: str):
    """Export all decoded results as JSON."""
    all_data = []
    for raw, data in results:
        all_data.append({
            "raw_message": raw,
            "decoded_data": {k: v for k, v in data.__dict__.items() if k not in ('raw_groups',)}
        })
    
    with open(filename, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)
    ok(f"Exported {len(results)} result(s) to {c(filename, CYAN)}")

def export_all_csv(results: list[tuple[str, SynopData]], filename: str):
    """Export all decoded results as CSV."""
    import csv
    
    if not results:
        return
    
    # Get all possible keys from all results
    all_keys = set()
    for _, data in results:
        all_keys.update(data.__dict__.keys())
    all_keys.discard('raw_groups')
    all_keys.discard('warnings')
    all_keys = sorted(list(all_keys))
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['raw_message'] + all_keys)
        writer.writeheader()
        
        for raw, data in results:
            row = {'raw_message': raw}
            for key in all_keys:
                row[key] = getattr(data, key, None)
            writer.writerow(row)
    
    ok(f"Exported {len(results)} result(s) to {c(filename, CYAN)}")

def export_all_txt(results: list[tuple[str, SynopData]], filename: str):
    """Export all decoded results as Plain Text."""
    compass_map = {}
    
    with open(filename, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write(f"  IMD SYNOP BATCH DECODED REPORT\n")
        f.write(f"  Total Codes: {len(results)}\n")
        f.write(f"  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        
        for idx, (raw, data) in enumerate(results, 1):
            compass = deg_to_compass(data.wind_direction_deg) if data.wind_direction_deg is not None else "—"
            time_str = f"{data.utc_hour:02d}:00 GMT" if data.utc_hour is not None else "N/A"
            
            f.write(f"\n{'─' * 70}\n")
            f.write(f"ENTRY {idx}/{len(results)} — Station: {data.station_id}\n")
            f.write(f"{'─' * 70}\n\n")
            f.write(f"  Raw Message: {raw}\n\n")
            f.write(f"  Station Info:\n")
            f.write(f"    Station ID         : {data.station_id}\n")
            f.write(f"    Day (day of month) : {data.day}\n")
            f.write(f"    Hour (GMT)         : {time_str}\n")
            f.write(f"    Station Type       : {data.station_type}\n\n")
            f.write(f"  Temperature:\n")
            f.write(f"    Current            : {data.temperature_c} °C\n")
            f.write(f"    Dew Point          : {data.dewpoint_c} °C\n")
            f.write(f"    Max                : {data.max_temperature_c} °C\n")
            f.write(f"    Min                : {data.min_temperature_c} °C\n")
            f.write(f"    Relative Humidity  : {data.rel_humidity_pct} %\n\n")
            f.write(f"  Wind:\n")
            f.write(f"    Direction          : {data.wind_direction_deg}° ({compass})\n")
            f.write(f"    Speed              : {data.wind_speed} {data.wind_speed_unit}\n\n")
            f.write(f"  Clouds:\n")
            f.write(f"    Total Cover (N)    : {data.cloud_cover_oktas} oktas\n")
            f.write(f"    Low Cloud Type     : {data.cloud_low_type}\n")
            f.write(f"    Medium Cloud Type  : {data.cloud_mid_type}\n")
            f.write(f"    High Cloud Type    : {data.cloud_high_type}\n")
            f.write(f"    Base Height        : {data.cloud_base_height_m} m\n\n")
            f.write(f"  Visibility & Pressure:\n")
            f.write(f"    Visibility         : {round(data.visibility_km, 2) if data.visibility_km else 'N/A'} km\n")
            f.write(f"    Station Pressure   : {data.pressure_station_hpa} hPa\n")
            f.write(f"    MSL Pressure       : {data.pressure_msl_hpa} hPa\n\n")
            f.write(f"  Weather:\n")
            f.write(f"    Present            : {data.present_weather}\n")
            f.write(f"    Thunderstorm (TS)  : {'YES' if data.thunderstorm else 'No'}\n")
            f.write(f"    TS + Rain (TSRA)   : {'YES' if data.thunderstorm_rain else 'No'}\n")
            
            if data.warnings:
                f.write(f"\n  Warnings:\n")
                for w in data.warnings:
                    f.write(f"    • {w}\n")
        
        f.write(f"\n{'=' * 70}\n")
        f.write(f"END OF REPORT\n")
        f.write(f"{'=' * 70}\n")
    
    ok(f"Exported {len(results)} result(s) to {c(filename, CYAN)}")

def menu_decode_all_synops(synop_codes: list[str]):
    """Decode and display all SYNOP codes with full reports."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{BOLD}DECODING ALL SYNOP CODES{RESET}")
    sep()
    
    results = decode_synop_list(synop_codes)
    ok(f"Decoded {len(results)} code(s).")
    pause()
    
    # Add to session history
    for raw, data in results:
        SESSION_HISTORY.append((raw, data))
    
    # Display all results in navigable summary
    display_decoded_results_summary(results)


def menu_decode_by_station(synop_codes: list[str]):
    """Decode SYNOP codes by station number with full reports."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{BOLD}DECODE BY STATION NUMBER{RESET}")
    sep()
    
    # First pass: decode all and collect unique stations
    results = decode_synop_list(synop_codes)
    stations = set()
    for raw, data in results:
        if data.station_id:
            stations.add(data.station_id)
    
    if not stations:
        err("No valid station IDs found in the codes.")
        pause()
        return
    
    ok(f"Found {len(stations)} unique station(s): {', '.join(sorted(stations))}")
    
    station_id = prompt("Enter station number to decode →").strip()
    
    filtered = filter_by_station(results, station_id)
    
    if not filtered:
        err(f"No codes found for station: {station_id}")
        pause()
        return
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{BOLD}DECODING FOR STATION {station_id}{RESET}")
    sep()
    ok(f"Found {len(filtered)} code(s) for station {station_id}.")
    pause()
    
    # Add to session history
    for raw, data in filtered:
        SESSION_HISTORY.append((raw, data))
    
    # Display all results in navigable summary
    display_decoded_results_summary(filtered)


def menu_decode_from_vomm():
    """Load SYNOP codes from a VOMM file."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{BOLD}LOAD FROM VOMM FILE{RESET}")
    sep()
    info("Format: VOMM + YYYYMMDD (e.g., VOMM20260507)")
    
    filename = prompt("Enter filename (without .txt) →").strip()
    
    is_valid, error_msg = validate_vomm_filename(filename)
    
    if not is_valid:
        err(error_msg)
        pause()
        return
    
    # Load file
    filepath = os.path.join(r"D:\IMD INTERNSHIP", f"{filename}.txt")
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception as e:
        err(f"Error reading file: {e}")
        pause()
        return
    
    synop_codes = extract_synop_codes(content)
    
    if not synop_codes:
        warn("No SYNOP codes found in file.")
        pause()
        return
    
    ok(f"Loaded {len(synop_codes)} SYNOP code(s) from {filename}.txt")
    
    # Show submenu for this file
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{BOLD}VOMM FILE: {filename} — {len(synop_codes)} code(s){RESET}")
        sep()
        print(f"  {GREEN}1{RESET}. Decode fully (all codes)")
        print(f"  {GREEN}2{RESET}. Enter station number and decode all codes for it")
        print(f"  {RED}0{RESET}. Back")
        sep()
        choice = prompt("Enter choice [0-2] →")
        
        if choice == '1':
            menu_decode_all_synops(synop_codes)
        elif choice == '2':
            menu_decode_by_station(synop_codes)
        elif choice == '0':
            break
        else:
            err("Invalid choice.")

# ═══════════════════════════════════════════════════════════
# MAIN MENU SYSTEM
# ═══════════════════════════════════════════════════════════
SESSION_HISTORY: list[tuple[str, SynopData]] = []   # (raw_msg, data)

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    🌦   IMD SYNOP CODE DECODER  v2.0                     ║
║         FM-12 Surface Synoptic Observation               ║
║         India Meteorological Department                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")

def main_menu():
    while True:
        banner()
        print(f"  {BOLD}MAIN MENU{RESET}")
        sep()
        print(f"  {GREEN}1{RESET}. Decode a SYNOP message")
        print(f"  {GREEN}2{RESET}. Decode from a text file (with SYNOP code list options)")
        print(f"  {GREEN}3{RESET}. View session history")
        print(f"  {GREEN}4{RESET}. Help / Format guide")
        print(f"  {RED}0{RESET}. Exit")
        sep()
        choice = prompt("Enter choice [0-4] →")

        if   choice == '1': menu_decode_single()
        elif choice == '2': menu_decode_file()
        elif choice == '3': menu_history()
        elif choice == '4': menu_help()
        elif choice == '0':
            print(f"\n  {CYAN}Goodbye! Stay weather-aware! 🌤{RESET}\n")
            break
        else:
            err("Invalid choice. Please try again.")
            pause()

def menu_decode_single():
    raw = get_synop_input()
    if not raw.strip():
        err("No message entered.")
        pause(); return

    data = decode_synop(raw)
    SESSION_HISTORY.append((raw, data))
    results_menu(raw, data)

def menu_decode_file():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{BOLD}DECODE FROM TEXT FILE{RESET}")
    sep()
    info("Enter the filename (e.g., VOMM20260605.txt or synop_data.txt)")
    filename = prompt("Enter filename →").strip()
    
    # Construct full path
    base_path = r"D:\IMD INTERNSHIP"
    filepath = os.path.join(base_path, filename)
    
    if not os.path.isfile(filepath):
        err(f"File not found: {filepath}")
        pause()
        return

    with open(filepath) as f:
        content = f.read()

    # Extract SYNOP codes from file
    synop_codes = extract_synop_codes(content)
    
    if not synop_codes:
        err("No SYNOP codes found in file.")
        pause()
        return
    
    ok(f"Found {len(synop_codes)} SYNOP code(s).")
    
    # Show simplified options menu
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{BOLD}FILE: {filename} — {len(synop_codes)} code(s){RESET}")
        sep()
        print(f"  {GREEN}1{RESET}. Decode all codes")
        print(f"  {GREEN}2{RESET}. Filter by station number and decode")
        print(f"  {RED}0{RESET}. Back to main menu")
        sep()
        choice = prompt("Enter choice [0-2] →")
        
        if choice == '1':
            menu_decode_all_synops(synop_codes)
        elif choice == '2':
            menu_decode_by_station(synop_codes)
        elif choice == '0':
            break
        else:
            err("Invalid choice.")
            pause()



def results_menu(raw: str, data: SynopData):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{BOLD}RESULTS MENU  {DIM}— Station: {data.station_id}{RESET}")
        sep()
        print(f"  {GREEN}1{RESET}. Show FULL decoded report")
        print(f"  {GREEN}2{RESET}. Temperature only")
        print(f"  {GREEN}3{RESET}. Humidity only")
        print(f"  {GREEN}4{RESET}. Cloud cover only")
        print(f"  {GREEN}5{RESET}. Wind only")
        print(f"  {GREEN}6{RESET}. Present weather (TS / TSRA)")
        print(f"  {GREEN}7{RESET}. Visibility & Pressure")
        print(f"  {GREEN}8{RESET}. Export results")
        print(f"  {GREEN}9{RESET}. Show raw groups")
        print(f"  {RED}0{RESET}. Back to main menu")
        sep()
        choice = prompt("Enter choice [0-9] →")

        if choice == '1':
            print_full_report(data)
            pause()
        elif choice in ('2','3','4','5','6','7'):
            map_ = {'2':'1','3':'2','4':'3','5':'4','6':'5','7':'6'}
            print_specific(data, map_[choice])
            pause()
        elif choice == '8':
            export_menu(data)
        elif choice == '9':
            header("RAW SYNOP GROUPS")
            sep()
            print("  " + "  ".join(c(g, CYAN) for g in data.raw_groups))
            sep()
            pause()
        elif choice == '0':
            break
        else:
            err("Invalid choice.")

def export_menu(data: SynopData):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{BOLD}EXPORT RESULTS{RESET}")
    sep()
    print(f"  {GREEN}1{RESET}. Export as JSON")
    print(f"  {GREEN}2{RESET}. Export as CSV")
    print(f"  {GREEN}3{RESET}. Export as Plain Text")
    print(f"  {RED}0{RESET}. Cancel")
    sep()
    choice = prompt("Enter format [0-3] →")
    if choice == '0': return

    station = data.station_id or "unknown"
    ts_str  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"synop_{station}_{ts_str}"
    name = prompt(f"Filename (without extension) [default: {default_name}] →") or default_name

    if   choice == '1': export_json(data, name + ".json")
    elif choice == '2': export_csv (data, name + ".csv")
    elif choice == '3': export_txt (data, name + ".txt")
    else: err("Invalid choice."); return
    pause()

def menu_history():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{BOLD}SESSION HISTORY{RESET}")
    sep()
    if not SESSION_HISTORY:
        info("No messages decoded yet in this session.")
        pause(); return
    for i, (raw, data) in enumerate(SESSION_HISTORY, 1):
        ts_flag = "⚡ TS" if data.thunderstorm else ""
        tsr_flag= "⛈ TSRA" if data.thunderstorm_rain else ""
        print(f"  {GREEN}{i:2d}{RESET}. Station {c(str(data.station_id), WHITE)}"
              f"  T={c(fmt(data.temperature_c,'°C'),YELLOW)}"
              f"  RH={c(fmt(data.rel_humidity_pct,'%'),CYAN)}"
              f"  {RED}{ts_flag} {tsr_flag}{RESET}")
    sep()
    sel = prompt(f"View details for entry [1-{len(SESSION_HISTORY)}], or 0 to go back →")
    if sel == '0': return
    try:
        idx = int(sel) - 1
        raw, data = SESSION_HISTORY[idx]
        results_menu(raw, data)
    except (ValueError, IndexError):
        err("Invalid selection."); pause()

def menu_help():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗
║              FM-12 SYNOP FORMAT GUIDE                    ║
╚══════════════════════════════════════════════════════════╝{RESET}

{BOLD}STRUCTURE:{RESET}
  AAXX YYGGiw           ← Section 0: Header
  IIiii                 ← Station number (e.g. 43279 = Chennai)
  iRiXhVV               ← Precip/Type/Cloud-height/Visibility
  Nddff                 ← Cloud cover / Wind direction / Wind speed
  1SnTTT                ← Temperature (Sn=0 positive, 1 negative)
  2SnTdTdTd             ← Dew point (or 9xx=RH)
  3PPPP                 ← Station pressure (/10 hPa)
  4PPPP                 ← MSL pressure (/10 hPa)
  5appp                 ← Pressure tendency (skip)
  6RRRt                 ← Precipitation (skip)
  7wwW1W2               ← Present weather / Past weather
  8NhCLCMCH             ← Cloud types (Low / Medium / High)
  333                   ← Section 3 separator
  1SnTxTxTx             ← Max temperature
  2SnTnTnTn             ← Min temperature

{BOLD}EXAMPLE (from IMD notebook):{RESET}
  {c("AAXX 03094", CYAN)}
  {c("43279 32597 31410 10390 20264 30018 40035 83400", CYAN)}
  {c("333", CYAN)}
  {c("59108", CYAN)}

{BOLD}KEY CODES:{RESET}
  iw (wind unit): 3 or 4 = knots | 1 or 2 = m/s
  N  (cloud cover): 0=clear, 8=overcast, 9=obscured
  ww 95-99 = Thunderstorm (TS)
  ww 91,92,95-99 = TS with Rain (TSRA)
""")
    sep()
    pause()

# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    main_menu() 