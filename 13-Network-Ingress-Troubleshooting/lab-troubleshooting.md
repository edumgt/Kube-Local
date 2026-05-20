# k3s 교육 실습 랩: Pod 장애 분석 / 서비스 라우팅 / HPA / Ingress(Traefik)

> 통합본: `7.1 k3s-edu-labs-troubleshooting.md` + `7.4 k8s_beginner_troubleshooting_playbook.md`

## 기존 문서 1

---


# HPA 실습(사전 조건 점검 → 부하 → 스케일)
> 주의: k3s는 환경에 따라 metrics-server가 없을 수 있습니다.  
> **HPA/`kubectl top`이 안 되면 먼저 metrics부터.**

### 3-A. metrics API 동작 확인
```sh
kubectl get apiservices | grep metrics
```
---
ubuntu@cp1:~$ kubectl get apiservices | grep metrics
v1beta1.metrics.k8s.io              kube-system/metrics-server   True        27d
```
---
```
kubectl top node 2>&1 | head
```
---
```
ubuntu@cp1:~$ kubectl top node 2>&1 | head
NAME   CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
cp1    207m         20%      2301Mi          58%
w1     38m          3%       942Mi           47%
w2     73m          7%       995Mi           50%
```

- `kubectl top`이 에러면: metrics-server가 없거나 동작 문제가 있을 수 있음

#### (선택) metrics-server 존재/로그 점검
```sh
kubectl -n kube-system get deploy | grep metrics
kubectl -n kube-system logs deploy/metrics-server --tail=200 | egrep -i 'error|fail|x509|timeout'
```
---
```
E0110 09:29:14.140394       1 scraper.go:149] "Failed to scrape node" err="Get \"https://192.168.56.11:10250/metrics/resource\": dial tcp 192.168.56.11:10250: connect: no route to host" node="w1"
E0110 09:29:14.140444       1 scraper.go:149] "Failed to scrape node" err="Get \"https://192.168.56.12:10250/metrics/resource\": dial tcp 192.168.56.12:10250: connect: no route to host" node="w2"
```
---
#### 위와 같이 10250 포트 막힐 경우 metrics-server 실행 노드 확인, 해당 netshoot pod 실행
```
timeout 2 bash -lc '</dev/tcp/192.168.56.11/10250' && echo "OK: w1:10250 open" || echo "FAIL: w1:10250"
timeout 2 bash -lc '</dev/tcp/192.168.56.12/10250' && echo "OK: w2:10250 open" || echo "FAIL: w2:10250"

OK: w1:10250 open
OK: w2:10250 open
```
---


### 3-B. HPA 대상 앱 준비(요청량 requests 설정 포함)
```sh
cat <<'YAML' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hpa-app
  namespace: demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hpa-app
  template:
    metadata:
      labels:
        app: hpa-app
    spec:
      containers:
      - name: app
        image: nginx:1.27-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: hpa-svc
  namespace: demo
spec:
  selector:
    app: hpa-app
  ports:
  - port: 80
    targetPort: 80
