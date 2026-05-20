# K3s 노드(w3) NotReady + INTERNAL-IP 오인(중복/아이덴티티 꼬임) 정리

## 1) 관찰된 증상

### (1) cp1에서 본 노드 상태
- `cp1`만 **Ready**
- `w1 / w2 / w3`는 **NotReady**

```
ubuntu@cp1:~$ kubectl get nodes -o wide 
NAME STATUS ROLES AGE VERSION INTERNAL-IP EXTERNAL-IP OS-IMAGE KERNEL-VERSION CONTAINER-RUNTIME 
cp1 Ready control-plane 4d4h v1.34.3+k3s1 192.168.56.10 <none> Ubuntu 22.04.5 LTS 5.15.0-164-generic containerd://2.1.5-k3s1 
w1 NotReady <none> 4d4h v1.34.3+k3s1 192.168.56.11 <none> Ubuntu 22.04.5 LTS 5.15.0-164-generic containerd://2.1.5-k3s1 
w2 NotReady <none> 4d4h v1.34.3+k3s1 192.168.56.12 <none> Ubuntu 22.04.5 LTS 5.15.0-164-generic containerd://2.1.5-k3s1 
w3 NotReady <none> 33m v1.34.3+k3s1 192.168.56.11 <none> Ubuntu 22.04.5 LTS 5.15.0-164-generic containerd://2.1.5-k3s1
```

- 위에서 w1 NotReady <none> 4d4h v1.34.3+k3s1 192.168.56.11 ... 과 w3 NotReady <none> 33m v1.34.3+k3s1 192.168.56.11 동일 
- `kubectl get nodes -o wide`에서 **w3의 INTERNAL-IP가 `192.168.56.11`로 표시**됨  
  → 이 값은 `w1`의 IP와 동일하게 보임 (충돌/오인 가능)

### (2) w3에서 본 실제 네트워크 상태
- `ip -br a` 결과: `enp0s8`가 **`192.168.56.13/24`로 정상**
- `/etc/netplan/*.yaml`도 `192.168.56.13/24`로 설정되어 있음

✅ 결론적으로, **w3 자체 IP는 정상인데 클러스터가 w3를 `192.168.56.11`(w1)로 “착각”**하는 상태로 보임.

---

## 2) 가장 유력한 원인(거의 확정)

### “노드 아이덴티티(식별 정보) 복제/재사용” 또는 “노드 등록 정보 꼬임”
VM을 클론했거나 네트워크/디스크를 복제한 환경에서 아래가 **w1과 동일하게 복제**되면 자주 발생합니다.

- `/etc/hostname` (hostname)
- `/etc/machine-id` (machine-id)
```
cd /etc
ls -al

-r--r--r--  1 root root      33 Jan  1 06:15 machine-id

ubuntu@cp1:/etc$ cat ./machine-id
912972408d93480fbc4263ea5c041eab
```

- k3s agent가 이전 노드의 인증서/상태를 들고 재조인

이 경우, **서버(cp1)가 w3를 새 노드로 인식하지 못하고 기존 노드(w1)의 정체성을 덮어쓰거나 공유**하게 되어,
`kubectl get nodes`에 **IP가 엉뚱하게 표시 + NotReady**가 지속될 수 있습니다.

---

## 3) 원인 확정용 빠른 체크(10초)

w3에서 아래를 실행해 **w1과 동일한지 비교**합니다.

```bash
hostname
cat /etc/hostname
cat /etc/machine-id
cat /var/lib/dbus/machine-id 2>/dev/null || true
```

- hostname이 `w1`로 나오거나
- machine-id가 w1과 동일하면  
→ **100% 복제/아이덴티티 문제**입니다.

---

## 4) 해결(가장 확실): w3를 “깨끗하게 제거 후 재조인(join)”

> 목표: **w3의 hostname + machine-id + k3s agent 상태를 모두 새로** 만들어  
> cp1이 w3를 진짜 “새 노드”로 정상 등록하게 하기

### Step A) cp1에서 w3 노드 삭제
```bash
kubectl delete node w3
```

> (선택) w3가 삭제가 안 되거나 노드 레코드가 꼬였으면, 상황에 따라 w1도 정리 대상이 될 수 있음.

---

### Step B) w3에서 k3s-agent 완전 제거/초기화
```bash
sudo /usr/local/bin/k3s-agent-uninstall.sh
sudo rm -rf /etc/rancher /var/lib/rancher
```

---

### Step C) w3 hostname을 유니크하게 설정
```bash
sudo hostnamectl set-hostname w3
```

---

### Step D) machine-id 재생성(클론 VM에서 핵심)
```bash
sudo rm -f /etc/machine-id /var/lib/dbus/machine-id
sudo systemd-machine-id-setup
sudo reboot
```

---

### Step E) 재부팅 후 w3 재조인(join)

#### 1) cp1에서 토큰 확인
```bash
sudo cat /var/lib/rancher/k3s/server/node-token
```

#### 2) w3에서 agent 설치/실행
(서버 URL은 cp1: `192.168.56.10:6443` 기준)

```bash
curl -sfL https://get.k3s.io |   K3S_URL=https://192.168.56.10:6443   K3S_TOKEN='<위 토큰>'   sh -

sudo systemctl enable --now k3s-agent
```

---

## 5) 정상 복구 확인

cp1에서:

```bash
kubectl get nodes -o wide
```

정상 기준:
- `w3`가 **Ready**
- `w3`의 INTERNAL-IP가 **`192.168.56.13`으로 정확히 표시**

---

## 6) 추가 점검(노드 NotReady / Pod Pending 원인 확인)

### (1) 워커 노드에서 agent 상태/로그 확인
각 워커(w1/w2/w3)에서:

```bash
sudo systemctl status k3s-agent
sudo journalctl -u k3s-agent -n 200 --no-pager
```

### (2) Pod가 Pending/스케줄 실패 확인
cp1에서:

```bash
kubectl get pods -A -o wide | egrep "Pending|Terminating|CrashLoop|demo-hpa|kube-system" -n
kubectl -n demo-hpa get events --sort-by=.lastTimestamp | tail -n 50
```

---

## 7) 핵심 요약(한 줄 결론)

w3의 네트워크/IP 자체 문제라기보다,  
**클러스터가 w3를 w1로 오인하는 “노드 아이덴티티( hostname/machine-id/k3s 상태 ) 꼬임”**이 핵심이며,  
**w3를 완전 초기화 → hostname/machine-id 재생성 → k3s-agent 재조인**이 가장 확실한 해결책입니다.



---
---
