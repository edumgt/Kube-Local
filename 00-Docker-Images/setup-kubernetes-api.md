# Kubernetes API 설치 가이드 (192.168.253.146)

> 대상 서버: `ssh ubuntu@192.168.253.146`  
> 배포판: k3s (경량 Kubernetes)  
> OS: Ubuntu 22.04 LTS

---

## 0) 사전 준비

### 0-1) SSH 접속 확인

```sh
ssh ubuntu@192.168.253.146
```

초기 접속 시 fingerprint 확인이 나오면 `yes` 입력.

### 0-2) 기본 패키지 업데이트

```sh
sudo apt update && sudo apt upgrade -y
```

---

## 1) k3s 설치 (Control Plane + API Server)

### 1-1) k3s 설치 스크립트 실행

```sh
curl -sfL https://get.k3s.io | sh -
```

설치 완료 후 자동으로 아래가 구성됩니다:
- Kubernetes API Server (포트 6443)
- etcd (내장)
- kube-scheduler, kube-controller-manager
- kubectl (k3s kubectl로 사용 가능)

### 1-2) 서비스 상태 확인

```sh
sudo systemctl status k3s --no-pager -l
```

정상 예시:
```text
Active: active (running)
```

### 1-3) 노드 확인

```sh
sudo k3s kubectl get nodes
```

정상 예시:
```text
NAME     STATUS   ROLES                  AGE   VERSION
cp1      Ready    control-plane,master   1m    v1.34.x+k3s1
```

---

## 2) kubectl 일반 사용자 설정

k3s 설치 후 kubeconfig는 기본적으로 root 권한으로만 접근 가능합니다.  
`ubuntu` 사용자가 편하게 사용하려면 홈 디렉토리로 복사합니다.

```sh
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown ubuntu:ubuntu ~/.kube/config
chmod 600 ~/.kube/config
```

### 2-1) 동작 확인

```sh
kubectl get nodes
kubectl get pods -A
```

---

## 3) API Server 외부 접근 설정 (원격 kubectl)

k3s 기본 kubeconfig의 API Server 주소는 `127.0.0.1:6443`입니다.  
Windows/WSL 등 **외부 PC에서 접속**하려면 실제 VM IP로 변경해야 합니다.

### 3-1) kubeconfig 서버 주소 수정 (서버에서)

```sh
sed -i 's#https://127.0.0.1:6443#https://192.168.253.146:6443#g' ~/.kube/config
```

### 3-2) 수정 내용 확인

```sh
kubectl config view --minify
```

`server:` 항목이 아래처럼 바뀌면 정상:
```yaml
server: https://192.168.253.146:6443
```

### 3-3) 방화벽 6443 포트 허용 (UFW 활성화된 경우)

```sh
sudo ufw status
sudo ufw allow 6443/tcp
```

---

## 4) 원격 PC에서 kubectl 연결 (Windows/WSL)

### 4-1) 서버에서 kubeconfig 출력

```sh
cat ~/.kube/config
```

### 4-2) 로컬 PC에 kubeconfig 저장

출력 내용을 로컬 `~/.kube/config`에 붙여넣거나 scp로 복사:

```sh
# Windows PowerShell에서 실행
scp ubuntu@192.168.253.146:~/.kube/config $env:USERPROFILE\.kube\config
```

```sh
# WSL / Linux에서 실행
scp ubuntu@192.168.253.146:~/.kube/config ~/.kube/config
chmod 600 ~/.kube/config
```

### 4-3) 로컬에서 접속 확인

```sh
kubectl get nodes
kubectl cluster-info
```

정상 예시:
```text
Kubernetes control plane is running at https://192.168.253.146:6443
```

---

## 5) k3s 주요 파일 위치

| 목적 | 경로 |
|------|------|
| kubeconfig (root) | `/etc/rancher/k3s/k3s.yaml` |
| kubeconfig (ubuntu) | `~/.kube/config` |
| k3s 서비스 설정 | `/etc/systemd/system/k3s.service` |
| 노드 토큰 (worker 조인용) | `/var/lib/rancher/k3s/server/node-token` |

---

## 6) Worker 노드 추가 (선택)

Control Plane에서 토큰 확인:

```sh
sudo cat /var/lib/rancher/k3s/server/node-token
```

Worker 노드에서 실행 (토큰과 Control Plane IP 대입):

```sh
curl -sfL https://get.k3s.io | K3S_URL=https://192.168.253.146:6443 K3S_TOKEN=<토큰> sh -
```

조인 확인:

```sh
kubectl get nodes
```

---

## 7) API Server 동작 점검

```sh
# API Server 포트 리스닝 확인
sudo ss -lntp | grep ':6443' || echo "6443 not listening"

# API 버전 확인
kubectl version --short

# API 리소스 목록 확인
kubectl api-resources | head -20

# 클러스터 정보
kubectl cluster-info
```

---

## 빠른 체크리스트

- [ ] `ssh ubuntu@192.168.253.146` 접속 성공
- [ ] `sudo systemctl status k3s` → Active: running
- [ ] `kubectl get nodes` → Ready 상태
- [ ] `kubectl config view --minify` → `server: https://192.168.253.146:6443`
- [ ] 6443 포트 접근 가능 확인

---

## 참고 문서

- [setup-ssh.md](./setup-ssh.md)
- [setup-kubeconfig.md](./setup-kubeconfig.md)
- [setup-virtualbox.md](./setup-virtualbox.md)
- [cheatsheet-wsl-powershell-docker-k8s.md](./cheatsheet-wsl-powershell-docker-k8s.md)
