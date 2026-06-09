# Kubernetes 아키텍처

## Step-01: 왜 Kubernetes인가?
- **문제 배경**
  - 마이크로서비스가 늘어나면서 컨테이너 수가 많아지고, 수동 운영이 어려워집니다.
  - 장애 복구, 스케일링, 배포 롤백 같은 작업을 자동화할 필요가 있습니다.
- **Kubernetes의 역할**
  - 컨테이너 오케스트레이션: 컨테이너 스케줄링, 상태 관리, 자동 복구
  - 서비스 디스커버리/로드밸런싱: 안정적 서비스 노출
  - 선언형 운영: 원하는 상태를 정의하면 시스템이 맞춰줌

## Step-02: Kubernetes 아키텍처
- **Control Plane (관리 영역)**
  - API Server: 모든 요청의 진입점이며 인증/인가/어드미션을 처리합니다.
  - Scheduler: 어떤 노드에 Pod를 배치할지 결정합니다.
  - Controller Manager: ReplicaSet/Deployment 등 컨트롤러 루프를 실행합니다.
  - etcd: 클러스터의 모든 상태를 저장하는 분산 키-값 저장소입니다.
- **Node (작업 노드)**
  - kubelet: 노드에서 Pod 실행을 책임지는 에이전트입니다.
  - Container Runtime: 컨테이너 실행(예: containerd)
  - kube-proxy: Service 트래픽 라우팅/로드밸런싱을 담당합니다.

---
```
1) Kubernetes에서 “Container Runtime”이 하는 일

노드에서 kubelet이 “이 Pod 띄워!”라고 지시하면, 실제로는 Container Runtime이 아래를 수행합니다.

이미지 pull (레지스트리에서 내려받기)

컨테이너 생성/시작/중지/삭제

cgroups / namespaces 적용(리눅스 격리)

네트워크/스토리지(볼륨) 연결

로그/상태 리포팅(런타임 레벨)

K8s는 kubelet이 런타임과 대화할 때 CRI(Container Runtime Interface) 라는 표준 인터페이스를 씁니다.

2) containerd vs Docker: 무엇이 다른가?
containerd

“런타임(실행) 중심” 컴포넌트

컨테이너 실행/관리 기능을 제공하는 daemon

보통 내부적으로 runc(OCI 런타임) 를 호출해서 실제 컨테이너 프로세스를 띄움

K8s와는 CRI 플러그인(cri-containerd) 를 통해 자연스럽게 붙음

즉, K8s가 원하는 “컨테이너 실행기” 역할에 딱 맞는 구조입니다.

Docker (정확히는 Docker Engine)

Docker는 historically 다음을 한 번에 제공했어요.

이미지 빌드(Dockerfile → 이미지)

이미지 관리/배포(pull/push)

컨테이너 실행

CLI/UX( docker build, docker run 등)

예전에는 내부에 dockerd + containerd + runc 같은 계층이 같이 있었음

즉 Docker는 개발자 경험(빌드/실행/배포를 한 번에) 까지 포함한 “풀 패키지”에 가까워요.

3) “K8s에서 Docker를 런타임으로 쓰는 것”이 왜 줄었나?

예전엔 Kubernetes가 dockershim 이라는 중간 어댑터를 통해 Docker Engine(dockerd)과 직접 붙었는데,
지금은 Kubernetes가 CRI를 표준으로 강제하면서 containerd/CRI-O 같은 CRI 지원 런타임을 권장/기본으로 씁니다.

정리하면:

K8s 관점: “CRI로 말할 수 있는 런타임이 필요” → containerd/CRI-O가 정석

Docker Engine: K8s가 원하는 형태(CRI)가 아니어서 중간 어댑터(dockershim)가 필요했음

4) 그럼 Docker는 이제 K8s에서 못 쓰나?

개발/빌드 도구로서는 여전히 매우 많이 씁니다.

로컬에서 docker build로 이미지를 만들고

레지스트리에 push

K8s 노드는 containerd 가 그 이미지를 pull 해서 실행

즉,

Docker = 빌드/배포 도구(이미지 제작/관리)

containerd = 실행 도구(노드에서 컨테이너 실제 구동)
이 조합이 흔합니다.

5) 한 줄 비유

Docker: “주방(빌드) + 배달(푸시/풀) + 조리(실행)까지 다 있는 프랜차이즈”

containerd: “조리 담당(실행) 파트만 깔끔하게 분리한 엔진”

Kubernetes: “주문서(CRI)로 조리 담당에게 지시하는 매니저(kubelet)”
```
---
```
1) k3s에서 기본 구조

k3s 프로세스 안에(또는 함께) containerd가 같이 돌아갑니다.

kubelet(k3s에 내장)이 CRI로 containerd에 “Pod 띄워”를 요청합니다.

Docker Engine(dockerd)는 기본 구성에 포함되지 않습니다. (설치돼 있을 수는 있지만 k3s 기본 경로는 containerd)

2) “docker ps가 안 보이는” 이유 (가장 흔한 오해)

k3s가 containerd로 컨테이너를 띄우면, 그 컨테이너들은 Docker Engine이 관리하는 컨테이너가 아니에요.
그래서 노드에서 docker ps를 쳐도 K8s(Pod) 컨테이너가 안 보이거나, Docker로 따로 띄운 것만 보입니다.

대신 아래가 정석이에요.

(A) crictl로 보기 (CRI 표준 툴)
```

