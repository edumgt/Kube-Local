# SSH 빠른 접속 메모 (Ubuntu 서버 VM)

> 통합본: `3. ssh.md` + `3. ssh_access_troubleshooting_guide.md`

## 기존 문서 1

> 목표: Ubuntu 서버 VM(cp1 등)에 **SSH로 접속**해 Windows 터미널에서 복붙하며 운영합니다.

---

## 1) cp1에서 SSH 서버 설치/활성화

```sh
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo systemctl status ssh --no-pager -l
```

정상 예시:

```text
Active: active (running)
```

---

## 2) UFW가 켜져 있으면 22/tcp 허용 (선택)

```sh
sudo ufw status
```

`Status: active`라면:

```sh
sudo ufw allow 22/tcp
```

---

## 3) 22번 포트 리스닝 확인

```sh
sudo ss -lntp | grep ':22' || echo "22 not listening"
```

---

## 4) Windows에서 접속

PowerShell:

```powershell
ssh ubuntu@192.168.56.10
```

- Host-Only IP가 아직 확정 전이면 현재 VM IP(예: `192.168.56.101`)로 접속합니다.
- 첫 접속 시 fingerprint 확인은 `yes` 입력.

---

## 5) 자주 발생하는 문제 요약

### 5-1) `Connection refused`

대부분 **sshd가 실행되지 않은 상태**입니다. 섹션 1~3을 재확인하세요.

### 5-2) `no hostkeys available`

```sh
sudo ssh-keygen -A
sudo systemctl restart ssh
sudo systemctl status ssh --no-pager -l
```

---

## 6) Desktop VM인 경우 (Guest Additions)

GUI가 있는 VM이라면:

- VirtualBox → **Devices → Insert Guest Additions CD image…**
- 게스트에서 설치 후 재부팅

서버(Text) VM에서는 SSH가 가장 효율적입니다.

---

## 기존 문서 2

> 목표: Ubuntu 서버 VM(cp1 등)에 **SSH로 접속**해서 Windows 터미널에서 명령을 **복붙**하며 운영합니다.
> “GUI 없는 서버 VM”에서는 이 방식이 가장 빠르고 안정적입니다.

- 날짜: 2026-01-10

---

## 1) cp1(Ubuntu)에서 SSH 서버 설치/활성화

cp1에서:
```sh
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo systemctl status ssh --no-pager -l
```

정상 예시:
```text
Active: active (running)
```

---

## 2) (선택) UFW가 켜져 있으면 22/tcp 허용

cp1에서:
```sh
sudo ufw status
```

`Status: active`라면:
```sh
sudo ufw allow 22/tcp
```

---

## 3) cp1에서 22번 포트 리스닝 확인

```sh
sudo ss -lntp | grep ':22' || echo "22 not listening"
```

정상 예시(형태):
```text
LISTEN ... :22 ... users:(("sshd",pid=...,fd=...))
```
---
### 서버 재 설치 후 ssh 접속 중 오류

```sh
PS C:\Windows\system32> ssh ubuntu@192.168.56.10
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the ED25519 key sent by the remote host is
SHA256:eX2RzRgJQDVRWBaaWWxGexVLnMsyGlD/NmAZ+x8t6Vs.
Please contact your system administrator.
Add correct host key in C:\\Users\\TJ/.ssh/known_hosts to get rid of this message.
Offending ECDSA key in C:\\Users\\TJ/.ssh/known_hosts:3
Host key for 192.168.56.10 has changed and you have requested strict checking.
Host key verification failed.
```
---
```sh
PS C:\Windows\system32> ssh-keygen -R 192.168.56.10
