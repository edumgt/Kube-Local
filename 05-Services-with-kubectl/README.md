# Kubernetes - Service 다루기

## Step-01: Service 소개

- **Service 유형**
  1. ClusterIP
  2. NodePort
  3. LoadBalancer
  4. ExternalName
- 이 섹션에서는 ClusterIP와 NodePort/Ingress를 함께 다룹니다.
- LoadBalancer는 클라우드 제공자마다 동작이 달라, 해당 환경별 섹션에서 다룹니다.
- ExternalName은 명령형 생성이 없어 YAML로 정의해야 하며, 필요 시 추가 설명합니다.

---

## Step-02: ClusterIP Service - Backend 애플리케이션 구성

- Backend(Spring Boot REST) Deployment 생성
- Backend를 위한 ClusterIP Service 생성 (프론트엔드가 내부에서 접근용)
- Backend를 외부(포트 8080)에 직접 노출하기 위해 `hostPort` 사용

> **왜 NodePort를 안 쓰나?**  
> Kubernetes NodePort의 기본 허용 범위는 30000-32767입니다.  
> 포트 8080은 이 범위 밖이므로 `hostPort`를 사용해 노드에 직접 바인딩합니다.

### Backend Deployment + ClusterIP Service (`backend-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-backend-rest-app
  labels:
    app: my-backend-rest-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-backend-rest-app
  template:
    metadata:
      labels:
        app: my-backend-rest-app
    spec:
      nodeSelector:
        kubernetes.io/hostname: w1      # w1 노드(192.168.253.148)에 고정 배치
      containers:
      - name: kube-helloworld
        image: stacksimplify/kube-helloworld:1.0.0
        ports:
        - containerPort: 8080
          hostPort: 8080                # 노드 포트 8080에 직접 바인딩
---
apiVersion: v1
kind: Service
metadata:
  name: my-backend-service
  labels:
    app: my-backend-rest-app
spec:
  type: ClusterIP
  selector:
    app: my-backend-rest-app
  ports:
  - port: 8080
    targetPort: 8080
```

```bash
kubectl apply -f backend-deployment.yaml
kubectl get pods -o wide
# Observation: my-backend-rest-app Pod가 w1 노드에 배치되는지 확인

kubectl get svc my-backend-service
# Observation: ClusterIP 타입, 8080 포트 확인
```

**접속 URL (직접):**
```
http://192.168.253.148:8080/hello
```

---

## Step-03: Ingress - Frontend 애플리케이션 구성

- Frontend(Nginx Reverse Proxy) Deployment 생성
- Frontend를 위한 ClusterIP Service 생성
- Traefik Ingress를 통해 포트 80(외부)으로 노출

> **왜 Ingress를 쓰나?**  
> k3s에 Traefik이 이미 포트 80을 점유하고 있습니다.  
> NodePort로 80을 열 수 없으므로, Traefik Ingress 리소스를 생성해 라우팅합니다.

### Nginx 설정 (이미지 내장)

Frontend 이미지(`stacksimplify/kube-frontend-nginx:1.0.0`)는 아래 nginx 설정으로 모든 요청을 백엔드 ClusterIP 서비스로 프록시합니다.

```nginx
server {
    listen       80;
    server_name  localhost;
    location / {
        proxy_pass http://my-backend-service:8080;
    }
}
```

### Frontend Deployment + ClusterIP Service + Ingress (`frontend-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-frontend-nginx-app
  labels:
    app: my-frontend-nginx-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-frontend-nginx-app
  template:
    metadata:
      labels:
        app: my-frontend-nginx-app
    spec:
      containers:
      - name: kube-frontend-nginx
        image: stacksimplify/kube-frontend-nginx:1.0.0
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: my-frontend-service
  labels:
    app: my-frontend-nginx-app
spec:
  type: ClusterIP
  selector:
    app: my-frontend-nginx-app
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-frontend-ingress
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-frontend-service
            port:
              number: 80
```

```bash
kubectl apply -f frontend-deployment.yaml
kubectl get pods -o wide
kubectl get svc my-frontend-service
kubectl get ingress my-frontend-ingress
# Observation: ADDRESS 컬럼에 192.168.253.148, 192.168.253.149 확인
```

**접속 URL (Traefik → Nginx → Backend 프록시):**
```
http://192.168.253.149/hello
http://192.168.253.148/hello
```

> **참고:** `/`(루트) 경로는 백엔드에 핸들러가 없어 404를 반환합니다. `/hello`로 접근해야 합니다.

---

## 전체 트래픽 흐름

```
[외부 브라우저]
    │
    ├─ http://192.168.253.148:8080/hello
    │       └─> w1 hostPort:8080 → Backend Pod (Spring Boot) → "Hello World V1"
    │
    └─ http://192.168.253.149/hello
            └─> Traefik (port 80) → Ingress → Frontend Service
                    └─> Nginx Pod → ClusterIP:8080 → Backend Pod → "Hello World V1"
```

---

## Step-04: 스케일링 및 로드밸런싱 확인

```bash
# Backend를 10개로 스케일링
kubectl scale --replicas=10 deployment/my-backend-rest-app