YAML
```

### 3-C. HPA 생성(예: CPU 50% 목표)
```sh
kubectl -n demo autoscale deploy hpa-app --cpu-percent=50 --min=1 --max=5
```
---
```
ubuntu@cp1:~$ kubectl -n demo autoscale deploy hpa-app --cpu-percent=50 --min=1 --max=5
Flag --cpu-percent has been deprecated, Use --cpu with percentage or resource quantity format (e.g., '70%' for utilization or '500m' for milliCPU).
horizontalpodautoscaler.autoscaling/hpa-app autoscaled
```
---
```
kubectl -n demo get hpa
```
---
```
ubuntu@cp1:~$ kubectl -n demo get hpa
NAME      REFERENCE            TARGETS       MINPODS   MAXPODS   REPLICAS   AGE
hpa-app   Deployment/hpa-app   cpu: 0%/50%   1         5         1          32s
```

---

지금 출력은 HPA가 정상 생성됐고, 대상 Deployment(hpa-app)도 붙었으며, 현재는 스케일할 만큼 CPU 사용량이 없어서(0%) replicas=1로 유지 중이라는 뜻이에요.

출력 해석

REFERENCE: Deployment/hpa-app
→ HPA가 이 디플로이먼트를 감시/조절

TARGETS: cpu: 0%/50%
→ 현재 CPU 사용률 0%, 목표는 50% (기본은 요청(request) 대비 사용률)

MINPODS / MAXPODS: 1 ~ 5
→ 최소 1개, 최대 5개까지 늘릴 수 있음

REPLICAS: 1
→ 지금은 스케일 조건이 안 되어 1개 유지

---

### 3-D. 부하 생성(내부에서 반복 요청)
```sh
kubectl run -n demo load --rm -it --image=busybox:1.36 -- sh -lc \
"while true; do wget -qO- http://hpa-svc:80/ >/dev/null; done"
```

다른 터미널에서 스케일 추적
```sh
kubectl -n demo get hpa -w
```
---
```
ubuntu@cp1:~$ kubectl -n demo get hpa -w
NAME      REFERENCE            TARGETS        MINPODS   MAXPODS   REPLICAS   AGE
hpa-app   Deployment/hpa-app   cpu: 30%/50%   1         5         1          2m22s
hpa-app   Deployment/hpa-app   cpu: 44%/50%   1         5         1          2m30s
hpa-app   Deployment/hpa-app   cpu: 42%/50%   1         5         1          3m30s
hpa-app   Deployment/hpa-app   cpu: 44%/50%   1         5         1          3m45s
hpa-app   Deployment/hpa-app   cpu: 40%/50%   1         5         1          4m
hpa-app   Deployment/hpa-app   cpu: 44%/50%   1         5         1          4m15s
```
또 다른 터미날에서 
```
ubuntu@cp1:~$ kubectl top nodes
NAME   CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
cp1    568m         56%      2380Mi          60%
w1     42m          4%       947Mi           48%
w2     742m         74%      915Mi           46%
```
---
```
kubectl -n demo get pod -l app=hpa-app -w
```

### 3-E. 해석 포인트(교육용)
- **requests가 없으면** CPU 기반 HPA가 이상하게 동작/불가능할 수 있음
- 스케일은 즉시가 아니라 metrics 수집 주기/안정화에 따라 지연될 수 있음
- 부하를 끊으면 scale down은 더 느리게(안정화) 일어나는 게 일반적

---
---


---



# F. 프로브(Probe) 실패로 재시작 --> 7.2 내용 참고
- `livenessProbe`가 계속 실패해서 kubelet이 컨테이너를 죽이고 재시작
- (주의) readinessProbe는 “트래픽 제외”이지 보통 “재시작”은 아닙니다. 재시작은 주로 liveness/startupProbe 실패가 원인.

---

## 3) 실습에서 자주 보는 케이스 (kubectl run 임시 Pod)

`kubectl run -it --rm ...`로 만든 임시 Pod에서:
- 서비스 Endpoint가 없어서 `curl`이 오래 대기하다가
- `^C`로 끊거나 컨테이너가 비정상 종료하면
- Pod가 **깨끗하게 삭제되지 않고 남거나**, **재시작**하면서 CrashLoop처럼 보일 수 있습니다.

---

## 4) 진단: “무엇이 죽이는가?” 빠르게 찾는 순서

### Step 1) Pod 이벤트부터 보기 (가장 중요)
```bash
kubectl -n <ns> describe pod <pod>
```
아래 키워드를 찾습니다:
- `Back-off restarting failed container`
- `Error`, `Exit Code`, `OOMKilled`
- 이미지 풀 실패(`ImagePullBackOff`)는 CrashLoop와 다름(아예 실행을 못함)

### Step 2) 현재/이전 로그 확인
CrashLoop는 “재시작”이므로 **직전 실행 로그**가 중요합니다.
```bash
kubectl -n <ns> logs <pod> -c <container>
kubectl -n <ns> logs <pod> -c <container> --previous
```

### Step 3) 종료 코드(Exit Code) 확인
```bash
kubectl -n <ns> get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'; echo
kubectl -n <ns> get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'; echo
```

### Step 4) 리소스/OOM 확인
```bash
kubectl -n <ns> describe pod <pod> | egrep -i 'oom|killed|memory|cpu|limit|request'
kubectl top pod -n <ns>
```

### Step 5) 프로브 확인
```bash
kubectl -n <ns> get pod <pod> -o yaml | egrep -n 'livenessProbe|readinessProbe|startupProbe'
kubectl -n <ns> describe pod <pod> | egrep -n 'Liveness|Readiness|Startup|probe|Unhealthy'
```

---

## 5) 해결 패턴(원인별 처방)

### A. 커맨드/엔트리포인트 문제
- `command/args` 오타, 실행 파일 경로 확인
- 컨테이너 안에서 직접 실행 확인:
```bash
kubectl -n <ns> exec -it <pod> -- sh

