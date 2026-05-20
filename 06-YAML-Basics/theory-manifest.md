# IT에서 “매니페스트(Manifest)”란?

**매니페스트(manifest)** 는 IT 전반에서 흔히 **“어떤 시스템/애플리케이션이 ‘어떻게 존재해야 하는지’를 선언적으로 적어둔 파일(또는 설정 묶음)”** 을 의미합니다.  
즉, **실행 방법(절차)** 보다는 **원하는 최종 상태(Desired State)** 를 기술하는 경우가 많습니다.

- 예: “웹 서버 컨테이너는 nginx:1.27 이미지를 쓰고, 포트 80을 열고, 리플리카는 2개여야 한다”
- 매니페스트는 보통 **버전 관리(Git)** 와 함께 사용되며, **재현성/표준화/자동화** 의 핵심 재료가 됩니다.

---

## 1) 왜 “Manifest”라고 부르나?

원래 단어 뜻이 “명세서/목록/선적서” 같은 의미라서,
IT에서는 다음과 같이 확장되어 사용됩니다.

- **구성 요소 목록**: 무엇이 포함되는지(패키지, 의존성, 리소스)
- **설치/배포에 필요한 선언**: 어떤 설정이 적용되어야 하는지
- **정책/권한/환경 정보**: 누가 무엇을 할 수 있는지, 어떤 네트워크/리소스를 쓰는지

---

## 2) 매니페스트의 공통 특징

### ✅ 선언적(Declarative) 성향
- “이걸 실행해라(절차)”가 아니라 “이 상태가 되어야 한다(목표)”에 가깝습니다.
- 대표: Kubernetes YAML, Terraform HCL, CloudFormation 템플릿 등

### ✅ 재현성(Reproducibility)
- 같은 매니페스트를 적용하면 **항상 같은 결과**를 얻는 것이 목표입니다.

### ✅ 자동화/도구 연계
- 매니페스트는 보통 도구가 읽어서 적용합니다.
  - `kubectl apply -f ...`
  - `terraform apply`
  - `docker compose up`
  - CI/CD 파이프라인

### ✅ 소스코드처럼 관리(IaC, GitOps)
- “인프라도 코드다” (Infrastructure as Code)
- 운영 설정도 Git으로 관리하고 리뷰/배포 흐름에 올립니다.

---

## 3) 분야별 “Manifest” 대표 예시

### 3.1 Kubernetes Manifest (가장 흔한 ‘매니페스트’ 용례)
Kubernetes에서 매니페스트는 리소스의 원하는 상태를 YAML로 선언합니다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
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
```
---

## yaml review
```
apiVersion: v1                       # 이 리소스의 API 그룹/버전. Namespace는 core(v1)에 속함.
kind: Namespace                      # 만들 리소스 종류: 네임스페이스(논리적 격리 단위)
metadata:                            # 리소스 메타정보(이름/라벨/어노테이션 등)
  name: demo-hpa                     # 네임스페이스 이름. 이후 리소스들이 이 공간 안에 생성됨.

---
apiVersion: apps/v1                  # Deployment는 apps API 그룹의 v1을 사용
kind: Deployment                     # 만들 리소스 종류: Deployment (ReplicaSet을 통해 Pod 복제/롤링업데이트 관리)
metadata:
  name: nginx                        # Deployment 이름(네임스페이스 내 유일)
  namespace: demo-hpa                # 이 Deployment가 생성될 네임스페이스 지정 (없으면 default)