```
sudo crictl ps
sudo crictl images
sudo crictl pods
```
(B) ctr로 보기 (containerd 네이티브 툴)

k8s 컨테이너는 containerd의 k8s 네임스페이스에 들어가므로:(B) ctr로 보기 (containerd 네이티브 툴)

k8s 컨테이너는 containerd의 k8s 네임스페이스에 들어가므로:
```
sudo ctr -n k8s.io containers ls
sudo ctr -n k8s.io tasks ls
sudo ctr -n k8s.io images ls
```
3) k3s의 containerd 소켓 위치(자주 쓰는 경로)

환경/버전에 따라 조금씩 다를 수 있는데, k3s는 보통 이런 쪽에 소켓이 있습니다.

/run/k3s/containerd/containerd.sock (k3s가 번들 containerd를 쓰는 대표 케이스)

(일반 k8s/containerd) /run/containerd/containerd.sock

그래서 crictl이 안 잡히면 이런 식으로 확인합니다:
```
sudo crictl info
# 또는
sudo crictl --runtime-endpoint unix:///run/k3s/containerd/containerd.sock info
```
4) “Docker 없이도 이미지 빌드/배포는 어떻게?”

k3s 노드 런타임이 containerd인 것과 “이미지 빌드”는 별개입니다.

개발 PC: Docker로 빌드 → 레지스트리에 push → k3s가 pull 해서 실행 (가장 흔함)

Docker 없이도 빌드 가능:

buildctl(BuildKit)

kaniko(클러스터 안에서 빌드)

nerdctl(containerd용 docker-like CLI)

예: nerdctl은 Docker CLI 느낌으로 containerd를 다룹니다.
```
sudo nerdctl -n k8s.io ps
sudo nerdctl images
```
5) 결론(한 문장)

k3s에서는 “컨테이너 실행(런타임)”을 Docker가 아니라 containerd가 담당하고,
Docker는 있다면 보통 이미지 빌드/개발 편의용이지 k3s의 기본 실행 경로가 아닙니다.
---
---

1) kubelet이 하는 일(노드 관점)

kubelet은 노드에서 Pod를 ‘실제로’ 원하는 상태로 유지하는 에이전트입니다.

스케줄된 Pod를 감지(“이 노드에 nginx Pod 배치됨”)

Container Runtime(containerd)에 CRI로 요청

이미지 pull / 컨테이너 생성 / 시작

볼륨 마운트, 환경변수/시크릿 주입

liveness/readiness probe 실행

Pod 상태를 API 서버에 보고(Ready/NotReady 등)

노드 상태(NodeStatus), 자원 사용량(요약) 보고

로그/exec/port-forward 같은 기능의 기반 제공(간접적으로)

### 2) k3s에서 kubelet “프로세스” 확인 예시
일반 kubeadm 클러스터면 kubelet 프로세스가 따로 보이는데, k3s는 k3s가 kubelet 역할을 포함해서 아래처럼 보이는 경우가 많습니다.

```
ps -ef | egrep 'k3s|kubelet' | grep -v egrep
```

