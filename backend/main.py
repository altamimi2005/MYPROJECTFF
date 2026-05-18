import os
import uuid
import io
import csv
import shutil
from pathlib import Path
from typing import List, Dict
from fastapi import FastAPI, UploadFile, File, Response, Cookie, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .inference import process_batch

# Temp directory for uploaded images (served back to browser)
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="SolarVision AI Backend")

@app.on_event("startup")
async def startup_event():
    print("------------------------------------------")
    print("SERVER STARTED - BATCHED CSV EXPORT READY")
    print("------------------------------------------")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (Session ID -> List of result dictionaries)
session_results: Dict[str, List[dict]] = {}

@app.post("/api/upload")
async def upload_images(
    response: Response, 
    session_id: str = Cookie(None),
    files: List[UploadFile] = File(...),
    auto_crop: bool = Form(True)
):
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        session_results[session_id] = []
    elif session_id not in session_results:
        session_results[session_id] = []
        
    session_results[session_id] = []

    # Save images to a session folder so the browser can display them
    session_dir = UPLOADS_DIR / session_id
    if session_dir.exists():
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    contents_list = []
    filenames = []
    for file in files:
        data = await file.read()
        contents_list.append(data)
        # Sanitize filename
        safe_name = Path(file.filename).name
        filenames.append(safe_name)
        # Write to disk
        (session_dir / safe_name).write_bytes(data)

    try:
        results = process_batch(contents_list, filenames, auto_crop=auto_crop)
    except Exception as e:
        results = [{"filename": f, "error": f"Batch process failed: {str(e)}", "is_solar_panel": True} for f in filenames]

    session_results[session_id] = results

    # Return results to client — add image_url, strip raw bytes
    client_results = []
    for r in results:
        cr = r.copy()
        if "image_data" in cr: del cr["image_data"]
        cr["image_url"] = f"/uploads/{session_id}/{cr['filename']}"
        client_results.append(cr)

    return {"message": "Success", "results": client_results, "session_id": session_id}

@app.get("/api/results")
async def get_results(session_id: str = Cookie(None)):
    if not session_id or session_id not in session_results:
        return {"results": []}
    
    client_results = []
    for r in session_results[session_id]:
        cr = r.copy()
        if "image_data" in cr: del cr["image_data"]
        client_results.append(cr)
        
    return {"results": client_results}

@app.get("/api/download-results")
async def download_results(filenames: str = None, session_id: str = Cookie(None)):
    if not session_id or session_id not in session_results:
        return Response(content="No results found", status_code=404)
        
    results = session_results[session_id]
    if filenames:
        name_list = set(filenames.split(","))
        results = [r for r in results if r.get("filename") in name_list]
    
    # 📝 CSV version (Keep for simple data needs)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Filename", "Analysis Result", "Confidence (%)"])
    
    for r in results:
        writer.writerow([
            r.get("filename", "unknown"),
            r.get("result", "Error"),
            r.get("confidence", 0.0)
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=SolarVision_Results.csv"}
    )

@app.get("/api/download-report")
async def download_report(filenames: str = None, session_id: str = Cookie(None)):
    if not session_id or session_id not in session_results:
        return Response(content="No results found", status_code=404)
        
    results = session_results[session_id]
    if filenames:
        name_list = set(filenames.split(","))
        results = [r for r in results if r.get("filename") in name_list]
    import xlsxwriter
    from PIL import Image
    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("Analysis Report")
    
    # Formatting
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1e293b', 'font_color': 'white', 'align': 'center', 'valign': 'vcenter'})
    cell_fmt = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
    
    # Headers
    headers = ["Image", "Filename", "Result", "Confidence", "Cropping Status", "Is Solar?"]
    for col, h in enumerate(headers):
        worksheet.write(0, col, h, header_fmt)
        
    worksheet.set_column(0, 0, 20) # Image column width
    worksheet.set_column(1, 1, 40) # Filename column width
    worksheet.set_column(2, 5, 18) # Other columns
    
    for row, res in enumerate(results, start=1):
        worksheet.set_row(row, 80) # Row height for thumbnail
        
        # 1. Insert Image Thumbnail (if exists)
        if "image_data" in res:
            try:
                img_bytes = res["image_data"]
                img = Image.open(io.BytesIO(img_bytes))
                img.thumbnail((150, 100)) # Create thumbnail for efficiency
                thumb_io = io.BytesIO()
                img.save(thumb_io, format="PNG")
                worksheet.insert_image(row, 0, f"img_{row}.png", {'image_data': thumb_io, 'x_offset': 5, 'y_offset': 5})
            except:
                worksheet.write(row, 0, "No Image", cell_fmt)
        else:
            worksheet.write(row, 0, "N/A", cell_fmt)
            
        # 2. Other data
        worksheet.write(row, 1, res.get("filename", "unknown"), cell_fmt)
        worksheet.write(row, 2, res.get("result", "N/A"), cell_fmt)
        worksheet.write(row, 3, "Overwritten" if res.get('confidence') == "Overwritten" else f"{res.get('confidence', 0)}%", cell_fmt)
        worksheet.write(row, 4, res.get("crop_status", "N/A"), cell_fmt)
        worksheet.write(row, 5, "Yes" if res.get("is_solar_panel") else "No", cell_fmt)
        
    workbook.close()
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=SolarVision_Full_Report.xlsx"}
    )

# Mount the beautiful new frontend directory

from fastapi import Request

@app.post("/api/override")
async def override_result(request: Request, session_id: str = Cookie(None)):
    if not session_id or session_id not in session_results:
        return {"status": "error", "message": "No active session"}
    
    data = await request.json()
    filename = data.get("filename")
    new_result = data.get("new_result")
    
    for r in session_results[session_id]:
        if r.get("filename") == filename:
            r["result"] = new_result
            r["confidence"] = "Overwritten"
            r["is_damaged"] = (new_result == "Damaged")
            r["is_uncertain"] = (new_result == "Uncertain")
            break
            
    return {"status": "success"}

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
uploads_dir = str(UPLOADS_DIR)

# Serve uploaded images BEFORE the catch-all frontend mount
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

