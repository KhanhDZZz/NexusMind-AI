import os
import glob
import json
import shutil
import requests
from typing import Optional
from urllib.parse import unquote
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from tavily import TavilyClient
from bs4 import BeautifulSoup

app = FastAPI(title="AI System - Universal Text File Attachment & KB Isolation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_GEMS_DIR = os.path.join(BASE_DIR, "gems")
GEMS_METADATA_FILE = os.path.join(BASE_DIR, "gems_metadata.json")
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Khởi tạo Tavily Client
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "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")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY and TAVILY_API_KEY != "tvly-KEY_CUA_BAN" else None

CHAT_HISTORY_DIR = "gem_histories"

def get_chat_history_file(gem_id: str) -> str:
    os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
    safe_gem_id = "".join(c if c.isalnum() else "_" for c in str(gem_id))
    return os.path.join(CHAT_HISTORY_DIR, f"{safe_gem_id}_history.json")

def load_chat_history(gem_id: str) -> list:
    history_file = get_chat_history_file(gem_id)
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"Lỗi đọc lịch sử (sẽ tạo mới): {e}")
            return []
    return []

def save_chat_history(gem_id: str, history: list):
    history_file = get_chat_history_file(gem_id)
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi lưu lịch sử chat của {gem_id}: {e}")

def ensure_dirs():
    os.makedirs(BASE_GEMS_DIR, exist_ok=True)
    if not os.path.exists(GEMS_METADATA_FILE):
        default_metadata = [
            {"gem_id": "default_gem", "id": "default_gem", "name": "Default Gem", "description": "Trợ lý hệ thống mặc định"},
            {"gem_id": "Pikey_Bot", "id": "Pikey_Bot", "name": "Pikey_Bot", "description": "Trợ lý cá nhân"}
        ]
        with open(GEMS_METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_metadata, f, ensure_ascii=False, indent=4)

ensure_dirs()

def get_gem_kb_dir(gem_id: Optional[str]) -> str:
    if not gem_id or str(gem_id).strip() == "" or str(gem_id) in ["undefined", "null", "none"]:
        gem_id = "default_gem"
    safe_gem_id = "".join([c if c.isalnum() else "_" for c in str(gem_id)])
    kb_dir = os.path.join(BASE_GEMS_DIR, safe_gem_id, "knowledge")
    return kb_dir

# HÀM CÀO NỘI DUNG TỪ ĐƯỜNG DẪN URL
def extract_text_from_url(url: str) -> str:
    try:
        # Nếu là liên kết Spotify, tận dụng Tavily Search để tìm tên bài hát và nghệ sĩ thay vì cào chay
        if "spotify.com" in url:
            from urllib.parse import urlparse
            # Trích xuất đoạn mã track nếu có thể hoặc dùng Tavily search với URL
            search_res = search_web(f"site:open.spotify.com {url}")
            if search_res:
                return f"Thông tin tìm thấy từ Spotify link qua Web Search:\n{search_res}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"[Không thể truy cập URL, mã lỗi: {response.status_code}]"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        title = soup.title.string if soup.title else "Không có tiêu đề"
        text = soup.get_text(separator=' ', strip=True)
        
        if len(text) > 4000:
            text = text[:4000] + "\n[... Nội dung trang web đã được lược bớt ...]"
            
        return f"Tiêu đề trang: {title}\nNội dung:\n{text}"
    except Exception as e:
        return f"[Lỗi khi đọc URL: {str(e)}]"