---
### 이 명령어는 리눅스 서버에서 "k3s나 kubelet이라는 단어가 들어간 실행 중인 프로그램(프로세스)을 찾되, 검색하는 과정 자체는 결과에서 제외하라"는 뜻입니다.

> 쉽게 말해, 내 서버에서 쿠버네티스(k3s 또는 kubelet)가 잘 돌아가고 있는지 확인하는 명령어예요.

- 명령어가 기니까 | (파이프) 기호를 기준으로 3단막극으로 나누어서 설명해 드릴게요.

### 1단계: ps -ef (지금 컴퓨터에서 뭐 돌아가고 있어?)
> ps (Process Status): 현재 실행 중인 프로그램들을 보여달라는 명령어입니다.

-ef: 옵션입니다. 모든 사용자(-e)의 프로세스를 아주 상세히/풀 포맷(-f)으로 보여달라는 뜻이에요.

> 이거만 치면 화면에 수백 줄의 컴퓨터 작동 기록이 엄청 빠르게 지나갑니다.

2단계: | egrep 'k3s|kubelet' (그중에서 k3s나 kubelet만 골라내봐)
| (파이프): 앞 단계의 결과물을 뒷 단계의 입력물로 넘겨주는 연결고리입니다.

egrep 'k3s|kubelet': 확장된 grep 명령어입니다. | 기호를 사용해 또는(OR) 연산을 합니다. 즉, 앞서 나온 수백 개의 프로세스 중 이름에 k3s 또는 kubelet이 포함된 줄만 필터링해서 보여줍니다.

3단계: | grep -v egrep (내가 방금 검색한 명령어는 빼고 보여줘)
grep -v: -v 옵션은 'Invert match'의 약자로, "이 단어가 들어간 줄은 제외해라"라는 뜻입니다.

왜 egrep을 제외할까요? 2단계를 실행하는 순간, 리눅스 안에서는 egrep 'k3s|kubelet'이라는 검색 명령어 자체도 하나의 프로그램으로 실행됩니다. 그래서 아무 조치도 안 하면 검색 결과에 내가 방금 입력한 검색 명령어 줄이 꼽사리 껴서 출력됩니다.

그걸 방지하기 위해 "검색어(egrep)가 들어간 줄은 깔끔하게 지우고, 진짜 돌아가고 있는 k3s나 kubelet 프로세스만 보여줘"라고 거르는 작업입니다.

한 줄 요약
"내 서버에서 k3s나 kubelet 프로세스가 실제로 살아있는지 화면에 깔끔하게 딱 그것만 띄워봐!" 라는 뜻입니다.

---


보통 결과에 k3s server ... 또는 k3s agent ...가 보이고

“kubelet” 관련 플래그/로그가 k3s 안에서 처리됩니다.

3) kubelet이 런타임(containerd)와 연결되는 것 확인(예시)

kubelet(=k3s)이 어떤 런타임 소켓을 쓰는지 확인하는 대표 예시:

(A) k3s 서비스 상태/로그에서 kubelet 성격의 로그 보기
```
sudo systemctl status k3s
sudo journalctl -u k3s -n 200 --no-pager
```

Agent 노드라면:
```
sudo systemctl status k3s-agent
sudo journalctl -u k3s-agent -n 200 --no-pager
```

여기서 containerd, cri, runtime endpoint 같은 단서가 나오는 경우가 많아요.

(B) CRI 관점에서 “kubelet이 보는 런타임” 확인
```
sudo crictl info
```

안 되면 소켓을 명시:
```
sudo crictl --runtime-endpoint unix:///run/k3s/containerd/containerd.sock info
```

이 결과가 “kubelet이 붙어있는 런타임이 containerd”라는 걸 실무적으로 확인하는 가장 빠른 방법입니다.

4) kubelet 동작 예시(“Pod 하나 배치 → 컨테이너 실행” 흐름)

예: nginx 배포하면
```
kubectl create deploy nginx --image=nginx:1.27-alpine
kubectl get pod -o wide
```

이때 내부적으로는:

Scheduler가 “nginx Pod → 노드 cp1” 같은 결정을 내림

해당 노드의 kubelet(k3s) 이 PodSpec을 받고

containerd(CRI) 에 요청 → 이미지 pull → 컨테이너 실행

kubelet이 readiness/liveness 체크, 상태를 API 서버에 보고

노드에서 실제로 확인하는 예시:

