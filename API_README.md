# IMD SYNOP Decoder API

A FastAPI-based REST API for decoding FM-12 Surface Synoptic Code messages.

## Installation

```bash
pip install fastapi uvicorn python-multipart
```

## Running the API

```bash
python synop_api.py
```

The API will start at `http://localhost:8000`

## API Documentation

- **Interactive Docs (Swagger UI):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc

## Endpoints

### 1. Decode Single Message
```
POST /decode

Request:
{
    "message": "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400"
}

Response:
{
    "success": true,
    "raw_message": "...",
    "decoded_data": {
        "station_id": "43279",
        "temperature_c": 28.5,
        ...
    }
}
```

### 2. Decode Multiple Codes
```
POST /decode-multiple

Request:
{
    "codes": [
        "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400",
        "AAXX 05094 43279 32597 31410 10390 20264 30018 40035 83400"
    ]
}

Response:
{
    "success": true,
    "total_codes": 2,
    "decoded_count": 2,
    "results": [...]
}
```

### 3. Filter by Station
```
POST /filter-by-station

Request:
{
    "codes": [
        "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400",
        "AAXX 05094 42809 32597 31410 10390 20264 30018 40035 83400"
    ],
    "station_id": "43279"
}

Response:
{
    "success": true,
    "station_id": "43279",
    "total_codes": 2,
    "matching_codes": 1,
    "results": [...]
}
```

### 4. Load from VOMM File
```
POST /load-vomm

Request:
{
    "filename": "VOMM20260507"
}

Response:
{
    "success": true,
    "filename": "VOMM20260507",
    "total_codes": 24,
    "decoded_count": 24,
    "results": [...]
}
```

### 5. Export Results
```
POST /export

Request:
{
    "data": {
        "station_id": "43279",
        "temperature_c": 28.5,
        "wind_speed": 12.5
    },
    "format": "json"
}

Response: Binary file download (json/csv/txt)
```

### 6. Health Check
```
GET /health

Response:
{
    "status": "healthy",
    "service": "IMD SYNOP Decoder API"
}
```

## Usage Examples

### Using cURL

```bash
# Decode single message
curl -X POST http://localhost:8000/decode \
  -H "Content-Type: application/json" \
  -d '{"message": "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400"}'

# Decode multiple codes
curl -X POST http://localhost:8000/decode-multiple \
  -H "Content-Type: application/json" \
  -d '{"codes": ["AAXX 03094 43279...", "AAXX 05094 43279..."]}'

# Filter by station
curl -X POST http://localhost:8000/filter-by-station \
  -H "Content-Type: application/json" \
  -d '{"codes": ["..."], "station_id": "43279"}'
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Decode single
response = requests.post(
    f"{BASE_URL}/decode",
    json={"message": "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400"}
)
print(response.json())

# Decode multiple
response = requests.post(
    f"{BASE_URL}/decode-multiple",
    json={"codes": ["AAXX ...", "AAXX ..."]}
)
print(response.json())

# Filter by station
response = requests.post(
    f"{BASE_URL}/filter-by-station",
    json={"codes": ["..."], "station_id": "43279"}
)
print(response.json())

# Load VOMM file
response = requests.post(
    f"{BASE_URL}/load-vomm",
    json={"filename": "VOMM20260507"}
)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
const BASE_URL = "http://localhost:8000";

// Decode single
fetch(`${BASE_URL}/decode`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        message: "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400"
    })
})
.then(r => r.json())
.then(data => console.log(data));

// Filter by station
fetch(`${BASE_URL}/filter-by-station`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        codes: ["AAXX ...", "AAXX ..."],
        station_id: "43279"
    })
})
.then(r => r.json())
.then(data => console.log(data));
```

## Features

✅ Decode single or multiple SYNOP messages  
✅ Filter results by station ID  
✅ Load SYNOP codes from VOMM files  
✅ Export decoded data (JSON/CSV/TXT)  
✅ Comprehensive error handling  
✅ CORS enabled for cross-origin requests  
✅ Interactive API documentation with Swagger UI  
✅ Health check endpoint  

## Notes

- The CLI (`synop_decoding.py`) remains unchanged and functional
- Both API and CLI can be used independently
- All decoded parameters are returned in JSON format
- File paths are configured for `D:\IMD INTERNSHIP\` directory