spec:                                # Deployment의 “원하는 상태(desired state)” 정의
  replicas: 2                        # 원하는 Pod 개수(초기값). HPA가 붙으면 이 값은 “기본”이고 실제는 HPA가 조정.
  selector:                          # 이 Deployment가 어떤 Pod를 “자기 것”으로 관리할지 선택 규칙
    matchLabels:                     # 라벨 매칭 방식(가장 흔함)
      app: nginx                     # 라벨 app=nginx 인 Pod를 이 Deployment가 관리(ReplicaSet 포함)
  template:                          # Deployment가 생성할 Pod의 템플릿(설계도)
    metadata:
      labels:                        # Pod에 붙일 라벨(서비스 셀렉터/디플로이 셀렉터와 일치해야 함)
        app: nginx                   # Pod 라벨. 위 selector.matchLabels 와 반드시 논리적으로 일치해야 함(불일치 시 오류/예상치 못한 동작).
    spec:                            # Pod 스펙(컨테이너/볼륨/노드스케줄링 등)
      containers:                    # Pod 안에서 실행될 컨테이너 목록(대부분 1개, sidecar면 여러 개)
      - name: nginx                  # 컨테이너 이름(해당 Pod 내에서 유일)
        image: nginx:1.27-alpine     # 사용할 컨테이너 이미지(태그 포함). Alpine 기반이라 가볍고 빠름.
        ports:
        - containerPort: 80          # 컨테이너 내부에서 listen 하는 포트 “정보”. (Service의 targetPort와 연결될 가능성이 큼)
                                     # 주의: 이 설정만으로 방화벽/노출이 되는 건 아니고, “메타 정보”에 가까움.

        # HPA는 requests를 기준으로 CPU Utilization(%) 계산
        resources:                   # 리소스 요청/제한을 설정(스케줄링/제한/오토스케일 기준에 영향)
          requests:                  # "요청(request)" = 이 컨테이너가 최소 이만큼은 필요하다고 선언
            cpu: "50m"               # 50 millicore = 0.05 vCPU. 
                                     # 스케줄러는 노드의 allocatable에서 requests 합을 보고 배치함.
                                     # HPA의 CPU Utilization(%) 계산에서 분모가 되는 기준이 됨(아래 설명).
            memory: "64Mi"           # 메모리 최소 요구량 64MiB. 스케줄링 시 이만큼 자리 필요.
          limits:                    # "제한(limit)" = 컨테이너가 최대 이 이상 쓰지 못하게 제한(강제)
            cpu: "300m"              # CPU 최대 0.3 vCPU 정도로 제한. 초과 사용 시 throttling(쓰로틀링) 발생.
            memory: "128Mi"          # 메모리 최대 128MiB. 초과 시 OOMKilled(강제 종료)될 수 있음.

---
apiVersion: v1                       # Service는 core(v1)
kind: Service                        # 만들 리소스 종류: Service (Pod 집합에 대한 안정적 가상 IP/이름 제공)
metadata:
  name: nginx-svc                    # 서비스 이름 (DNS: nginx-svc.demo-hpa.svc.cluster.local)
  namespace: demo-hpa                # 서비스가 속할 네임스페이스
spec:
  selector:                          # 어떤 Pod들을 이 서비스의 엔드포인트로 묶을지
    app: nginx                       # 라벨 app=nginx 인 Pod들이 대상(Deployment가 만든 Pod와 일치)
  ports:
  - port: 80                         # Service가 클러스터 내부에서 제공하는 포트(클라이언트는 이 포트로 접속)
    targetPort: 80                   # 실제 Pod(컨테이너)로 전달되는 포트(보통 containerPort와 동일)
                                     # (명시 안 하면 port와 동일하다고 간주)

---
apiVersion: autoscaling/v2           # HPA v2 API. behavior, multiple metrics 등 고급 설정 가능.
kind: HorizontalPodAutoscaler        # 만들 리소스 종류: HPA (수평 확장: Pod 개수 조절)
metadata:
  name: nginx-hpa                    # HPA 이름
  namespace: demo-hpa                # HPA가 적용될 네임스페이스(대상 Deployment와 동일해야 함)