# 또는 (Pod가 바로 죽어 exec가 안 되면) 이미지로 별도 디버그 Pod 실행
kubectl -n <ns> run debug --rm -it --restart=Never --image=<image> -- sh
```

### B. 환경변수/ConfigMap/Secret 문제
- 누락 여부 점검:
```bash
kubectl -n <ns> get cm,secret
kubectl -n <ns> describe deploy/<name>
```
- 앱이 “설정 없으면 즉시 종료”하는지 코드/설정 확인

### C. 의존 서비스 연결 실패
- 서비스 DNS/포트 확인:
```bash
kubectl -n <ns> get svc,ep
kubectl -n <ns> run net --rm -it --restart=Never --image=curlimages/curl -- sh -lc \
"nslookup <svc> && curl -sv http://<svc>:<port>/ 2>&1 | head"
```

### D. OOMKilled(메모리 부족)
- limits/requests 조정, 앱 메모리 사용량 최적화
- 임시로 limit 상향 후 재현 여부 확인

### E. livenessProbe 실패
- startup 시간이 긴 앱이면:
  - `startupProbe` 도입
  - livenessProbe `initialDelaySeconds`, `failureThreshold`, `timeoutSeconds` 완화
- 실제로 “앱이 살아있는데” 프로브가 너무 빡빡하면 계속 재시작됩니다.

---

## 6) CrashLoopBackOff vs 비슷한 상태들

| 상태 | 의미 | 핵심 |
|---|---|---|
| CrashLoopBackOff | 실행은 되지만 계속 죽어서 재시작/백오프 | **Exit code/로그/이벤트** 봐야 함 |
| ImagePullBackOff | 이미지 풀 실패 | 레지스트리/태그/인증 문제 |
| ErrImagePull | 이미지 다운로드 자체 실패 | 동일 |
| CreateContainerConfigError | 설정 문제로 컨테이너 생성 불가 | env/secret/volume 등 |
| RunContainerError | 런타임 레벨 에러 | 노드/런타임 로그 필요 |

---

## 7) 실습용 “재현” 예시(이해를 위한)

### (1) 즉시 종료되는 컨테이너 → CrashLoop
```bash
kubectl -n demo run crash --image=busybox --restart=Always -- sh -lc "exit 1"
kubectl -n demo get pod crash -w
kubectl -n demo describe pod crash
kubectl -n demo logs crash --previous
```

---

## 8) “바로 해결” 체크리스트

1. `kubectl describe pod`에서 **Events** 확인  
2. `kubectl logs --previous`로 **직전 로그** 확인  
3. `ExitCode / Reason(OOMKilled 등)` 확인  
4. 프로브/리소스/설정/의존성 중 어디 문제인지 분류  
5. 수정 후 재배포(`kubectl rollout restart deploy/<name>`) 또는 Pod 재생성  

---

## 9) (당신 실습 로그 기준) 핵심 포인트

- `kubectl run ... tmp`가 `AlreadyExists`로 막힌 것은 **tmp Pod가 이미 남아있기 때문**입니다.
- CrashLoopBackOff 상태의 임시 Pod는 아래처럼 정리하는 게 깔끔합니다:
```bash
kubectl -n demo delete pod tmp --force --grace-period=0
kubectl -n demo run --rm -it --restart=Never --image=curlimages/curl curltest- -- sh -lc \
"curl -sS http://web-svc:80/ | head"
```

---

## 결론

`CrashLoopBackOff`는 “앱(컨테이너)이 계속 죽는다”는 신호입니다.  
가장 빠른 해결은 **Events + --previous 로그 + 종료코드** 3가지를 보고 원인을 좁히는 것입니다.

---

### 2-A. 장애 만들기: 존재하지 않는 명령으로 컨테이너 시작
(컨테이너가 바로 죽어서 CrashLoopBackOff 발생)
```sh
cat <<'YAML' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crash-app
  namespace: demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crash-app
  template:
    metadata:
      labels:
        app: crash-app
    spec:
      containers:
        - name: app
          image: busybox:1.36
          command: ["sh","-lc","not-a-real-command"]