K8s 관점:
```
kubectl describe pod <pod명>
```

런타임 관점(crictl):
```
sudo crictl ps
sudo crictl pods
sudo crictl images
```

containerd 네이티브 관점(네임스페이스 중요):
```
sudo ctr -n k8s.io containers ls
sudo ctr -n k8s.io tasks ls
```
5) “kubelet이 죽으면 뭐가 보이나?”(현상 예시)

kubelet(=k3s agent/server의 노드 에이전트 부분)이 정상 보고를 못 하면:

kubectl get nodes에서 해당 노드가 NotReady로 바뀜

새 Pod가 그 노드에 배치돼도 실행/상태보고가 꼬일 수 있음

### 확인 예시:
```
kubectl get nodes -o wide
kubectl describe node <노드명>
```
---
---

## 추가 설명
- **Kubernetes vs AWS EKS**
  - EKS는 Control Plane을 AWS에서 관리해주므로 운영 부담이 줄어듭니다.
  - 노드(EC2)는 사용자가 관리하거나, Managed Node Group으로 관리합니다.
- **Control Plane 고가용성**
  - 운영 환경에서는 API Server/etcd를 다중화해 장애에 대비합니다.
  - etcd 백업은 클러스터 복구의 핵심 포인트입니다.
- **핵심 개념 정리**
  - Pod: 컨테이너를 실행하는 최소 단위
  - ReplicaSet: Pod 복제/복구를 담당
  - Deployment: 롤링 업데이트/롤백을 지원하는 상위 리소스
  - Service: 네트워크 접근을 제공하는 추상화

---

쿠버네티스(Kubernetes)에서 컨테이너의 최소 배포 단위를 Pod(팟)이라고 부르는 이유는, 영어 단어 Pod의 원래 뜻인 '고래의 무리' 또는 '완두콩 꼬투리'에서 유래했기 때문입니다.

쿠버네티스의 로고와 생태계를 보면 이 비유가 아주 직관적으로 이해됩니다.

1. 완두콩 꼬투리 (A pod of peas)
비유: 완두콩 꼬투리(Pod)를 까보면 그 안에 여러 개의 완두콩 알맹이들이 긴밀하게 모여 있습니다.

의미: 쿠버네티스에서 Pod는 하나 또는 그 이상의 컨테이너(완두콩)들을 감싸고 있는 껍질입니다. 이 컨테이너들은 한 껍질(Pod) 안에서 네트워크와 저장 공간을 공유하며 마치 하나의 프로그램처럼 끈끈하게 움직입니다.

2. 고래의 무리 (A pod of whales)
비유: 영어에서 고래나 돌고래가 떼를 지어 다닐 때 이를 'A pod of whales'라고 부릅니다.

의미: 도커(Docker)의 마스코트가 바로 '컨테이너를 싣고 다니는 고래'인 것 기억하시나요? 쿠버네티스는 이 고래(컨테이너)들을 관리하는 시스템입니다. 따라서 고래들이 무리 지어 다니는 모습을 나타내기 위해 Pod라는 단어를 선택한 것입니다.

요약하자면
"도커가 하나의 **고래(컨테이너)**라면, 쿠버네티스는 그 고래들이 무리 지어(Pod) 유기적으로 움직이게 관리하는 시스템이다"라는 위트 있는 비유에서 탄생한 이름입니다.


---

```bash
helm repo add headlamp https://kubernetes-sigs.github.io/headlamp/
helm repo update

# 설치
helm install headlamp headlamp/headlamp \
  --namespace headlamp \
  --create-namespace \
  --set service.type=NodePort \
  --set service.nodePort=30080
```

---
```
ubuntu@controller-node:~$ helm install headlamp headlamp/headlamp \
  --namespace headlamp \
  --create-namespace \
  --set service.type=NodePort \
  --set service.nodePort=30080
NAME: headlamp
LAST DEPLOYED: Tue Jun  9 05:02:34 2026
NAMESPACE: headlamp
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  export NODE_PORT=$(kubectl get --namespace headlamp -o jsonpath="{.spec.ports[0].nodePort}" services headlamp)
  export NODE_IP=$(kubectl get nodes --namespace headlamp -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
2. Get the token using
  kubectl create token headlamp --namespace headlamp
```

---
### 영문 사이트 아닐 경우 - ?lng=en