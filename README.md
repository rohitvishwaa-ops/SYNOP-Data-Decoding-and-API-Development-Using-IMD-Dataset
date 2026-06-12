# IMD SYNOP Decoder 🌦️

A comprehensive FM-12 Surface Synoptic Code decoder from the India Meteorological Department (IMD). Decode meteorological SYNOP messages with an interactive CLI or RESTful API.

---

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [CLI (Interactive Menu)](#cli-interactive-menu)
  - [API (REST Service)](#api-rest-service)
- [Project Structure](#project-structure)
- [Examples](#examples)
- [API Endpoints](#api-endpoints)
- [Supported Formats](#supported-formats)

---

## ✨ Features

### 🎯 Core Decoding
✅ **Decode single SYNOP messages** - Parse individual FM-12 codes  
✅ **Batch decode** - Process multiple codes at once  
✅ **Filter by station** - Extract results for specific stations  
✅ **VOMM file support** - Load codes from VOMM files (format: VOMM20260507.txt)  

### 📊 Data Extraction
✅ **Temperature & Humidity** - Current, dew point, max/min, relative humidity  
✅ **Wind Information** - Direction, speed (knots/m/s), compass direction  
✅ **Cloud Data** - Coverage, types (low/medium/high), base height  
✅ **Pressure** - Station & MSL pressure readings  
✅ **Weather Conditions** - Present weather, thunderstorm detection (TS/TSRA)  
✅ **Visibility** - Extended visibility table (0-70+ km)  

### 💾 Export Options
✅ **JSON** - For APIs, databases, automation  
✅ **CSV** - Open in Excel/Google Sheets  
✅ **Plain Text** - Human-readable formatted reports  
✅ **Batch Export** - Save all decoded results in one file  

### 🚀 Interfaces
✅ **Interactive CLI** - User-friendly menu-driven interface  
✅ **REST API** - FastAPI with auto-generated Swagger UI  
✅ **Both run independently** - Use separately or together  

### 🎨 User Experience
✅ **Color-coded output** - Easy-to-read terminal interface  
✅ **Interactive navigation** - Browse multiple results (P/N/E keys)  
✅ **Auto-generated docs** - Interactive API documentation  
✅ **CORS enabled** - Works with web/mobile apps  

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Step 1: Clone or Download
```bash
# Navigate to project directory
cd "D:\IMD internship"
```

### Step 2: Install Dependencies
```bash
# For CLI only
pip install python-dateutil

# For API (includes CLI)
pip install fastapi uvicorn python-multipart
```

---

## 🚀 Quick Start

### CLI (Interactive)
```bash
python synop_decoding.py
```

Then follow the on-screen menu:
1. **Decode a SYNOP message** - Enter raw code manually
2. **Decode from file** - Load codes from .txt file
3. **View history** - See previous decodings
4. **Export results** - Save as JSON/CSV/TXT

### API (REST Service)
```bash
python synop_api.py
```

Then open in browser:
- **Interactive Docs:** http://localhost:9000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:9000/redoc (ReDoc)
- **Base URL:** http://localhost:9000

---

## 📖 Usage

### CLI: Decode a Single Message

1. **Start the program:**
   ```bash
   python synop_decoding.py
   ```

2. **Select option 1** (Decode a SYNOP message)

3. **Enter SYNOP code:**
   ```
   AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400
   ```

4. **Press Enter twice** (once to finish, once for confirmation)

5. **View results:**
   - Full decoded report with all parameters
   - Temperature, wind, pressure, clouds, etc.

6. **Export (optional):**
   - Select option 8 (Export results)
   - Choose format: JSON, CSV, or TXT
   - File saved automatically

### CLI: Decode Multiple Codes from File

1. **Create a text file** with SYNOP codes (e.g., VOMM20260501.txt)

2. **Select option 2** (Decode from text file)

3. **Enter filename:** `VOMM20260501.txt`

4. **Choose action:**
   - **Decode all codes** - Saves all results
   - **Filter by station** - Show results for specific station

5. **Navigate results:**
   - **[P]** - Previous result
   - **[N]** - Next result
   - **[S]** - Save all to JSON/CSV/TXT
   - **[E]** - Exit

### API: Decode via REST

#### Single Message
```bash
curl -X POST http://localhost:9000/decode \
  -H "Content-Type: application/json" \
  -d '{"message": "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400"}'
```

#### Multiple Codes
```bash
curl -X POST http://localhost:9000/decode-multiple \
  -H "Content-Type: application/json" \
  -d '{
    "codes": [
      "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400",
      "AAXX 05094 43279 32597 31410 10390 20264 30018 40035 83400"
    ]
  }'
```

#### Filter by Station
```bash
curl -X POST http://localhost:9000/filter-by-station \
  -H "Content-Type: application/json" \
  -d '{
    "codes": ["AAXX 03094 43279...", "AAXX 05094 42809..."],
    "station_id": "43279"
  }'
```

#### Load VOMM File
```bash
curl -X POST http://localhost:9000/load-vomm \
  -H "Content-Type: application/json" \
  -d '{"filename": "VOMM20260507"}'
```

#### Export Batch Results
```bash
curl -X POST http://localhost:9000/export-batch \
  -H "Content-Type: application/json" \
  -d '{
    "results": [{"raw_message": "...", "decoded_data": {...}}, ...],
    "format": "json"
  }' \
  --output synop_batch.json
```

---

## 📁 Project Structure

```
D:\IMD internship\
├── synop_decoding.py           # Main CLI decoder
├── synop_api.py                # FastAPI REST service
├── synop_decode.bat            # Windows batch file
├── API_README.md               # API documentation
├── README.md                   # This file
├── VOMM*.txt                   # Sample VOMM files
├── synop_*.csv                 # Generated exports
├── synop_*.json                # Generated exports
└── synop_*.txt                 # Generated exports
```

---

## 🔍 Examples

### Example 1: Decode and Export
```python
import requests
import json

# Decode single message
response = requests.post(
    "http://localhost:9000/decode",
    json={"message": "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400"}
)

data = response.json()
print(f"Station: {data['decoded_data']['station_id']}")
print(f"Temperature: {data['decoded_data']['temperature_c']}°C")
print(f"Wind: {data['decoded_data']['wind_speed']} {data['decoded_data']['wind_speed_unit']}")
```

### Example 2: Batch Processing
```python
import requests

# Get codes from file
with open("VOMM20260501.txt") as f:
    content = f.read()

# Decode all
response = requests.post(
    "http://localhost:9000/decode-multiple",
    json={"codes": extract_codes(content)}  # Helper function
)

results = response.json()["results"]

# Export as JSON
export_resp = requests.post(
    "http://localhost:9000/export-batch",
    json={"results": results, "format": "json"}
)

with open("synop_batch.json", "wb") as f:
    f.write(export_resp.content)
```

### Example 3: Station-Specific Filtering
```bash
# Via CLI
# 1. Select option 2 (Decode from file)
# 2. Enter: VOMM20260605.txt
# 3. Select option 2 (Filter by station)
# 4. Enter: 43279 (Chennai)
# 5. Press [S] to save all Chennai observations

# Via API
curl -X POST http://localhost:9000/filter-by-station \
  -H "Content-Type: application/json" \
  -d '{
    "codes": [...],
    "station_id": "43279"
  }'
```

---

## 📡 API Endpoints

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| GET | `/` | API info & endpoints | JSON |
| GET | `/health` | Health check | JSON status |
| POST | `/decode` | Decode single message | JSON with decoded data |
| POST | `/decode-multiple` | Decode multiple codes | JSON array of results |
| POST | `/filter-by-station` | Filter by station ID | JSON filtered results |
| POST | `/load-vomm` | Load from VOMM file | JSON decoded results |
| POST | `/export` | Export single result | File download |
| POST | `/export-batch` | Export multiple results | File download (JSON/CSV/TXT) |

---

## 💾 Supported Formats

### JSON
- **Use for:** APIs, databases, programming
- **Structure:** Single object or array of objects
- **Pretty-printed:** Yes, with indentation

### CSV
- **Use for:** Excel, Google Sheets, data analysis
- **Format:** Headers + data rows
- **One row per SYNOP code**

### TXT
- **Use for:** Reports, human reading, printing
- **Format:** Nicely formatted readable report
- **Multiple sections:** Station, Temperature, Wind, Clouds, Pressure, Weather

---

## 📊 Sample Decoded Output

```
Station Info:
  ID: 43279
  Day: 3 (June 3rd)
  Time: 09:00 GMT
  Type: Manned (sec 3 omitted)

Temperature:
  Current: 39.0°C
  Dew Point: 26.4°C
  Humidity: 49.2%

Wind:
  Direction: 140° (SE)
  Speed: 10.0 knots

Pressure:
  Station: 1001.8 hPa
  MSL: 1003.5 hPa

Clouds:
  Cover: 3/8 oktas
  Base Height: 600m
  Types: Sc (Low), None (Medium), None (High)

Weather:
  Thunderstorm: No
  TS with Rain: No
```

---

## 🛠️ SYNOP Format Guide

### FM-12 Structure
```
AAXX YYGGiw IIiii iRiXhVV Nddff 1SnTTT 2SnTdTd 3PPPP 4PPPP 7wwW1W2 8NhCLCMCH 333 ...
```

### Key Groups
| Group | Meaning | Range |
|-------|---------|-------|
| AAXX | Header | Fixed |
| YYGGiw | Day, Hour, Wind unit | 01-31, 00-23, 1/3/4 |
| IIiii | Station ID | 00001-99999 |
| Nddff | Cloud cover, Wind dir, Wind speed | 0-9, 0-36, 00-99 |
| 1SnTTT | Temperature | Sign + 000-999 |
| 2SnTdTd | Dew point (or RH) | Sign + 000-999 |
| 3PPPP | Station pressure × 10 | 0000-9999 |
| 4PPPP | MSL pressure × 10 | 0000-9999 |
| 7wwW1W2 | Present/past weather | 0-99 |
| 8NhCL | Cloud info | Low/Medium/High types |

---

## 🔧 Troubleshooting

### API won't start on port 9000
```bash
# Check what's using the port
netstat -ano | findstr :9000

# Kill the process (Windows)
taskkill /PID <PID> /F

# Or use a different port - edit synop_api.py, change port to 8001
```

### File not found error
```bash
# Make sure file is in: D:\IMD internship\
# VOMM filename format: VOMM + YYYYMMDD (e.g., VOMM20260507.txt)
```

### Syntax errors
```bash
# Reinstall dependencies
pip install --upgrade fastapi uvicorn python-multipart
```

---

## 📝 Notes

- **Wind units:** Automatically detected from SYNOP code (knots or m/s)
- **Visibility:** Uses extended table (0 to 70+ km with special codes)
- **Pressure:** Automatically adds 1000 hPa if value < 500
- **Relative Humidity:** Calculated from temperature & dew point using Magnus formula
- **Warnings:** Displayed for parsing issues but don't stop decoding

---

## 📄 License

India Meteorological Department (IMD)

---

## 👤 Author

Developed for IMD Internship Program

---

## 📞 Support

For issues or questions:
1. Check the API documentation: http://localhost:9000/docs
2. Review this README
3. Check your SYNOP code format
4. Verify file paths and names

---

**Status:** ✅ Fully Functional | CLI + API | Batch Export Support | Multiple Formats

Happy decoding! 🌦️📊
