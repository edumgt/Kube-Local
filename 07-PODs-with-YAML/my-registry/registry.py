import os
import json
import hashlib

from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import FileResponse



app = FastAPI()

# 이미지가 저장될 기본 디렉토리
STORAGE_DIR = "./registry_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

# 1. API 버전 체크 (Docker CLI가 가장 먼저 요청함)
@app.get("/v2/")
def check_version():
    return Response(
        status_code=200,
        headers={"Docker-Distribution-API-Version": "registry/2.0"}
    )

# 2. Blob 존재 여부 확인 (Docker push/pull 시 기존 레이어가 있는지 확인할 때 필요)
@app.head("/v2/{name:path}/blobs/{digest}")
def check_blob_existence(name: str, digest: str):
    blob_path = os.path.join(STORAGE_DIR, name, "blobs", digest.replace(":", "_"))
    if not os.path.exists(blob_path):
        raise HTTPException(status_code=404, detail="Blob not found")
    
    return Response(
        status_code=200,
        headers={
            "Docker-Content-Digest": digest,
            "Content-Length": str(os.path.getsize(blob_path)),
            "Content-Type": "application/octet-stream"
        }
    )

# 3. Blob 업로드 시작 (Initiate Blob Upload)
@app.post("/v2/{name:path}/blobs/uploads/")
def initiate_upload(name: str):
    # 테스트용 고정 UUID 세션 생성
    uuid = "session-123"
    headers = {
        "Location": f"/v2/{name}/blobs/uploads/{uuid}",
        "Range": "0-0",
        "Docker-Upload-UUID": uuid
    }
    return Response(status_code=202, headers=headers)

# 4. Blob 데이터 업로드 (Monolithic/Chunked Upload 처리)
@app.patch("/v2/{name:path}/blobs/uploads/{uuid}")
async def upload_blob_chunk(name: str, uuid: str, request: Request):
    blob_data = await request.body()
    
    upload_dir = os.path.join(STORAGE_DIR, name, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, uuid)
    
    # 이어쓰기 모드(ab)로 데이터 기록
    with open(file_path, "ab") as f:
        f.write(blob_data)
        
    file_size = os.path.getsize(file_path)
    
    headers = {
        "Location": f"/v2/{name}/blobs/uploads/{uuid}",
        "Range": f"0-{file_size-1}",
        "Docker-Upload-UUID": uuid
    }
    return Response(status_code=202, headers=headers)

# 5. Blob 업로드 완료 (Commit Upload) — monolithic & chunked 모두 지원
@app.put("/v2/{name:path}/blobs/uploads/{uuid}")
async def commit_upload(name: str, uuid: str, digest: str, request: Request):
    blob_dir = os.path.join(STORAGE_DIR, name, "blobs")
    os.makedirs(blob_dir, exist_ok=True)
    final_path = os.path.join(blob_dir, digest.replace(":", "_"))

    upload_path = os.path.join(STORAGE_DIR, name, "uploads", uuid)
    if os.path.exists(upload_path):
        # chunked upload: PATCH로 쌓인 파일을 rename
        os.rename(upload_path, final_path)
    else:
        # monolithic upload: PUT body에 데이터가 직접 포함
        body = await request.body()
        if body:
            with open(final_path, "wb") as f:
                f.write(body)

    return Response(
        status_code=201,
        headers={
            "Docker-Content-Digest": digest,
            "Location": f"/v2/{name}/blobs/{digest}"
        }
    )

# 6. Blob 다운로드 (Pull)
@app.get("/v2/{name:path}/blobs/{digest}")
def download_blob(name: str, digest: str):
    blob_path = os.path.join(STORAGE_DIR, name, "blobs", digest.replace(":", "_"))
    if not os.path.exists(blob_path):
        raise HTTPException(status_code=404, detail="Blob not found")
    return FileResponse(blob_path, media_type="application/octet-stream")