YAML
```

### 2-B. 증상 확인
```sh
kubectl -n demo get pod -l app=crash-app -w
```
(잠깐 기다리면 STATUS가 CrashLoopBackOff로 변함)

### 2-C. 원인 진단 루틴(실전 순서)
1) Events(가장 빠름)
```sh
POD=$(kubectl -n demo get pod -l app=crash-app -o jsonpath='{.items[0].metadata.name}')
kubectl -n demo describe pod "$POD" | egrep -n 'Events|Warning|Back-off|Failed|Error'
```

2) logs / previous
```sh
kubectl -n demo logs "$POD" --tail=200
kubectl -n demo logs "$POD" --previous --tail=200
```

### 2-D. 해결: 정상 command로 변경(무한 대기)
```sh
cat <<'YAML' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crash-app
  namespace: demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crash-app
  template:
    metadata:
      labels:
        app: crash-app
    spec:
      containers:
        - name: app
          image: busybox:1.36
          command: ["sh","-lc","echo ok; sleep 3600"]
YAML
```

### 2-E. 해결 검증
```sh
kubectl -n demo get pod -l app=crash-app -w
kubectl -n demo logs -l app=crash-app --tail=50
```
---
---




# inside:
nslookup <svc>
nslookup <svc>.<ns>.svc.cluster.local
wget -qO- http://<svc>.<ns>.svc.cluster.local:<port>/
```

---

## C. Ingress / Traefik이 이상하다 (404/라우팅/호스트)

11) Ingress 전체 확인
```bash
kubectl get ingress -A
kubectl describe ingress <ing> -n <ns>
```

12) Traefik 상태/로그
```bash
kubectl -n kube-system get pods | grep -i traefik
kubectl -n kube-system logs deploy/traefik --tail=200
```

13) (k3s에서 가끔) LoadBalancer처럼 보이는 svclb 확인
```bash
kubectl -n kube-system get pods | grep -i svclb
kubectl -n kube-system describe pod <svclb-pod>
```

---

## D. “내가 들어간 셸이 컨테이너인지?” 확인

14) 컨테이너 셸에서 확인
```sh
hostname
ip a
cat /proc/1/cgroup | head
```
- 보통 **hostname이 pod처럼 보이고**, 네트워크가 **10.42.x** 대역이면 컨테이너일 확률이 큼

---

## E. 노드 유지보수(drain)에서 막힘

15) DaemonSet 때문에 drain 막힐 때(실습용)
```bash
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
```

---

### “증상 → 바로 쓰는 조합” 초단축 맵
- **Pending** → `describe pod` + `top nodes` + `describe node`
- **CrashLoopBackOff** → `logs --previous` + `describe pod`
- **ImagePullBackOff** → `describe pod (Events)` + 이미지명/레지스트리/시크릿
- **서비스 접속 안됨** → `describe svc` + `endpoints` + `pod labels` + 내부 busybox 테스트
- **Ingress 404** → `describe ingress` + `traefik logs`

---

## 2) 장애 유형별 예시 출력 + 해석 + 해결 (샘플)

### 2-1) Pod `Pending` (스케줄링 실패)
**예시**
```bash
kubectl get pod -n demo -o wide
NAME                  READY   STATUS    NODE
web-7c7b8c9d8-9xk2m   0/1     Pending   <none>
```

```bash
kubectl describe pod web-7c7b8c9d8-9xk2m -n demo
...
Events:
  Warning  FailedScheduling   0/3 nodes are available: 3 Insufficient cpu.
```

**해석 포인트**
- `NODE <none>` + `FailedScheduling` → **스케줄러가 배치 못함**
- `Insufficient cpu/memory` → **리소스 부족**

**해결**
```bash
kubectl top nodes
kubectl top pod -A | head
```

---

### 2-2) `ImagePullBackOff` (이미지 다운로드 실패)
**예시**
```bash
kubectl describe pod api-... -n demo
...
Events:
  Normal   Pulling    Pulling image "ngnix:1.27"
  Warning  Failed     Failed to pull image "ngnix:1.27": not found
  Warning  BackOff    Back-off pulling image "ngnix:1.27"
```

**해석 포인트**
- `not found` → **오타/태그 없음**
- `unauthorized`면 → **사설 레지스트리 인증 문제**

**해결**
- 이미지명/태그 수정
- 사설 레지스트리면 `imagePullSecrets` 구성

---

### 2-3) `CrashLoopBackOff` (컨테이너가 계속 죽음)
**예시**
```bash
kubectl get pod -n demo
NAME      READY   STATUS             RESTARTS
web-...   0/1     CrashLoopBackOff   5
```

```bash
kubectl logs web-... -n demo --previous --tail=50
Error: listen tcp :8080: bind: address already in use
```

**해석 포인트**
- **제일 먼저 `logs --previous`** 봐야 “죽기 직전 로그”가 나옴
- 흔한 원인: 포트 충돌, ENV 누락, 설정 파일 경로 오류, 프로브 실패