spec:
  scaleTargetRef:                    # “어떤 대상”의 replicas를 조절할지 참조
    apiVersion: apps/v1              # 대상 리소스의 API 버전
    kind: Deployment                 # 대상 리소스 종류
    name: nginx                      # 대상 리소스 이름(= 위 Deployment nginx)
  minReplicas: 2                     # 최소 Pod 개수. replicas가 이보다 내려가지 않게 보장(가용성/HA 관점)
  maxReplicas: 4                     # 최대 Pod 개수. 무한 확장 방지(비용/안정성)
  metrics:                           # 오토스케일 판단에 사용할 지표 목록(복수 가능)
  - type: Resource                   # 리소스 기반 지표(CPU/Memory 등). (Pod 지표, External 지표 등도 가능)
    resource:
      name: cpu                      # 측정할 리소스: cpu
      target:
        type: Utilization            # “사용률(%)” 기반 목표
        averageUtilization: 50       # 목표: 평균 CPU 사용률을 50%로 맞추도록 Pod 수 조절
                                     # 여기서 50%는 "requests.cpu"를 기준으로 계산됨.
                                     # 예) requests=50m 인 Pod가 실제 25m 쓰면 utilization=50%
                                     # 예) 60m 쓰면 utilization=120% (요청치보다 많이 쓰는 상태)

  behavior:                          # 스케일 업/다운의 “속도/안정화” 정책 (v2의 핵심 고급 기능)
    scaleUp:                         # Pod를 늘릴 때(확장) 정책
      stabilizationWindowSeconds: 0  # 확장 시 “안정화 창” 0초 = 즉시 반영(가장 공격적인 확장)
                                     # (안정화 창은 최근 권고치들을 보고 급격한 변동을 완화)
      policies:                      # 확장 속도를 제한하는 규칙들(여러 개 가능)
      - type: Pods                   # 절대값 기준 정책
        value: 2                     # 한 번의 스케일 이벤트에서 최대 +2 Pod까지 증가 허용
        periodSeconds: 15            # 이 정책이 적용되는 기간(15초 단위로 평가)
      - type: Percent                # 비율 기준 정책
        value: 100                   # 한 번의 스케일 이벤트에서 현재 replicas의 최대 100%까지 증가 허용
                                     # 예) 현재 2개면 +2까지(=100% 증가)
                                     # 예) 현재 3개면 +3까지 허용하지만 maxReplicas=4 때문에 실제는 +1까지만 가능
        periodSeconds: 15            # 15초 단위
      selectPolicy: Max              # 여러 policies가 동시에 있을 때 “더 크게 늘릴 수 있는” 정책을 선택
                                     # 즉, Pods(+2) vs Percent(+100%) 중 더 큰 증가폭 허용을 채택.
                                     # 이 설정은 “부하 급증에 빨리 대응”하려는 공격적 확장 성향.
```
---
### apps라는 ‘API 그룹(API Group)’**이 Kubernetes에 있고, 그 그룹 안에 Deployment 같은 리소스 타입(kind) 이 들어있다는 뜻이에요.
```
정리하면:
apiVersion: apps/v1

apps = API 그룹 이름
v1 = 그 API 그룹의 버전

kind: Deployment
Deployment라는 리소스 타입(Kind) 을 만들겠다

