# livenessProbe 실패로 재시작되는 이유 (CrashLoopBackOff와의 관계)

## 1) 결론부터: livenessProbe는 “살아있는지” 검사이고, 실패하면 kubelet이 컨테이너를 **죽이고 재시작**한다

Kubernetes에서 `livenessProbe`는 컨테이너가 **정상적으로 살아있는지**(hung/deadlock/무한대기 등) 확인하기 위한 건강검사입니다.

- `livenessProbe`가 **연속으로 실패**하면 kubelet은 “이 컨테이너는 죽었다/응답 불능이다”라고 판단하고,
- 해당 컨테이너를 **강제로 종료(kill)** 한 다음,
- Pod의 `restartPolicy`가 `Always`(Deployment 기본)라면 **즉시 재시작**합니다.

이 과정이 반복되면, 컨테이너가 계속 재시작되면서 `CrashLoopBackOff` 상태로 보이게 됩니다.

---

## 2) kubelet의 동작 흐름 (왜 “재시작”이 일어나나)

`livenessProbe` 실패 → kubelet은 컨테이너 런타임(containerd 등)에 종료를 요청합니다.

1. kubelet이 주기적으로 livenessProbe 실행
2. probe가 실패(HTTP/exec/tcp 실패)  
3. 실패 횟수가 `failureThreshold`에 도달하면:
   - kubelet이 컨테이너를 **Restart 대상으로 판단**
4. kubelet이 컨테이너 종료(SIGTERM → 유예시간 후 SIGKILL) 처리
5. `restartPolicy=Always`이면 컨테이너를 다시 실행
6. 다시 livenessProbe 실행 → 또 실패하면 반복
7. 반복이 심하면 kubelet이 재시작 간격을 늘리며(backoff) → `CrashLoopBackOff`

---

## 3) 자주 발생하는 원인 (livenessProbe “설정이 너무 빡빡한” 케이스)

### A. 앱이 “느리게 뜨는”데 livenessProbe가 너무 빨리 검사함
예: Spring Boot/Node 앱이 20~60초 걸려 뜨는데  
- `initialDelaySeconds`가 너무 짧고
- `timeoutSeconds`가 너무 짧고
- `failureThreshold`가 낮으면

앱이 정상 부팅 중인데도 “응답 없음”으로 판단해서 계속 재시작합니다.

✅ 해결:
- `startupProbe`를 추가하거나
- livenessProbe 시작을 늦추고(초기 지연),
- timeout/failureThreshold를 완화

---

### B. livenessProbe가 “실제 헬스체크 엔드포인트”가 아닌 곳을 찌름
- `/`가 아니라 `/healthz` 같은 전용 엔드포인트를 써야 하는데
- 인증 필요/리다이렉트/404가 나오는 경로를 검사함
- 혹은 앱이 특정 헤더 없으면 403을 주는 경로를 검사함

✅ 해결:
- 인증 불필요, 빠르고 가벼운 전용 health endpoint 사용
- HTTP status 200을 반환하도록 설계

---

### C. CPU/메모리 압박으로 응답이 순간적으로 늦어짐
- 부하 시 응답 지연 → probe timeout 발생 → 연속 실패 → 재시작

✅ 해결:
- `timeoutSeconds` 증가
- 리소스 requests/limits 조정
- 앱의 health endpoint는 매우 가볍게(의존성 호출 최소화)

---

### D. 헬스체크 엔드포인트가 “외부 의존성”까지 포함
예: `/health`가 DB/Redis/외부 API까지 체크해서  
DB가 잠깐만 느려도 liveness 실패 → 컨테이너 재시작

✅ 권장 설계:
- **liveness**: “프로세스가 살아있나?” (가벼움, 내부 상태 위주)
- **readiness**: “트래픽 받아도 되나?” (의존성 포함 가능)

---

## 4) readinessProbe와 차이 (매우 중요)

| 구분 | 실패 시 영향 | 목적 |
|---|---|---|
| livenessProbe | 컨테이너를 **죽이고 재시작** | 프로세스가 “살아있는지” |
| readinessProbe | Service Endpoint에서 **제외**(트래픽 차단) | “준비가 되었는지” |
| startupProbe | 앱 기동 중에는 liveness/readiness를 “대신” 담당 | 느린 기동 보호 |