**해결**
- 앱 실행 옵션/환경변수/포트 점검
- 프로브 완화(초기지연 증가, 실패 임계치 조정)

---

### 2-4) `Running`인데 서비스 접속 불가 (Service selector/port/endpoints)
**예시**
```bash
kubectl get pod -n demo --show-labels
web-...  Running  app=web

kubectl describe svc web-svc -n demo
Selector: app=weeb

kubectl get endpoints web-svc -n demo
ENDPOINTS: <none>
```

**해석 포인트**
- Endpoints `<none>` = **Service가 연결할 Pod를 못 찾음**
- 대부분 **selector 라벨 오타**

**해결**
```bash
kubectl edit svc web-svc -n demo

# selector를 app=web로 수정
```

---

### 2-5) DNS 조회에서 NXDOMAIN이 섞여 나옴
**예시**
```sh
nslookup web-svc
** server can't find web-svc.svc.cluster.local: NXDOMAIN
Name: web-svc.demo.svc.cluster.local
Address: 10.43.31.179
```

**해석 포인트**
- 검색 도메인 순서에 따라 여러 후보를 시도하다 NXDOMAIN이 찍힐 수 있음
- 핵심은 **원하는 FQDN이 정상 해석되는지**

**해결**
```sh
nslookup web-svc.demo.svc.cluster.local
```

---

### 2-6) Ingress 404 / 라우팅 안 됨 (Traefik)
**예시(로그 힌트)**
```bash
kubectl -n kube-system logs deploy/traefik --tail=200
... msg="service not found" serviceName=whoami namespace=default
```

**해석 포인트**
- `service not found` → ingress backend 서비스명/namespace/port 불일치 가능성

**해결**
```bash
kubectl get svc -n <ns>
kubectl describe svc <svc> -n <ns>
kubectl describe ingress <ing> -n <ns>
```

---

### 2-7) `kubectl drain` 실패 (DaemonSet)
**예시**
```bash
kubectl drain w1
error: cannot delete DaemonSet-managed Pods ...
```

**해석 포인트**
- DaemonSet Pod는 노드 상주 목적 → 기본 drain이 삭제 못 함

**해결(실습용)**
```bash
kubectl drain w1 --ignore-daemonsets --delete-emptydir-data
```

---

### 2-8) “내가 지금 컨테이너 안 셸인가?”
**확인**
```sh
hostname
ip a
cat /proc/1/cgroup | head
```

---

## 3) 실습용 트러블 시나리오 10개 문제집 (망가뜨리기/복구)

### 사전 준비(공통)
네임스페이스 `demo` 기준.

```bash
kubectl create ns demo
```

기본 웹(nginx) + svc
```yaml

# 00-good.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: demo
spec:
  replicas: 2
  selector:
    matchLabels: { app: web }
  template:
    metadata:
      labels: { app: web }
    spec:
      containers:
      - name: nginx
        image: nginx:1.27-alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: web-svc
  namespace: demo
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
```

```bash
kubectl apply -f 00-good.yaml
```

---

### 시나리오 1) Service selector 오타 → Endpoints 없음
**망가뜨리기**
```bash
kubectl -n demo patch svc web-svc -p '{"spec":{"selector":{"app":"weeb"}}}'
```

**증상**
```bash
kubectl -n demo get endpoints web-svc

# ENDPOINTS <none>
```

**고치기**
```bash
kubectl -n demo patch svc web-svc -p '{"spec":{"selector":{"app":"web"}}}'
```

---

### 시나리오 2) targetPort 틀림 → 연결은 되는데 접속 실패
**망가뜨리기**
```bash
kubectl -n demo patch svc web-svc -p '{"spec":{"ports":[{"port":80,"targetPort":81}]}}'
```

**확인(내부에서 테스트)**
```bash
kubectl -n demo run bb --rm -it --restart=Never --image=busybox:1.36 -- sh

# inside:
wget -qO- http://web-svc:80/
```

**고치기**
```bash
kubectl -n demo patch svc web-svc -p '{"spec":{"ports":[{"port":80,"targetPort":80}]}}'
```

---

### 시나리오 3) 네임스페이스 착각 → “없는 리소스”로 보임
**실수 유도**
```bash
kubectl get svc web-svc

# NotFound
```

**고치기**
```bash
kubectl -n demo get svc web-svc
kubectl get svc -A | grep web-svc
```

---

