"""
╔══════════════════════════════════════════════════════════╗
║   IMD SYNOP DECODER — FastAPI REST Service               ║
║   FM-12 Surface Synoptic Code  |  IMD Meenambakkam       ║
╚══════════════════════════════════════════════════════════╝

Usage:
    pip install fastapi uvicorn python-multipart
    python synop_api.py
    
Then access: http://localhost:8000/docs (interactive API docs)
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import os
import tempfile
from pathlib import Path

# Import core decoder from existing script
from synop_decoding import (
    decode_synop, 
    SynopData,
    extract_synop_codes,
    decode_synop_list,
    filter_by_station,
    export_json,
    export_csv,
    export_txt,
    validate_vomm_filename
)

# ═══════════════════════════════════════════════════════════
# PYDANTIC MODELS FOR API
# ═══════════════════════════════════════════════════════════

class DecodeRequest(BaseModel):
    """Request model for decoding a single SYNOP message."""
    message: str

class DecodeMultipleRequest(BaseModel):
    """Request model for decoding multiple SYNOP codes."""
    codes: List[str]

class FilterByStationRequest(BaseModel):
    """Request model for filtering by station ID."""
    codes: List[str]
    station_id: str

class VommFileRequest(BaseModel):
    """Request model for loading VOMM file."""
    filename: str  # e.g., "VOMM20260507" (without .txt)

class ExportRequest(BaseModel):
    """Request model for exporting results."""
    data: dict
    format: str  # "json", "csv", or "txt"

class BatchExportRequest(BaseModel):
    """Request model for exporting multiple decoded results."""
    results: List[dict]  # List of {"raw_message": "...", "decoded_data": {...}}
    format: str  # "json", "csv", or "txt"

# ═══════════════════════════════════════════════════════════
# SYNOP DATA SERIALIZER
# ═══════════════════════════════════════════════════════════

def synop_data_to_dict(data: SynopData) -> dict:
    """Convert SynopData object to JSON-serializable dictionary."""
    return {
        "station_id": data.station_id,
        "day": data.day,
        "utc_hour": data.utc_hour,
        "wind_unit": data.wind_unit,
        "precip_included": data.precip_included,
        "station_type": data.station_type,
        "cloud_base_height_m": data.cloud_base_height_m,
        "visibility_km": data.visibility_km,
        "cloud_cover_oktas": data.cloud_cover_oktas,
        "wind_direction_deg": data.wind_direction_deg,
        "wind_speed": data.wind_speed,
        "wind_speed_unit": data.wind_speed_unit,
        "temperature_c": data.temperature_c,
        "dewpoint_c": data.dewpoint_c,
        "rel_humidity_pct": data.rel_humidity_pct,
        "pressure_station_hpa": data.pressure_station_hpa,
        "pressure_msl_hpa": data.pressure_msl_hpa,
        "present_weather": data.present_weather,
        "present_weather_code": data.present_weather_code,
        "past_weather_1": data.past_weather_1,
        "past_weather_2": data.past_weather_2,
        "cloud_low_type": data.cloud_low_type,
        "cloud_mid_type": data.cloud_mid_type,
        "cloud_high_type": data.cloud_high_type,
        "low_cloud_cover": data.low_cloud_cover,
        "max_temperature_c": data.max_temperature_c,
        "min_temperature_c": data.min_temperature_c,
        "thunderstorm": data.thunderstorm,
        "thunderstorm_rain": data.thunderstorm_rain,
        "raw_groups": data.raw_groups,
        "warnings": data.warnings,
    }

# ═══════════════════════════════════════════════════════════
# BATCH EXPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════

def export_batch_json(results: List[dict]) -> str:
    """Export batch results as JSON string."""
    return json.dumps(results, indent=2, default=str)

def export_batch_csv(results: List[dict]) -> str:
    """Export batch results as CSV string."""
    import csv
    from io import StringIO
    
    if not results:
        return ""
    
    # Get all possible keys from all results
    all_keys = set()
    for result in results:
        if "decoded_data" in result:
            all_keys.update(result["decoded_data"].keys())
    all_keys.discard('raw_groups')
    all_keys.discard('warnings')
    all_keys = sorted(list(all_keys))
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=['raw_message'] + all_keys)
    writer.writeheader()
    
    for result in results:
        row = {'raw_message': result.get('raw_message', '')}
        decoded = result.get('decoded_data', {})
        for key in all_keys:
            row[key] = decoded.get(key, None)
        writer.writerow(row)
    
    return output.getvalue()

def export_batch_txt(results: List[dict]) -> str:
    """Export batch results as Plain Text string."""
    from datetime import datetime
    
    lines = []
    lines.append("=" * 70)
    lines.append("  IMD SYNOP BATCH DECODED REPORT")
    lines.append(f"  Total Codes: {len(results)}")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)
    
    for idx, result in enumerate(results, 1):
        data = result.get('decoded_data', {})
        raw = result.get('raw_message', '')
        
        lines.append(f"\n{'─' * 70}")
        lines.append(f"ENTRY {idx}/{len(results)} — Station: {data.get('station_id', 'N/A')}")
        lines.append(f"{'─' * 70}\n")
        lines.append(f"  Raw Message: {raw}\n")
        lines.append("  Station Info:")
        lines.append(f"    Station ID         : {data.get('station_id', 'N/A')}")
        lines.append(f"    Day (day of month) : {data.get('day', 'N/A')}")
        
        hour = data.get('utc_hour')
        time_str = f"{hour:02d}:00 GMT" if hour is not None else "N/A"
        lines.append(f"    Hour (GMT)         : {time_str}")
        lines.append(f"    Station Type       : {data.get('station_type', 'N/A')}\n")
        
        lines.append("  Temperature:")
        lines.append(f"    Current            : {data.get('temperature_c', 'N/A')} °C")
        lines.append(f"    Dew Point          : {data.get('dewpoint_c', 'N/A')} °C")
        lines.append(f"    Max                : {data.get('max_temperature_c', 'N/A')} °C")
        lines.append(f"    Min                : {data.get('min_temperature_c', 'N/A')} °C")
        lines.append(f"    Relative Humidity  : {data.get('rel_humidity_pct', 'N/A')} %\n")
        
        lines.append("  Wind:")
        wind_dir = data.get('wind_direction_deg', 'N/A')
        lines.append(f"    Direction          : {wind_dir}°")
        lines.append(f"    Speed              : {data.get('wind_speed', 'N/A')} {data.get('wind_speed_unit', '')}\n")
        
        lines.append("  Clouds:")
        lines.append(f"    Total Cover (N)    : {data.get('cloud_cover_oktas', 'N/A')} oktas")
        lines.append(f"    Low Cloud Type     : {data.get('cloud_low_type', 'N/A')}")
        lines.append(f"    Medium Cloud Type  : {data.get('cloud_mid_type', 'N/A')}")
        lines.append(f"    High Cloud Type    : {data.get('cloud_high_type', 'N/A')}")
        lines.append(f"    Base Height        : {data.get('cloud_base_height_m', 'N/A')} m\n")
        
        lines.append("  Visibility & Pressure:")
        lines.append(f"    Visibility         : {data.get('visibility_km', 'N/A')} km")
        lines.append(f"    Station Pressure   : {data.get('pressure_station_hpa', 'N/A')} hPa")
        lines.append(f"    MSL Pressure       : {data.get('pressure_msl_hpa', 'N/A')} hPa\n")
        
        lines.append("  Weather:")
        lines.append(f"    Present            : {data.get('present_weather', 'N/A')}")
        lines.append(f"    Thunderstorm (TS)  : {'YES' if data.get('thunderstorm') else 'No'}")
        lines.append(f"    TS + Rain (TSRA)   : {'YES' if data.get('thunderstorm_rain') else 'No'}")
    
    lines.append(f"\n{'=' * 70}")
    lines.append("END OF REPORT")
    lines.append(f"{'=' * 70}\n")
    
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════

app = FastAPI(
    title="IMD SYNOP Decoder API",
    description="FM-12 Surface Synoptic Code Decoder from India Meteorological Department",
    version="1.0.0",
)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "IMD SYNOP Decoder API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "endpoints": {
            "decode_single": "POST /decode",
            "decode_multiple": "POST /decode-multiple",
            "filter_by_station": "POST /filter-by-station",
            "load_vomm_file": "POST /load-vomm",
            "export_single": "POST /export",
            "export_batch": "POST /export-batch",
        }
    }

@app.post("/decode")
async def decode_single(request: DecodeRequest):
    """
    Decode a single SYNOP message.
    
    **Example:**
    ```json
    {
        "message": "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400"
    }
    ```
    """
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        data = decode_synop(request.message)
        return {
            "success": True,
            "raw_message": request.message,
            "decoded_data": synop_data_to_dict(data),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decoding error: {str(e)}")

@app.post("/decode-multiple")
async def decode_multiple(request: DecodeMultipleRequest):
    """
    Decode multiple SYNOP codes.
    
    **Example:**
    ```json
    {
        "codes": [
            "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400",
            "AAXX 05094 43279 32597 31410 10390 20264 30018 40035 83400"
        ]
    }
    ```
    """
    try:
        if not request.codes:
            raise HTTPException(status_code=400, detail="At least one code is required")
        
        results = decode_synop_list(request.codes)
        
        return {
            "success": True,
            "total_codes": len(request.codes),
            "decoded_count": len(results),
            "results": [
                {
                    "raw_message": raw,
                    "decoded_data": synop_data_to_dict(data),
                }
                for raw, data in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decoding error: {str(e)}")

@app.post("/filter-by-station")
async def filter_by_station_endpoint(request: FilterByStationRequest):
    """
    Decode multiple codes and filter by station ID.
    
    **Example:**
    ```json
    {
        "codes": [
            "AAXX 03094 43279 32597 31410 10390 20264 30018 40035 83400",
            "AAXX 05094 42809 32597 31410 10390 20264 30018 40035 83400"
        ],
        "station_id": "43279"
    }
    ```
    """
    try:
        if not request.codes:
            raise HTTPException(status_code=400, detail="At least one code is required")
        
        results = decode_synop_list(request.codes)
        filtered = filter_by_station(results, request.station_id)
        
        if not filtered:
            return {
                "success": False,
                "message": f"No codes found for station: {request.station_id}",
                "results": []
            }
        
        return {
            "success": True,
            "station_id": request.station_id,
            "total_codes": len(request.codes),
            "matching_codes": len(filtered),
            "results": [
                {
                    "raw_message": raw,
                    "decoded_data": synop_data_to_dict(data),
                }
                for raw, data in filtered
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filtering error: {str(e)}")

@app.post("/load-vomm")
async def load_vomm(request: VommFileRequest):
    """
    Load and decode SYNOP codes from a VOMM file.
    
    **Example:**
    ```json
    {
        "filename": "VOMM20260507"
    }
    ```
    """
    try:
        is_valid, error_msg = validate_vomm_filename(request.filename)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Load file
        filepath = os.path.join(r"D:\IMD INTERNSHIP", f"{request.filename}.txt")
        with open(filepath) as f:
            content = f.read()
        
        synop_codes = extract_synop_codes(content)
        
        if not synop_codes:
            return {
                "success": False,
                "message": "No SYNOP codes found in file.",
                "results": []
            }
        
        results = decode_synop_list(synop_codes)
        
        return {
            "success": True,
            "filename": request.filename,
            "total_codes": len(synop_codes),
            "decoded_count": len(results),
            "results": [
                {
                    "raw_message": raw,
                    "decoded_data": synop_data_to_dict(data),
                }
                for raw, data in results
            ]
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {request.filename}.txt")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/export")
async def export_results(request: ExportRequest):
    """
    Export decoded SYNOP data in various formats.
    
    **Supported formats:** json, csv, txt
    
    **Example:**
    ```json
    {
        "data": { "station_id": "43279", "temperature_c": 28.5, ... },
        "format": "json"
    }
    ```
    """
    try:
        if request.format not in ["json", "csv", "txt"]:
            raise HTTPException(status_code=400, detail="Format must be 'json', 'csv', or 'txt'")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f".{request.format}") as tmp:
            if request.format == "json":
                json.dump(request.data, tmp, indent=2)
            elif request.format == "csv":
                tmp.write("Parameter,Value\n")
                for key, value in request.data.items():
                    tmp.write(f'"{key}","{value}"\n')
            elif request.format == "txt":
                for key, value in request.data.items():
                    tmp.write(f"{key}: {value}\n")
            
            tmp_path = tmp.name
        
        return FileResponse(
            path=tmp_path,
            filename=f"synop_export.{request.format}",
            media_type=f"application/{request.format}" if request.format != "txt" else "text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@app.post("/export-batch")
async def export_batch(request: BatchExportRequest):
    """
    Export multiple decoded SYNOP results in batch (JSON, CSV, or TXT format).
    
    **Supported formats:** json, csv, txt
    
    **Use this after:** `/decode-multiple`, `/filter-by-station`, `/load-vomm`
    
    **Example:**
    ```json
    {
        "results": [
            {
                "raw_message": "AAXX 03094 43279...",
                "decoded_data": {"station_id": "43279", "temperature_c": 28.5, ...}
            },
            {
                "raw_message": "AAXX 05094 43279...",
                "decoded_data": {"station_id": "43279", "temperature_c": 29.0, ...}
            }
        ],
        "format": "json"
    }
    ```
    
    **Response:** Binary file download with all decoded results
    """
    try:
        if not request.results:
            raise HTTPException(status_code=400, detail="At least one result is required")
        
        if request.format not in ["json", "csv", "txt"]:
            raise HTTPException(status_code=400, detail="Format must be 'json', 'csv', or 'txt'")
        
        # Generate export content
        if request.format == "json":
            content = export_batch_json(request.results)
        elif request.format == "csv":
            content = export_batch_csv(request.results)
        else:  # txt
            content = export_batch_txt(request.results)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f".{request.format}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        filename = f"synop_batch_{len(request.results)}codes.{request.format}"
        
        return FileResponse(
            path=tmp_path,
            filename=filename,
            media_type="application/json" if request.format == "json" else \
                      "text/csv" if request.format == "csv" else \
                      "text/plain"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch export error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "IMD SYNOP Decoder API"}

# ═══════════════════════════════════════════════════════════
# RUN SERVER
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print("\n✨ Starting IMD SYNOP Decoder API...")
    print("📚 API Documentation: http://localhost:9000/docs")
    print("🚀 Interactive API: http://localhost:9000/redoc\n")
    uvicorn.run(app, host="0.0.0.0", port=9000)
