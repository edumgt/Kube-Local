# Python Container Registry

Docker Distribution API v2를 Python으로 직접 구현한 학습용 컨테이너 이미지 레지스트리입니다.

## 기술 스택

| 구분 | 기술 | 버전 | 역할 |
|------|------|------|------|
| 언어 | Python | 3.12 | 애플리케이션 런타임 |
| 웹 프레임워크 | FastAPI | - | REST API 서버 |
| ASGI 서버 | Uvicorn | - | HTTP 서버 (0.0.0.0:5000) |
| 스토리지 | 로컬 파일시스템 | - | `./registry_storage/` 디렉토리 |
| 프론트엔드 | HTML + TailwindCSS + Axios | CDN | 웹 UI |

## 구현 스펙

**Docker Distribution API v2** (`/v2/`) 기반으로 아래 엔드포인트를 구현합니다.

### API 엔드포인트

| 메서드 | 경로 | 기능 |
|--------|------|------|
| `GET` | `/v2/` | API 버전 체크 (`Docker-Distribution-API-Version: registry/2.0`) |
| `HEAD` | `/v2/{name}/blobs/{digest}` | Blob 존재 여부 확인 |
| `GET` | `/v2/{name}/blobs/{digest}` | Blob 다운로드 (이미지 레이어, config) |
| `POST` | `/v2/{name}/blobs/uploads/` | Blob 업로드 세션 시작 |
| `PATCH` | `/v2/{name}/blobs/uploads/{uuid}` | Blob chunked 업로드 |
| `PUT` | `/v2/{name}/blobs/uploads/{uuid}` | Blob 업로드 완료 (monolithic / chunked 모두 지원) |
| `PUT` | `/v2/{name}/manifests/{reference}` | Manifest 업로드 (tag 또는 digest로 저장) |
| `GET` | `/v2/{name}/manifests/{reference}` | Manifest 다운로드 (tag 또는 digest로 조회) |
| `GET` | `/v2/_catalog` | 저장된 레포지토리 목록 |
| `GET` | `/v2/{name}/tags/list` | 특정 이미지의 태그 목록 |
| `GET` | `/` | 웹 UI |

### 스토리지 구조

```
registry_storage/
└── {image-name}/
    ├── blobs/
    │   └── sha256_{hash}        # 이미지 레이어 및 config 파일
    ├── manifests/
    │   ├── {tag}.json           # 태그 기반 매니페스트 (예: 1.0.json)
    │   └── sha256_{hash}.json   # digest 기반 매니페스트
    └── uploads/
        └── {uuid}               # chunked 업로드 임시 파일
```

### Blob 업로드 흐름

Docker/containerd는 두 가지 방식으로 blob을 업로드합니다.

**Chunked upload** (대용량 레이어)
```
POST /uploads/          → 세션 UUID 발급
PATCH /uploads/{uuid}   → 데이터 전송 (분할 가능)
PUT   /uploads/{uuid}   → 완료 및 digest 확정
```

**Monolithic upload** (소용량 또는 Docker 기본 동작)
```
POST /uploads/          → 세션 UUID 발급
PUT  /uploads/{uuid}    → body에 데이터 직접 포함하여 완료
```

> `commit_upload`는 두 방식을 모두 처리합니다. 임시 파일이 존재하면 rename, 없으면 PUT body를 직접 저장합니다.

### Manifest 저장 방식

Push 시 매니페스트를 **태그명**과 **sha256 digest** 두 가지 파일명으로 동시에 저장합니다. containerd는 pull 시 태그 → manifest index → platform manifest 순서로 digest 기반 재조회를 수행하기 때문입니다.

```python
# 태그로 저장: 1.0.json
# digest로 저장: sha256_82097770...json
```

`Docker-Content-Digest` 헤더에는 반드시 실제 sha256을 반환해야 합니다 (태그명 반환 시 containerd가 검증 실패).

## 알려진 제약 사항

| 항목 | 내용 |
|------|------|
| 인증 | 없음 (학습용) |
| TLS | HTTP only — containerd에서 insecure registry 설정 필요 |
| 동시 업로드 | 고정 UUID(`session-123`) 사용으로 병렬 push 시 충돌 가능 |
| 자동 재시작 | systemd 미등록 — 서버 재부팅 시 수동 시작 필요 |
| Blob 검증 | 저장 시 digest 일치 여부 검증 없음 |

## k3s insecure registry 설정

HTTP 레지스트리를 k3s 클러스터에서 사용하려면 **모든 노드**에 아래 파일을 생성하고 k3s를 재시작해야 합니다.

**control-plane 노드** — `/etc/rancher/k3s/registries.yaml`

```yaml
mirrors:
  "192.168.253.148:5000":
    endpoint:
      - "http://192.168.253.148:5000"
configs:
  "192.168.253.148:5000":
    tls:
      insecure_skip_verify: true
```

```bash
sudo systemctl restart k3s           # control-plane
sudo systemctl restart k3s-agent     # worker node
```

## 실행 방법

```bash
cd /home/ubuntu/my-registry
source venv/bin/activate
python registry.py
```

백그라운드 실행:

```bash
source venv/bin/activate
nohup python registry.py > registry.log 2>&1 &
```

## 이미지 push / pull 예시

```bash
# push
docker build -t 192.168.253.148:5000/fastapi-health:1.0 .
docker push 192.168.253.148:5000/fastapi-health:1.0

# 저장된 이미지 목록 확인
curl http://192.168.253.148:5000/v2/_catalog

# 태그 목록
curl http://192.168.253.148:5000/v2/fastapi-health/tags/list
```