즉, Kubernetes가 제공하는 건 이렇게 계층이 있어요:
```
---
#### 1) API 그룹 / 버전
```
v1 (core group) : Namespace, Pod, Service, ConfigMap 같은 것들
core는 그룹명이 생략돼서 그냥 v1처럼 보임
apps/v1 : Deployment, ReplicaSet, StatefulSet, DaemonSet 등
batch/v1 : Job, CronJob
networking.k8s.io/v1 : Ingress, NetworkPolicy
rbac.authorization.k8s.io/v1 : Role, ClusterRole 등
```
#### 2) 리소스 타입(Kind)
```
각 그룹/버전 아래에 실제 “종류”가 존재합니다.
예: apps/v1 아래에 Deployment, ReplicaSet, StatefulSet…
```
##### 왜 이렇게 나눠놨나?
```
기능 영역별로 API를 묶고(확장/관리 쉬움)
버전(v1, v1beta1 등)로 안정성/호환성 관리
CRD 같은 확장도 “그룹/버전” 형태로 추가 가능
```
---
```sh
ubuntu@cp1:~$ kubectl api-resources | head
NAME                                SHORTNAMES   APIVERSION                          NAMESPACED   KIND
bindings                                         v1                                  true         Binding
componentstatuses                   cs           v1                                  false        ComponentStatus
configmaps                          cm           v1                                  true         ConfigMap
endpoints                           ep           v1                                  true         Endpoints
events                              ev           v1                                  true         Event
limitranges                         limits       v1                                  true         LimitRange
namespaces                          ns           v1                                  false        Namespace
nodes                               no           v1                                  false        Node
persistentvolumeclaims              pvc          v1                                  true         PersistentVolumeClaim
```
### `kubectl api-resources | head` 문장 설명

`kubectl api-resources | head` 는 **“kubectl 출력 결과(텍스트)를 Linux의 `head`로 앞부분만 잘라서 본다”** 는 뜻입니다.  
즉, **Kubernetes 명령 + 리눅스 파이프/필터 명령**이 한 줄에 섞인 대표 패턴입니다.

---

#### 1) 각 토큰(단어) 역할 분해

#### ✅ Kubernetes 쪽: `kubectl api-resources`
- Kubernetes API 서버가 제공하는 **리소스 목록**(Pod, Service, Deployment 같은 “종류들”)을 표 형태로 출력합니다.
- 내부적으로는 “API에 어떤 리소스들이 등록돼 있는지”를 조회해 보여주는 명령입니다.

#### ✅ Linux 쪽: `|` 와 `head`
- **`|` (파이프)**  
  왼쪽 명령의 “출력(stdout)”을 오른쪽 명령의 “입력(stdin)”으로 넘겨줍니다.
- **`head`**  
  입력된 텍스트의 **앞 N줄만 출력**합니다.  
  옵션이 없으면 보통 **기본 10줄**을 출력합니다.

---

#### 2) 전체 문장은 무슨 의미?
- `kubectl api-resources` 출력은 리소스가 많아 **줄이 아주 길어질 수** 있습니다.
- 그래서 그 중 **맨 위 10줄만 빠르게 미리보기** 하겠다는 뜻입니다.

보통 첫 줄은 헤더(예: `NAME SHORTNAMES APIVERSION NAMESPACED KIND`)가 나오고,  
그 아래로 리소스들이 쭉 나옵니다. `head`가 그 중 앞부분만 잘라 보여줍니다.

---

#### 3) 자주 쓰는 변형

- **앞 20줄 보기**
  ```sh
  kubectl api-resources | head -n 20
  ```

- **헤더 제외하고 10줄 보기**
  ```sh
  kubectl api-resources | tail -n +2 | head
  ```
  - `tail -n +2` 도 **리눅스 명령**이며, 2번째 줄부터 출력(=첫 줄 헤더 제거)하는 패턴입니다.
---


```
ubuntu@cp1:~$ kubectl api-resources | grep -i deployment
deployments                         deploy       apps/v1                             true         Deployment
ubuntu@cp1:~$
```
### `kubectl api-resources | grep -i deployment` 문장 설명

`kubectl api-resources | grep -i deployment` 는 **“클러스터가 제공하는 리소스 목록에서 ‘deployment’가 들어간 줄만(대소문자 무시하고) 걸러서 본다”** 는 뜻입니다.  
즉, **Kubernetes 출력 + Linux 텍스트 필터링** 조합입니다.

---

#### 1) 각 토큰(단어) 역할 분해

#### ✅ Kubernetes 쪽: `kubectl api-resources`
- API 서버가 제공하는 **리소스 종류 목록**을 표로 출력합니다.  
  (예: pods, services, deployments, replicasets …)

#### ✅ Linux 쪽: `| grep -i deployment`
- **`|` (파이프)**: 왼쪽 출력(stdout)을 오른쪽 입력(stdin)으로 전달
- **`grep`**: 입력 텍스트에서 **패턴이 포함된 줄만 출력**
- **`-i`**: 대소문자 무시 (Deployment / deployment / DEPLOYMENT 모두 매칭)
- **`deployment`**: 찾고 싶은 키워드(패턴)

---

#### 2) 전체 문장이 하는 일
- `kubectl api-resources` 전체 목록은 너무 길 수 있으니,
- 그중에서 **Deployment 관련 줄만 빠르게 찾는 용도**입니다.

예를 들어 보통 이런 줄이 잡힙니다(환경에 따라 조금 다름):

- `deployments  deploy  apps/v1  true  Deployment`

즉,
- **deployments**: 리소스 “이름”(복수형)
- **deploy**: 짧은 별칭(shortname)
- **apps/v1**: API 그룹/버전
- **true**: 네임스페이스 리소스인지 여부
- **Deployment**: Kind(리소스 타입 이름)


#### `kubectl apply ./deploy.yaml`
- `apply`는 파일을 직접 인자로 받지 않고 **`-f`가 필요**
```sh
kubectl apply -f ./deploy.yaml
```
---
#### linux 명령어 연습
```sh
sed -n '1,30p' ./deploy.yaml
grep -n "apiVersion" ./deploy.yaml
cat -A ./deploy.yaml | sed -n '1,30p'
```
---
---