kubectl get pods -o wide
# Observation: Pod들이 여러 노드에 분산 배치되는지 확인
# (단, hostPort 사용 시 동일 노드에 하나만 배치 가능 → 스케일링 시 nodeSelector 제거 권장)
```

스케일링 후 반복 접속하면 Pod 이름이 바뀌는 것으로 로드밸런싱을 확인할 수 있습니다:
```
Hello World  V1 <pod-hash>
```

---

## Step-05: 리소스 정리

```bash
kubectl delete -f backend-deployment.yaml
kubectl delete -f frontend-deployment.yaml

kubectl get all
# Observation: service/kubernetes만 남아 있으면 정상
```

---

## 추가 설명

- `hostPort`는 해당 노드에 Pod가 하나만 배치될 수 있어 스케일아웃이 제한됩니다. 운영에서는 NodePort 범위를 조정하거나 Ingress를 활용하는 것이 좋습니다.
- `ClusterIP`는 내부 통신의 기본이며, 마이크로서비스 간 안정적인 서비스 디스커버리를 제공합니다.
- `Ingress`는 단일 진입점(Traefik)에서 여러 서비스로 라우팅할 수 있어 NodePort보다 유연합니다.

---

## 참고: LoadBalancer / ExternalName

### LoadBalancer Service

- `type: LoadBalancer`는 클러스터 밖에서 들어오는 트래픽을 클라우드 LB(ELB/NLB 등)가 받아 Service로 전달합니다.
- k3s 환경에서는 Traefik이 `type: LoadBalancer`로 동작하며 `EXTERNAL-IP`가 자동 할당됩니다.
- 온프렘/베어메탈에서는 **MetalLB** 같은 구성요소가 필요합니다.

**언제 쓰나?**
- Ingress 없이 단일 서비스를 바로 외부에 노출할 때
- L4(TCP/UDP) 레벨로 외부 노출이 필요한 경우

**주요 설정 포인트:**
- `externalTrafficPolicy: Cluster` (기본) — 분산 쉽지만 클라이언트 원본 IP 미보존
- `externalTrafficPolicy: Local` — 원본 IP 보존, 단 해당 노드에 Pod 없으면 드롭

### ExternalName Service

- `type: ExternalName`은 프록시/로드밸런싱 없이 CoreDNS가 CNAME 응답을 반환하는 "DNS 별칭 서비스"입니다.
- 클러스터 내부 서비스 이름으로 외부 시스템(DB, API 등)을 가리킬 때 사용합니다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-external-api
spec:
  type: ExternalName
  externalName: api.example.com
```

**주의:**
- 포트 변환 기능 없음 — 앱이 직접 포트까지 포함해 호출해야 합니다.
- `externalName`에는 IP가 아닌 DNS 이름을 사용해야 합니다.

---

## 정리: 언제 무엇을 쓰나?

| 유형 | 용도 |
|---|---|
| **ClusterIP** | 클러스터 내부 통신 기본 (서비스 디스커버리 + 로드밸런싱) |
| **NodePort** | 노드 포트(30000-32767)를 고정 오픈해서 외부 진입 |
| **hostPort** | NodePort 범위 밖의 포트를 노드에 직접 바인딩 (스케일 제한 있음) |
| **LoadBalancer** | 클라우드/MetalLB LB를 공식 진입점으로 사용 |
| **Ingress** | 단일 LB(Traefik 등)에서 HTTP 경로 기반 라우팅 |
| **ExternalName** | K8s 서비스 이름 → 외부 DNS 별칭 (DNS만, 프록시 없음) |

---

# inotifywait 리눅스 명령어

## 개요
**`inotifywait`**는 리눅스에서 사용하는 명령어로, **inotify-tools** 패키지에 포함되어 있습니다.  
파일 시스템 이벤트(예: 파일 생성, 삭제, 수정, 접근 등)를 실시간으로 감시할 수 있습니다.

## 주요 특징
- **[inotifywait](ca://s?q=inotifywait_리눅스_명령어)**는 지정한 파일이나 디렉터리에 대해 이벤트가 발생할 때까지 대기합니다.
- 스크립트에서 파일 변경을 감지하고 자동으로 작업을 실행할 때 자주 사용됩니다.
- 이벤트 종류를 지정할 수 있으며, 무한 루프 형태로 계속 감시할 수도 있습니다.

## 사용 예시
```bash
# test.txt 파일의 변경 이벤트를 감시
inotifywait -m test.txt


---

# Playwright

## 개요
**Playwright**는 Microsoft가 만든 오픈소스 웹 자동화 및 테스트 프레임워크입니다.  
최신 브라우저(Chromium, Firefox, WebKit)를 하나의 API로 제어할 수 있으며, 다양한 언어를 지원합니다.

## 주요 특징
- **[멀티 브라우저 지원](ca://s?q=Playwright_브라우저_지원)**: Chromium, Firefox, WebKit
- **[다양한 언어](ca://s?q=Playwright_지원_언어)**: TypeScript, Python, .NET, Java
- **자동 대기(Auto-wait)**: 안정적인 테스트 실행
- **테스트 격리**: 각 테스트마다 새로운 브라우저 컨텍스트 생성
- **병렬 실행 및 샤딩**: CI/CD 환경에서 대규모 테스트 지원
- **접근성 기반 셀렉터**: `getByRole`, `getByLabel` 등

## 설치 방법
```bash
# Node.js 환경에서 설치
npm install -D @playwright/test
