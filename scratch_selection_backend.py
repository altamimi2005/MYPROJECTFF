import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add override endpoint
override_endpoint = '''
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
'''

code = code.replace('frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")', 
                    override_endpoint + '\nfrontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")')

# 2. Update download-results to support selection filtering
old_download_results = '''@app.get("/api/download-results")
async def download_results(session_id: str = Cookie(None)):
    if not session_id or session_id not in session_results:
        return Response(content="No results found", status_code=404)
        
    results = session_results[session_id]'''

new_download_results = '''@app.get("/api/download-results")
async def download_results(filenames: str = None, session_id: str = Cookie(None)):
    if not session_id or session_id not in session_results:
        return Response(content="No results found", status_code=404)
        
    results = session_results[session_id]
    if filenames:
        name_list = set(filenames.split(","))
        results = [r for r in results if r.get("filename") in name_list]'''

code = code.replace(old_download_results, new_download_results)

# 3. Update download-report to support selection filtering and "Overwritten" confidence
old_download_report = '''@app.get("/api/download-report")
async def download_report(session_id: str = Cookie(None)):
    if not session_id or session_id not in session_results:
        return Response(content="No results found", status_code=404)
        
    results = session_results[session_id]'''

new_download_report = '''@app.get("/api/download-report")
async def download_report(filenames: str = None, session_id: str = Cookie(None)):
    if not session_id or session_id not in session_results:
        return Response(content="No results found", status_code=404)
        
    results = session_results[session_id]
    if filenames:
        name_list = set(filenames.split(","))
        results = [r for r in results if r.get("filename") in name_list]'''

code = code.replace(old_download_report, new_download_report)

# Fix confidence formatting in Excel report
old_excel_write = 'worksheet.write(row, 3, f"{res.get(\'confidence\', 0)}%", cell_fmt)'
new_excel_write = 'worksheet.write(row, 3, "Overwritten" if res.get(\'confidence\') == "Overwritten" else f"{res.get(\'confidence\', 0)}%", cell_fmt)'
code = code.replace(old_excel_write, new_excel_write)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Backend updated successfully")