# HÀM ĐỌC NỘI DUNG TỪ TỆP DỮ LIỆU
def extract_text_from_file_bytes(filename: str, file_bytes: bytes) -> str:
    ext = filename.lower().split('.')[-1] if '.' in filename else ""
    text = ""
    
    if ext in ["txt", "md", "csv", "json", "py", "js", "html", "htm", "xml", "log", "css", "yaml", "yml", "ini", "bat", "sh", "sql"]:
        for enc in ["utf-8", "utf-16", "latin-1", "ascii"]:
            try:
                text = file_bytes.decode(enc)
                break
            except:
                continue
    elif ext == "pdf":
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            text = f"[Lỗi đọc file PDF: {e}]"
    elif ext == "docx":
        try:
            import io
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            text = f"[Lỗi đọc file Word: {e}]"
    elif ext in ["xlsx", "xls"]:
        try:
            import io
            import pandas as pd
            df_dict = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
            for sheet_name, df in df_dict.items():
                df = df.dropna(how='all').dropna(axis=1, how='all')
                text += f"\n--- Sheet: {sheet_name} (Tổng số dòng: {len(df)}) ---\n"
                if len(df) > 150:
                    text += df.head(150).to_string(index=False)
                    text += f"\n[... và {len(df) - 150} dòng dữ liệu tiếp theo đã được lược bớt ...]\n"
                else:
                    text += df.to_string(index=False) + "\n"
        except Exception as e:
            text = f"[Lỗi đọc file Excel: {e}]"
                
    return text.strip()

def load_gem_context(gem_id: Optional[str]) -> str:
    if not gem_id or str(gem_id).strip() in ["", "undefined", "null", "none"]:
        return ""
    
    safe_gem_id = "".join([c if c.isalnum() else "_" for c in str(gem_id)])
    kb_dir = os.path.join(BASE_GEMS_DIR, safe_gem_id, "knowledge")
    
    if not os.path.exists(kb_dir):
        return "" 
        
    files = glob.glob(os.path.join(kb_dir, "*"))
    context_text = ""
    for file_path in files:
        if os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as f:
                    content_bytes = f.read()
                extracted = extract_text_from_file_bytes(os.path.basename(file_path), content_bytes)
                context_text += f"\n--- Tài liệu nội bộ độc quyền của [{safe_gem_id}] ({os.path.basename(file_path)}) ---\n"
                context_text += extracted + "\n"
            except Exception as e:
                print(f"Lỗi đọc file {file_path}: {e}")
    return context_text.strip()

def search_web(query: str) -> str:
    try:
        global tavily_client
        if not tavily_client:
            key = os.environ.get("TAVILY_API_KEY", "tvly-KEY_CUA_BAN")
            tavily_client = TavilyClient(api_key=key)
            
        response = tavily_client.search(query=query, max_results=3)
        results = response.get("results", [])
        snippets = []
        for r in results:
            if isinstance(r, dict):
                title = r.get("title", "")
                content = r.get("content", "")
                url = r.get("url", "")
                snippets.append(f"- {title}: {content} ({url})")
        if snippets:
            return "\n".join(snippets)
    except Exception as e:
        print(f"Lỗi tìm kiếm Tavily: {e}")
    return ""

@app.get("/", response_class=HTMLResponse)
async def serve_chat_ui():
    for path in ["index.html", os.path.join(BASE_DIR, "index.html"), os.path.join(BASE_DIR, "app/templates/index.html")]:
        if os.path.exists(path):
            return FileResponse(path)
    return "Không tìm thấy file giao diện index.html"

@app.get("/api/config")
@app.get("/config")
async def get_config():
    return {"status": "ok", "ollama_url": OLLAMA_API_URL}

@app.get("/api/models")
async def get_models():
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=3)
        if res.status_code == 200:
            models = [m.get("name") for m in res.json().get("models", [])]
            if models: 
                return {"models": models}
    except: 
        pass
    return {"models": ["gemma4:e2b", "gemma2", "llama3"]}

