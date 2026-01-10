# Kube-Local 문서 모음

이 저장소는 Windows 환경에서 **VirtualBox + Ubuntu + K3s**로 로컬 Kubernetes 실습 환경을 구성하고 운영하는 과정을 정리한 문서 모음입니다. WSL/PowerShell 네트워크 점검부터 멀티노드 K3s 설치, SSH 접속, Ingress/대시보드 구성, 대시보드 재접속, HPA 오토스케일 실습까지 단계별로 안내합니다.

## 문서 구성

- **WSL/PowerShell/Docker/Kubernetes 치트시트**: `0. wsl_po wershell_docker_k8s_cheatsheet.md`
- **VirtualBox 설치 안내**: `1. virtualbox.md`
- **VirtualBox Host-Only 네트워크 구성 가이드**: `1. virtualbox_hostonly_k8s_guide.md`
- **K3s 기본 설치 메모**: `2. k3s.md`
- **K3s 멀티노드 설치 가이드**: `2. k3s_multinode_hostonly_guide.md`
- **SSH 접속 메모**: `3. ssh.md`
- **SSH 접속/트러블슈팅 가이드**: `3. ssh_access_troubleshooting_guide.md`
- **Ingress/대시보드 구성 메모**: `4. dashboard.md`
- **Ingress + Metrics Server + Dashboard 가이드**: `4. k3s_ingress_metrics_dashboard_guide.md`
- **대시보드 재접속/포트포워딩 문제 해결**: `5. dashboard_reconnect_portforward_guide.md`
- **재부팅 후 대시보드 재접속 메모**: `5. re-connect.md`
- **HPA 오토스케일 실습**: `6. AutoScaleUp_Test.md`

## 이미지 자료

실습 과정에서 사용한 스크린샷이 루트에 `image*.png` 형식으로 포함되어 있습니다.

## 활용 방법

1. **VirtualBox 설치 및 Host-Only 네트워크 구성**부터 시작합니다.
2. **K3s 멀티노드 설치 가이드**를 따라 cp1/w1/w2 노드를 구성합니다.
3. **SSH 접속 가이드**로 운영 터미널을 준비합니다.
4. **Ingress/대시보드 가이드**와 **재접속 문서**로 운영 환경을 점검합니다.
5. **HPA 오토스케일 실습**으로 자동 확장 동작을 확인합니다.

필요한 문서만 발췌하여 참고해도 되며, 각 문서는 독립적으로 읽을 수 있도록 구성되어 있습니다.