- readiness 실패는 보통 재시작을 유발하지 않습니다.
- 재시작 루프를 만드는 건 주로 **liveness/startup** 쪽 문제입니다.

---

## 5) 현장에서 흔한 “권장 설정 패턴”

### (1) 느리게 뜨는 앱: startupProbe를 쓰고 liveness는 보수적으로
```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30   # 30번까지 실패 허용
  periodSeconds: 2       # 2초마다 검사 => 최대 60초 부팅 허용

livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3
```

### (2) readiness는 “트래픽 수용 가능 여부”에 집중
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3
```

---

## 6) 진단 커맨드: “probe 실패로 재시작 중인지” 확인

1) Pod 이벤트에서 Unhealthy / probe 메시지 확인
```bash
kubectl -n <ns> describe pod <pod> | egrep -n "Unhealthy|Liveness|Readiness|Startup|probe"
kubectl -n default describe pod my-backend-rest-app-588459ddc5-czwp5 | egrep -n "Unhealthy|Liveness|Readiness|Startup|probe"

```

2) 컨테이너 재시작 횟수/상태 확인
```bash
kubectl -n <ns> get pod <pod> -o wide
kubectl -n <ns> get pod <pod> -o jsonpath='{.status.containerStatuses[0].restartCount}'; echo
```

3) (가능하면) 컨테이너 직전 로그 확인
```bash
kubectl -n <ns> logs <pod> --previous
kubectl -n default logs my-backend-rest-app-588459ddc5-r8vgf --previous
```

---

## 7) 요약

- `livenessProbe`는 “살아있나?” 검사이고, **연속 실패하면 kubelet이 컨테이너를 죽이고 재시작**합니다.
- 설정이 너무 공격적이면 정상 부팅 중/일시적인 지연에도 재시작이 반복되어 `CrashLoopBackOff`로 이어질 수 있습니다.
- 느린 기동은 `startupProbe`로 보호하고,  
  `livenessProbe`는 가볍고 보수적으로,  
  `readinessProbe`는 트래픽 수용 여부에 맞추는 것이 안정적입니다.



# livenessProbe 실패로 재시작되는 이유 (CrashLoopBackOff와의 관계) + FastAPI 실습 (Python)

> 이 문서는 `livenessProbe` 실패가 **컨테이너 재시작**을 유발하는 이유와, 그 결과로 **CrashLoopBackOff**가 발생하는 흐름을 설명하고  
> FastAPI(Python) 기반으로 **재현 → 관찰 → 해결**까지 실습할 수 있는 예시를 제공합니다.

---

## 1) 결론: livenessProbe는 “살아있는지” 검사, 실패하면 kubelet이 **죽이고 재시작**

Kubernetes에서 `livenessProbe`는 컨테이너가 **정상적으로 살아있는지**(hung/deadlock/무한대기 등) 확인하기 위한 건강검사입니다.

- `livenessProbe`가 **연속으로 실패**하면 kubelet은 “이 컨테이너는 응답 불능이다”라고 판단하고
- 해당 컨테이너를 **강제로 종료(SIGTERM → 유예시간 후 SIGKILL)** 한 뒤
- Pod의 `restartPolicy=Always`(Deployment 기본)면 **즉시 재시작**합니다.

이 과정이 반복되면, 컨테이너가 계속 재시작되면서 `CrashLoopBackOff` 상태로 보이게 됩니다.

---

## 2) kubelet 동작 흐름: 왜 “재시작”이 발생하나

`livenessProbe` 실패 → kubelet은 컨테이너 런타임(containerd 등)에 종료를 요청합니다.

1. kubelet이 주기적으로 livenessProbe 실행
2. probe가 실패(HTTP/exec/tcp 실패)
3. 실패 횟수가 `failureThreshold`에 도달하면 컨테이너를 **Restart 대상으로 판단**
4. kubelet이 컨테이너 종료(SIGTERM → SIGKILL) 처리
5. `restartPolicy=Always`이면 컨테이너를 다시 실행
6. 다시 livenessProbe 실행 → 또 실패하면 반복
7. 반복이 심하면 kubelet이 재시작 간격을 늘리며(backoff) → `CrashLoopBackOff`

---

## 3) 자주 발생하는 원인 (livenessProbe 설정이 “너무 빡빡한” 케이스)

### A. 앱이 느리게 뜨는데, livenessProbe가 너무 빨리 검사
예: Spring Boot/Node/Python 앱이 20~60초 걸려 뜨는데  
- `initialDelaySeconds`가 너무 짧고
- `timeoutSeconds`가 너무 짧고
- `failureThreshold`가 낮으면

앱이 정상 부팅 중인데도 “응답 없음”으로 판단해서 계속 재시작합니다.

✅ 해결:
- `startupProbe`를 추가하거나
- livenessProbe 시작을 늦추고(초기 지연)
- timeout/failureThreshold를 완화

---

### B. livenessProbe가 실제 헬스체크 엔드포인트가 아닌 곳을 찌름
- `/`가 아니라 `/healthz` 같은 전용 엔드포인트를 써야 하는데
- 인증 필요/리다이렉트/404/403이 나는 경로를 검사함

✅ 해결:
- 인증 불필요, 빠르고 가벼운 전용 health endpoint 사용
- HTTP status 200을 반환하도록 설계

---

### C. CPU/메모리 압박으로 응답이 순간적으로 늦어짐
- 부하 시 응답 지연 → probe timeout 발생 → 연속 실패 → 재시작

✅ 해결:
- `timeoutSeconds` 증가
- 리소스 requests/limits 조정
- health endpoint는 매우 가볍게(의존성 호출 최소화)

---

### D. 헬스체크가 외부 의존성까지 포함
예: `/health`가 DB/Redis/외부 API까지 체크해서  
DB가 잠깐만 느려도 liveness 실패 → 컨테이너 재시작

✅ 권장 설계:
- **liveness**: “프로세스가 살아있나?” (가벼움, 내부 상태 위주)
- **readiness**: “트래픽 받아도 되나?” (의존성 포함 가능)

---

## 4) readinessProbe와 차이 (매우 중요)

| 구분 | 실패 시 영향 | 목적 |
|---|---|---|
| livenessProbe | 컨테이너를 **죽이고 재시작** | 프로세스가 “살아있는지” |
| readinessProbe | Service Endpoint에서 **제외**(트래픽 차단) | “준비가 되었는지” |
| startupProbe | 앱 기동 중에는 liveness/readiness를 “대신” 담당 | 느린 기동 보호 |

- readiness 실패는 보통 재시작을 유발하지 않습니다.
- 재시작 루프를 만드는 건 주로 **liveness/startup** 쪽 문제입니다.

---

## 5) 권장 설정 패턴 예시

### (1) 느리게 뜨는 앱: startupProbe 사용 + liveness는 보수적으로
```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30   # 30번까지 실패 허용
  periodSeconds: 2       # 2초마다 검사 => 최대 60초 부팅 허용

livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3
```

### (2) readiness는 “트래픽 수용 가능 여부”에 집중
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3
```

---

## 6) 진단 커맨드: probe 실패로 재시작 중인지 확인

1) Pod 이벤트에서 Unhealthy / probe 메시지 확인
```bash
kubectl -n <ns> describe pod <pod> | egrep -n "Unhealthy|Liveness|Readiness|Startup|probe"
```

2) 컨테이너 재시작 횟수/상태 확인
```bash
kubectl -n <ns> get pod <pod> -o wide
kubectl -n <ns> get pod <pod> -o jsonpath='{.status.containerStatuses[0].restartCount}'; echo
```

3) 컨테이너 직전 로그 확인
```bash
kubectl -n <ns> logs <pod> --previous
```

---


# FastAPI(Python) 실습: livenessProbe 실패 → CrashLoopBackOff 재현/관찰/해결

## 목표 시나리오
1. FastAPI 앱이 `/healthz`를 제공한다.
2. **livenessProbe가 틀린 포트**를 찌르게 해서 항상 실패하도록 만든다.
3. kubelet이 컨테이너 kill/restart 반복 → 재시작 backoff로 **CrashLoopBackOff**가 된다.
4. YAML을 고쳐서(정상 포트/`startupProbe` 추가 등) 안정화한다.

---

## 1) FastAPI 앱 코드 (health endpoint 포함)

### `main.py`
```python
from fastapi import FastAPI
import os
import time

app = FastAPI()