# 8. Manifest 업로드 (Push의 최종 단계)
@app.put("/v2/{name:path}/manifests/{reference}")
async def upload_manifest(name: str, reference: str, request: Request):
    manifest_data = await request.body()
    
    # [수정] 업로드된 Manifest 데이터의 실제 sha256 해시값 계산
    sha256_hash = hashlib.sha256(manifest_data).hexdigest()
    digest = f"sha256:{sha256_hash}"
    
    manifest_dir = os.path.join(STORAGE_DIR, name, "manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    
    # reference(태그 이름)로도 저장하고, digest(해시값)로도 저장해 둡니다.
    with open(os.path.join(manifest_dir, f"{reference}.json"), "wb") as f:
        f.write(manifest_data)
    with open(os.path.join(manifest_dir, f"{digest.replace(':', '_')}.json"), "wb") as f:
        f.write(manifest_data)
        
    # [중요] Docker가 요구하는 정확한 Digest 헤더를 반환합니다.
    return Response(
        status_code=201,
        headers={
            "Docker-Content-Digest": digest,
            "Location": f"/v2/{name}/manifests/{digest}"
        }
    )



# 9. Manifest 다운로드 (Pull의 핵심 단계)
@app.get("/v2/{name:path}/manifests/{reference}")
def get_manifest(name: str, reference: str):
    manifest_dir = os.path.join(STORAGE_DIR, name, "manifests")
    # 태그(1.0.json) 또는 digest(sha256_abc.json) 순서로 탐색
    candidates = [
        os.path.join(manifest_dir, f"{reference}.json"),
        os.path.join(manifest_dir, f"{reference.replace(':', '_')}.json"),
    ]
    manifest_path = next((p for p in candidates if os.path.exists(p)), None)
    if manifest_path is None:
        raise HTTPException(status_code=404, detail="Manifest not found")

    with open(manifest_path, "rb") as f:
        manifest_data = f.read()

    data = json.loads(manifest_data)
    digest = f"sha256:{hashlib.sha256(manifest_data).hexdigest()}"
    media_type = data.get("mediaType", "application/vnd.docker.distribution.manifest.v2+json")
    return Response(
        content=manifest_data,
        media_type=media_type,
        headers={"Docker-Content-Digest": digest},
    )



# =====================================================================
# 10. 웹 UI를 위한 Catalog API (저장된 이미지 리스트 반환)
# =====================================================================
@app.get("/v2/_catalog")
def get_catalog():
    repositories = []
    if os.path.exists(STORAGE_DIR):
        # STORAGE_DIR 안의 하위 폴더들이 이미지 이름(Repository)이 됩니다.
        for item in os.listdir(STORAGE_DIR):
            if os.path.isdir(os.path.join(STORAGE_DIR, item)):
                repositories.append(item)
                
    return {"repositories": repositories}

# 특정 이미지의 태그 리스트 조회 API
@app.get("/v2/{name:path}/tags/list")
def get_tags(name: str):
    manifest_dir = os.path.join(STORAGE_DIR, name, "manifests")
    tags = []
    
    if os.path.exists(manifest_dir):
        for file in os.listdir(manifest_dir):
            # sha256_ 형태의 파일 제외하고 태그(.json 파일 이름)만 추출
            if file.endswith(".json") and not file.startswith("sha256_"):
                tags.append(file.replace(".json", ""))
                
    return {"name": name, "tags": tags}

# =====================================================================
# 11. 웹 브라우저 접속용 메인 화면 UI (HTML/TailwindCSS 사용)
# =====================================================================
@app.get("/", response_class=HTMLResponse)
async def index_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Python Container Registry UI</title>
        <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-900 text-gray-100 font-sans min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <header class="flex justify-between items-center border-b border-gray-700 pb-4 mb-8">
                <h1 class="text-3xl font-bold text-blue-400">🐳 Python Container Registry</h1>
                <span class="bg-green-500 text-gray-900 text-sm font-semibold px-3 py-1 rounded-full">Online</span>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="md:col-span-1 bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
                    <h2 class="text-xl font-semibold mb-4 text-gray-300 border-b border-gray-700 pb-2">📦 Repositories</h2>
                    <ul id="repo-list" class="space-y-2">
                        <li class="text-gray-500 italic">로딩 중...</li>
                    </ul>
                </div>

                <div class="md:col-span-2 bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
                    <h2 class="text-xl font-semibold mb-4 text-gray-300 border-b border-gray-700 pb-2">🏷️ Tags in <span id="selected-repo" class="text-blue-400">-</span></h2>
                    <div id="tag-container" class="flex flex-wrap gap-2">
                        <p class="text-gray-500 italic">레포지토리를 선택하면 태그 정보가 표시됩니다.</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // 페이지 로드 시 레포지토리 목록 가져오기
            async function fetchCatalog() {
                try {
                    const response = await axios.get('/v2/_catalog');
                    const repos = response.data.repositories;
                    const repoList = document.getElementById('repo-list');
                    
                    if (repos.length === 0) {
                        repoList.innerHTML = '<li class="text-gray-500 italic py-2">저장된 이미지가 없습니다.</li>';
                        return;
                    }
                    
                    repoList.innerHTML = '';
                    repos.forEach(repo => {
                        const li = document.createElement('li');
                        li.className = "p-3 bg-gray-700 hover:bg-blue-600 rounded-lg cursor-pointer transition duration-200 font-mono text-sm shadow-sm";
                        li.innerText = repo;
                        li.onclick = () => fetchTags(repo);
                        repoList.appendChild(li);
                    });
                } catch (error) {
                    console.error("Catalog 로드 실패:", error);
                }
            }

            // 특정 레포지토리의 태그 가져오기
            async function fetchTags(repoName) {
                document.getElementById('selected-repo').innerText = repoName;
                const tagContainer = document.getElementById('tag-container');
                tagContainer.innerHTML = '<p class="text-gray-400 italic">태그 조회 중...</p>';
                
                try {
                    const response = await axios.get(`/v2/${repoName}/tags/list`);
                    const tags = response.data.tags;
                    
                    if (!tags || tags.length === 0) {
                        tagContainer.innerHTML = '<p class="text-yellow-500 py-2">태그가 존재하지 않습니다.</p>';
                        return;
                    }
                    
                    tagContainer.innerHTML = '';
                    tags.forEach(tag => {
                        const span = document.createElement('span');
                        span.className = "px-4 py-2 bg-blue-900 border border-blue-500 text-blue-300 text-sm font-semibold rounded-lg font-mono shadow";
                        span.innerText = tag;
                        tagContainer.appendChild(span);
                    });
                } catch (error) {
                    console.error("Tag 로드 실패:", error);
                    tagContainer.innerHTML = '<p class="text-red-400">태그 정보를 가져오는 데 실패했습니다.</p>';
                }
            }

            // 초기 실행
            fetchCatalog();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)







if __name__ == "__main__":
    import uvicorn
    # 외부 장비(DESKTOP-CLQV18N)에서 접속할 수 있도록 0.0.0.0 으로 바인딩합니다.
    uvicorn.run(app, host="0.0.0.0", port=5000)
