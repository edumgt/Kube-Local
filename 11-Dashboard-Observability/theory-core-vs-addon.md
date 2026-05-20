# 쿠버네티스 코어 기능 vs 서드파티(애드온/에코시스템)

## 1) 쿠버네티스 원 기능(코어 기능)

### A. 클러스터 기본 동작 (오케스트레이션)
- **스케줄링**: Pod를 어떤 Node에 배치할지 결정 (scheduler)
- **상태 유지/자가 치유**: 장애 시 재시작/재스케줄 (kubelet + controller)
- **스케일링**: Deployment/ReplicaSet 기반 수평 확장
- **롤링 업데이트/롤백**: Deployment 기본 동작

### B. 워크로드/리소스 모델
- Pod, Deployment, ReplicaSet, StatefulSet, DaemonSet, Job/CronJob
- ConfigMap, Secret
- Namespace, Label/Selector, Annotation

### C. 서비스 디스커버리 & L4 로드밸런싱
- Service (ClusterIP/NodePort/LoadBalancer)
- CoreDNS (서비스 이름 기반 DNS)

### D. 네트워킹 규약
- CNI 플러그인 연동 구조
- NetworkPolicy 오브젝트

### E. 스토리지 규약
- Volume / PV / PVC / StorageClass
- CSI 연동 구조

### F. 접근제어/보안
- RBAC, ServiceAccount
- API 인증/인가, Admission
- Pod Security 표준(버전별)

### G. 운영/확장 메커니즘
- kubectl / API 서버 / etcd / controller-manager
- CRD (커스텀 리소스 정의)
- Operator 패턴 기반

👉 **한 줄 요약**: 쿠버네티스 코어는 *컨트롤 플레인 + 표준 리소스 모델 + 확장 인터페이스(CNI/CSI/CRD)* 제공

---

## 2) 대표적인 서드파티 솔루션

### A. 네트워킹(CNI)
- Calico, Cilium, Flannel, Weave Net

### B. Ingress / Gateway
- NGINX Ingress Controller, HAProxy, Traefik
- Envoy 기반 Gateway API 컨트롤러

### C. 서비스 메시
- Istio, Linkerd, Kuma

### D. 스토리지(CSI)
- Rook-Ceph, Longhorn, OpenEBS
- 클라우드 벤더 CSI (EBS, GCE PD, Azure Disk)

### E. 관측(Observability)
- Prometheus, Grafana
- Loki, ELK, Fluent Bit/Fluentd
- Jaeger, Tempo, OpenTelemetry

### F. 배포/릴리즈/GitOps
- Helm (패키징/템플릿)
- Argo CD, Flux (GitOps)
- Argo Rollouts, Flagger (고급 배포)

### G. 보안/정책
- OPA Gatekeeper, Kyverno
- cert-manager
- Vault, External Secrets Operator
- Falco

### H. 백업/DR
- Velero

### I. 오토스케일링
- KEDA (이벤트 기반)
- Cluster Autoscaler, Karpenter

### J. 운영 플랫폼/관리형 서비스
- Rancher, OpenShift
- EKS/GKE/AKS

👉 **구분 팁**  
- 오브젝트/컨트롤 플레인만으로 동작 → **코어**  
- 컨트롤러/플러그인 추가 설치 필요 → **서드파티**

---

## Helm의 역할

- **패키지 매니저** (apt, yum과 유사)
- **Chart**: 매니페스트(YAML) 묶음
- **템플릿화 & Values 분리**: 환경별 값 관리
- **Release 단위 관리**: install/upgrade/rollback/uninstall/history
- **의존성 관리**: Redis/DB 등 함께 설치 가능
- **표준 배포 방식 제공**: 팀 내 배포 표준화

👉 **한 줄 요약**: Helm = 쿠버네티스 앱을 *패키지처럼 설치/업그레이드/롤백*하는 도구

---

## Kubernetes Dashboard Service 리소스 설명

### 공통: TYPE=ClusterIP
- 클러스터 내부 IP(10.43.x.x) 부여
- Pod들이 DNS/ClusterIP로 접근 가능
- 외부 직접 접근 불가 → port-forward/Ingress 필요

### 1. `kubernetes-dashboard-web` (8000/TCP)
- 대시보드 UI 프론트엔드
- 사용자 브라우저에 HTML/JS/CSS 제공
- 👉 “사용자 화면 담당”

### 2. `kubernetes-dashboard-api` (8000/TCP)
- 대시보드 백엔드 API 서버
- 리소스 조회, Pod 로그, YAML 보기 처리
- 👉 “대시보드 핵심 백엔드”

### 3. `kubernetes-dashboard-auth` (8000/TCP)
- 인증/세션/로그인 처리
- 토큰/OIDC 인증 흐름 담당
- 👉 “로그인/인증 전담”

### 4. `kubernetes-dashboard-metrics-scraper` (8000/TCP)
- 대시보드 메트릭 수집기
- metrics-server로부터 CPU/Mem 등 가져와 UI 표시
- 👉 “메트릭 중계/수집”

### 5. `kubernetes-dashboard-kong-proxy` (443/TCP)
- Kong 기반 Reverse Proxy/API Gateway
- 단일 진입점으로 API/Web/Auth/Metrics 라우팅
- 외부 노출 시 NodePort/LoadBalancer/Ingress 활용
- 👉 “대시보드 관문”

---

## 확인 명령어

```sh