### 시나리오 4) ImagePullBackOff (이미지 오타)
**망가뜨리기**
```bash
kubectl -n demo set image deploy/web nginx=ngnix:1.27
```

**확인**
```bash
kubectl -n demo get pod
kubectl -n demo describe pod <pod> | sed -n '/Events/,$p'
```

**고치기**
```bash
kubectl -n demo set image deploy/web nginx=nginx:1.27-alpine
```

---

### 시나리오 5) CrashLoopBackOff (명령어로 강제 종료시키기)
**망가뜨리기**
```bash
kubectl -n demo patch deploy web --type='json' -p='[
{"op":"add","path":"/spec/template/spec/containers/0/command","value":["sh","-c","echo boom; exit 1"]}
]'
```

**확인**
```bash
kubectl -n demo get pod
kubectl -n demo logs <pod> --previous --tail=50
```

**고치기**
```bash
kubectl -n demo rollout undo deploy/web
```

---

### 시나리오 6) ReadinessProbe 실패 → Pod Running인데 READY 0/1
**망가뜨리기**
```bash
kubectl -n demo patch deploy web --type='json' -p='[
{"op":"add","path":"/spec/template/spec/containers/0/readinessProbe",
 "value":{"httpGet":{"path":"/not-exist","port":80},"initialDelaySeconds":3,"periodSeconds":5}}
]'
```

**확인**
```bash
kubectl -n demo get pod
kubectl -n demo describe pod <pod> | sed -n '/Readiness/,$p'
```

**고치기**
```bash
kubectl -n demo rollout undo deploy/web
```

---

### 시나리오 7) Pending (리소스 요청 과하게) → 스케줄링 실패
**망가뜨리기**
```bash
kubectl -n demo patch deploy web --type='json' -p='[
{"op":"add","path":"/spec/template/spec/containers/0/resources",
 "value":{"requests":{"cpu":"100","memory":"100Gi"}}}
]'
```

**확인**
```bash
kubectl -n demo get pod
kubectl -n demo describe pod <pod> | sed -n '/Events/,$p'
```

**고치기**
```bash
kubectl -n demo rollout undo deploy/web
```

---

### 시나리오 8) DNS/FQDN 헷갈림 → NXDOMAIN 혼란
**실수 유도**
```bash
kubectl -n default run bb --rm -it --restart=Never --image=busybox:1.36 -- sh

# inside:
nslookup web-svc
```

**정답(고치기)**
```sh
nslookup web-svc.demo.svc.cluster.local
```

---

### 시나리오 9) Ingress 404 (Host 헤더/호스트 룰 문제)
**Ingress 예시**
```yaml

# 09-ing.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ing
  namespace: demo
spec:
  ingressClassName: traefik
  rules:
  - host: web.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-svc
            port:
              number: 80
```

**적용**
```bash
kubectl apply -f 09-ing.yaml
kubectl get ingress -n demo
```

**고치기(Host 헤더 포함 호출)**
```bash
curl -H "Host: web.local" http://<INGRESS_IP>/
```

---

### 시나리오 10) Ingress backend 서비스명 오타 → Traefik에 service not found
**망가뜨리기**
```bash
kubectl -n demo patch ingress web-ing --type='json' -p='[
{"op":"replace","path":"/spec/rules/0/http/paths/0/backend/service/name","value":"web-svcc"}
]'
```

**확인**
```bash
kubectl -n kube-system logs deploy/traefik --tail=200
kubectl -n demo describe ingress web-ing
```

**고치기**
```bash
kubectl -n demo patch ingress web-ing --type='json' -p='[
{"op":"replace","path":"/spec/rules/0/http/paths/0/backend/service/name","value":"web-svc"}
]'
```

---

## 4) 원인 즉시 판별 “3종 세트” (암기용)
```bash
kubectl describe pod <pod> -n <ns>
kubectl logs <pod> -n <ns> --previous --tail=200
kubectl get events -n <ns> --sort-by=.lastTimestamp | tail -n 30
```

---


## 참고 문서
- [guide-ingress-traefik.md](./guide-ingress-traefik.md)
- [guide-network-basics.md](./guide-network-basics.md)
- [lab-troubleshooting.md](./lab-troubleshooting.md)
- [theory-kubectl-vs-docker.md](./theory-kubectl-vs-docker.md)
- [troubleshoot-crashloopbackoff.md](./troubleshoot-crashloopbackoff.md)
- [troubleshoot-ingress-routing.md](./troubleshoot-ingress-routing.md)
- [troubleshoot-node-notready.md](./troubleshoot-node-notready.md)
