# kubectl explain로 Probe(startup/liveness/readiness) 및 gRPC 지원 여부 확인

아래 명령들로 **현재 kubectl이 연결된 클러스터의 OpenAPI 스키마 기준**으로  
`startupProbe/livenessProbe/readinessProbe`와 **grpc/httpGet/exec/tcpSocket** 지원 여부를 확인할 수 있습니다.

---

## 1) 컨테이너 Probe 필드 3종이 있는지 확인

```bash
kubectl explain pod.spec.containers.startupProbe
kubectl explain pod.spec.containers.livenessProbe
kubectl explain pod.spec.containers.readinessProbe
```

- 각각의 설명/필드 목록이 출력되면 해당 probe 필드는 지원되는 것입니다.

---

## 2) Probe 객체 구조(공통 파라미터) 확인

```bash
kubectl explain pod.spec.containers.livenessProbe --recursive
```

출력에서 보이는 대표 공통 파라미터:
- `initialDelaySeconds`
- `periodSeconds`
- `timeoutSeconds`
- `failureThreshold`
- `successThreshold`

---

## 3) 프로브 핸들러(검사 방식) 지원 확인: httpGet / exec / tcpSocket / grpc

Probe에는 “어떤 방식으로 검사할지(핸들러)”가 들어갑니다.  
재귀 출력으로 지원 여부가 바로 드러납니다.

### A) HTTP GET
```bash
kubectl explain pod.spec.containers.livenessProbe.httpGet --recursive
```

### B) Exec
```bash
kubectl explain pod.spec.containers.livenessProbe.exec --recursive
```

### C) TCP Socket
```bash
kubectl explain pod.spec.containers.livenessProbe.tcpSocket --recursive
```

### D) gRPC (지원 여부 확인 핵심)
```bash
kubectl explain pod.spec.containers.livenessProbe.grpc --recursive
```

- **지원**이면 `grpc:` 아래에 `port`, `service` 등의 필드 설명이 나옵니다.
- **미지원**이면 보통 `field "grpc" does not exist` 류로 나오거나, recursive 출력에 `grpc`가 아예 보이지 않습니다.

---

## 4) 한 번에 핸들러 지원 여부만 빠르게 보기

```bash
kubectl explain pod.spec.containers.livenessProbe --recursive | egrep -n "httpGet|exec|tcpSocket|grpc"
```

---

## 5) startupProbe가 어떻게 동작하는지 스키마로 확인

```bash
kubectl explain pod.spec.containers.startupProbe --recursive | egrep -n "failureThreshold|periodSeconds|timeoutSeconds|httpGet|exec|tcpSocket|grpc"
```

---

## 6) (참고) 클러스터 버전 확인

gRPC probe 같은 기능은 Kubernetes 버전에 따라 지원 여부가 달라질 수 있으니 버전도 함께 확인하면 좋습니다.

```bash
kubectl version --short
kubectl get nodes -o wide
```