@app.get("/gems")
@app.get("/api/gems")
async def list_gems():
    ensure_dirs()
    try:
        gems_list = []
        if os.path.exists(GEMS_METADATA_FILE):
            with open(GEMS_METADATA_FILE, "r", encoding="utf-8") as f:
                gems_list = json.load(f)
        
        if os.path.exists(BASE_GEMS_DIR):
            existing_folders = [d for d in os.listdir(BASE_GEMS_DIR) if os.path.isdir(os.path.join(BASE_GEMS_DIR, d))]
            current_ids = {str(g.get("gem_id") or g.get("id")) for g in gems_list}
            
            for folder in existing_folders:
                if folder not in current_ids:
                    gems_list.append({
                        "gem_id": folder,
                        "id": folder,
                        "name": folder.replace("_", " ").title(),
                        "description": "Khôi phục từ thư mục hệ thống"
                    })
        return gems_list
    except Exception as e:
        print(f"Lỗi đọc danh sách gems: {e}")
        return []

@app.post("/gems")
@app.post("/create_gem")
@app.post("/api/gems")
async def create_gem(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
        else:
            data = dict(await request.form())
            
        gem_id = data.get("gem_id") or data.get("id") or data.get("gemId")
        name = data.get("name") or data.get("displayName") or gem_id
        description = data.get("description") or data.get("desc") or ""

        if not gem_id:
            raise HTTPException(status_code=400, detail="Gem ID không được để trống")

        target_gem = str(gem_id).strip()
        gems = []
        if os.path.exists(GEMS_METADATA_FILE):
            with open(GEMS_METADATA_FILE, "r", encoding="utf-8") as f:
                try: gems = json.load(f)
                except: gems = []

        if not any(str(g.get("gem_id") or g.get("id")) == target_gem for g in gems):
            gems.append({"gem_id": target_gem, "id": target_gem, "name": str(name), "description": str(description)})
            with open(GEMS_METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(gems, f, ensure_ascii=False, indent=4)

        return {"success": True, "message": f"Đã tạo Gem thành công: {target_gem}", "gem_id": target_gem}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/gems/{gem_id}")
@app.delete("/api/gems/{gem_id}")
async def delete_gem(gem_id: str):
    try:
        target_gem = str(gem_id).strip()
        if target_gem in ["default_gem"]:
            raise HTTPException(status_code=400, detail="Không thể xóa Gem mặc định!")

        gem_dir = os.path.join(BASE_GEMS_DIR, target_gem)
        if os.path.exists(gem_dir):
            shutil.rmtree(gem_dir)
        
        if os.path.exists(GEMS_METADATA_FILE):
            with open(GEMS_METADATA_FILE, "r", encoding="utf-8") as f:
                gems = json.load(f)
            new_gems = [g for g in gems if str(g.get("gem_id") or g.get("id")) != target_gem]
            with open(GEMS_METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(new_gems, f, ensure_ascii=False, indent=4)
                
        return {"success": True, "message": f"Đã xóa thành công Gem '{target_gem}'"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_chat")
@app.get("/get_chat")
async def get_chat_history_api(gem_id: str = "default_gem"):
    try:
        history = load_chat_history(gem_id)
        return {"status": "success", "history": history}
    except Exception as e:
        return {"status": "error", "history": [], "message": str(e)}

@app.post("/chat")
@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        form = None
        content_type = request.headers.get("content-type", "")
        
        if "multipart/form-data" in content_type:
            form = await request.form()
            data = dict(form)
        elif "application/json" in content_type:
            data = await request.json()
        else:
            try:
                data = dict(await request.form())
                form = data
            except:
                data = await request.json()

        gem_id = (
            data.get("gem_id") or data.get("id") or data.get("gemId") or 
            data.get("current_gem") or data.get("bot_id") or "default_gem"
        )
        if not gem_id or str(gem_id).strip() in ["", "undefined", "null", "none"]:
            gem_id = "default_gem"

        message = (
            data.get("message") or data.get("prompt") or data.get("query") or 
            data.get("text") or data.get("content") or ""
        )
        
        if not message and "messages" in data:
            msgs = data.get("messages")
            if isinstance(msgs, list) and len(msgs) > 0:
                message = msgs[-1].get("content") or msgs[-1].get("text") or str(msgs[-1])

        target_gem = str(gem_id).strip()

        # 1. Xử lý tệp đính kèm trực tiếp từ form multipart
        attached_file_content = ""
        if form:
            for key in ["file", "attachment", "upload", "files"]:
                if key in form:
                    uploaded_item = form[key]
                    if hasattr(uploaded_item, "filename") and uploaded_item.filename:
                        file_bytes = await uploaded_item.read()
                        extracted_text = extract_text_from_file_bytes(uploaded_item.filename, file_bytes)
                        attached_file_content += f"\n\n[TỆP ĐÍNH KÈM TỪ NGƯỜI DÙNG - {uploaded_item.filename}]:\n{extracted_text}\n"

        # 2. Phát hiện và đọc URL trực tiếp từ tin nhắn
        url_content = ""
        import re
        url_matches = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', message)
        if url_matches:
            for raw_url in url_matches:
                clean_url = raw_url.strip().rstrip('.,;')
                scraped_data = extract_text_from_url(clean_url)
                url_content += f"\n\n[NỘI DUNG TRÍCH XUẤT TỪ LINK ({clean_url})]:\n{scraped_data}\n"

        # 3. Phát hiện và đọc đường dẫn file local từ message
        local_file_content = ""
        path_patterns = []
        path_patterns.extend(re.findall(r'["\']([a-zA-Z]:\\[^"\']+|/[^"\']+)["\']', message))
        path_patterns.extend(re.findall(r'[a-zA-Z]:\\[^<>:"|?*\r\n]+', message))
        path_patterns.extend(re.findall(r'/[^\0<>:"|?*\r\n\s]+', message))
        
        for raw_path in list(set(path_patterns)):
            clean_path = raw_path.strip().strip('"').strip("'").rstrip('.,;')
            if os.path.exists(clean_path) and os.path.isfile(clean_path):
                try:
                    with open(clean_path, "rb") as f:
                        file_bytes = f.read()
                    filename = os.path.basename(clean_path)
                    extracted_text = extract_text_from_file_bytes(filename, file_bytes)
                    local_file_content += f"\n\n[ĐƯỢC TRÍCH XUẤT TỪ ĐƯỜNG DẪN LOCAL - {filename}]:\n{extracted_text}\n"
                    
                    kb_dir = get_gem_kb_dir(target_gem)
                    os.makedirs(kb_dir, exist_ok=True)
                    with open(os.path.join(kb_dir, filename), "wb") as kb_f:
                        kb_f.write(file_bytes)
                except Exception as e:
                    print(f"❌ Lỗi đọc file từ đường dẫn {clean_path}: {e}")

        gem_context = load_gem_context(target_gem)
        
        # 4. Tìm kiếm web nếu có từ khóa tra cứu
        search_context = ""
        keywords_to_search = ["là gì", "ai là", "tin tức", "giá", "thời tiết", "kết quả", "thông tin về", "search", "tìm kiếm"]
        if any(kw in message.lower() for kw in keywords_to_search) or len(message.split()) > 4:
            web_data = search_web(message)
            if web_data:
                search_context = f"\n=== THÔNG TIN TÌM KIẾM WEB (TAVILY) ===\n{web_data}\n=====================================\n"

        chat_history = load_chat_history(target_gem)

        # Tổng hợp prompt gửi cho Ollama
        full_prompt = f"Bạn là AI assistant hoạt động dưới định danh: '{target_gem}'.\n"
        
        if gem_context:
            full_prompt += f"\n[KNOWLEDGE BASE CỦA GEM]:\n{gem_context}\n----------------------------------------------------\n"
        if url_content:
            full_prompt += f"\n{url_content}\n----------------------------------------------------\n"
        if local_file_content:
            full_prompt += f"\n{local_file_content}\n----------------------------------------------------\n"
        if attached_file_content:
            full_prompt += f"\n{attached_file_content}\n----------------------------------------------------\n"
        if search_context:
            full_prompt += f"\n{search_context}\n"
            
        if chat_history:
            full_prompt += "\n--- LỊCH SỬ TRÒ CHUYỆN TRƯỚC ĐÓ ---\n"
            for h in chat_history[-10:]:
                full_prompt += f"User: {h.get('user', '')}\nAssistant: {h.get('assistant', '')}\n"
            full_prompt += "------------------------------------\n"

        full_prompt += f"\nUser: {message}\nAssistant:"

        payload = {
            "model": "gemma4:e2b",
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_predict": 4096,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
            if response.status_code != 200:
                ai_reply = f"⚠️ Lỗi từ Ollama (Status {response.status_code}): {response.text}"
            else:
                res_json = response.json()
                ai_reply = res_json.get("response") or res_json.get("message") or str(res_json)
        except Exception as e:
            ai_reply = f"❌ Không thể kết nối tới Ollama tại {OLLAMA_API_URL}. Chi tiết: {str(e)}"

        chat_history.append({"user": message, "assistant": ai_reply})
        save_chat_history(target_gem, chat_history)

        return {
            "gem_id": target_gem,
            "reply": ai_reply,
            "response": ai_reply,
            "message": ai_reply,
            "status": "success"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
@app.get("/api/files")
async def list_files_query(gem_id: Optional[str] = Query("default_gem")):
    target = gem_id if gem_id and gem_id not in ["undefined", "null", "none"] else "default_gem"
    kb_dir = get_gem_kb_dir(target)
    if not os.path.exists(kb_dir):
        return []
    filenames = [f for f in os.listdir(kb_dir) if os.path.isfile(os.path.join(kb_dir, f))]
    return [{"name": f, "filename": f, "file_name": f} for f in filenames]

@app.get("/gems/{gem_id}/files")
@app.get("/api/gems/{gem_id}/files")
async def list_files_path(gem_id: str):
    return await list_files_query(gem_id)

async def core_upload_file(gem_id: str, file: UploadFile):
    target = gem_id if gem_id and gem_id not in ["undefined", "null", "none"] else "default_gem"
    kb_dir = get_gem_kb_dir(target)
    os.makedirs(kb_dir, exist_ok=True)
    file_path = os.path.join(kb_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"success": True, "message": f"Tải lên thành công tệp '{file.filename}'"}

@app.post("/upload")
@app.post("/api/upload")
async def upload_file_query(request: Request, file: UploadFile = File(...)):
    form = await request.form()
    gem_id = form.get("gem_id") or form.get("id") or "default_gem"
    return await core_upload_file(str(gem_id), file)

@app.post("/gems/{gem_id}/upload")
@app.post("/api/gems/{gem_id}/upload")
@app.post("/gems/{gem_id}/files")
@app.post("/api/gems/{gem_id}/files")
async def upload_file_path(gem_id: str, file: UploadFile = File(...)):
    return await core_upload_file(gem_id, file)

@app.post("/api/clear_chat")
@app.post("/clear_chat")
async def clear_chat_history(request: Request):
    try:
        data = await request.json()
        gem_id = data.get("gem_id") or data.get("id") or "default_gem"
        history_file = get_chat_history_file(str(gem_id).strip())
        if os.path.exists(history_file):
            os.remove(history_file)
        return {"status": "success", "message": f"Đã xóa lịch sử chat của Gem: {gem_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/gems/{gem_id}/files/{filename}")
@app.delete("/api/gems/{gem_id}/files/{filename}")
async def delete_kb_file(gem_id: str, filename: str):
    try:
        target = gem_id if gem_id and gem_id not in ["undefined", "null", "none"] else "default_gem"
        kb_dir = get_gem_kb_dir(target)
        decoded_filename = unquote(filename)
        file_path = os.path.join(kb_dir, decoded_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"success": "True", "message": f"Đã xóa file {decoded_filename}"}
        raise HTTPException(status_code=404, detail=f"Không tìm thấy file: {decoded_filename}")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_5:app", host="0.0.0.0", port=8000, reload=True)