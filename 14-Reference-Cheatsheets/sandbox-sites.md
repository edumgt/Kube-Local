# Kubernetes(k8s) kubectl 명령어 연습용 Sandbox 사이트 (2026-03-11 점검)

k8s `kubectl` 실습용 브라우저 환경을 실제 접속 기준으로 점검하고, 대체/신규 사이트를 보완했습니다.

## 기존 사이트 점검 결과

| 사이트 | 상태 | 메모 |
|---|---|---|
| Killercoda Kubernetes Playground | 정상(접속 가능) | 브라우저 JS 활성화 필요 |
| Play with Kubernetes (PWK) | 종료 예정 공지 확인 | 2026-03-01부터 unavailable 공지 |
| PWK Classroom | 접속 가능 | 워크숍 안내형 페이지, PWK 종료 영향 가능 |
| KodeKloud Free Labs (K8s) | 정상(접속 가능) | `Pods/ReplicaSets/Deployments/Services/YAML` 랩 확인 |
| KodeKloud Public Playgrounds | 정상(접속 가능) | 멀티노드 Playground 버전 선택 가능 |
| iximiuz Labs K8s Playgrounds | 정상(접속 가능) | kubeadm/k3s/k0s 등 다양한 클러스터 playground 제공 |
| GitHub Codespaces | 정상(접속 가능) | 전용 k8s playground는 아니며, 직접 kind/k3d 구성 방식 |

## 신규 발굴 사이트 (보완)

### 1) AWS EKS Workshop
- EKS 실습 가이드 + 브라우저 IDE 기반 워크숍 흐름
- 이벤트 환경 또는 개인 AWS 계정에서 진행 가능
- 주의: 개인 계정 경로는 비용 발생 가능

바로가기:
- https://www.eksworkshop.com/docs/introduction/setup/
- https://www.eksworkshop.com/docs/introduction/setup/your-account/

### 2) Google Cloud Skills Boost - Kubernetes Labs
- Kubernetes 카테고리 랩을 브라우저 기반으로 제공
- 실습형 가이드가 많은 편
- 주의: 과정별로 무료/유료/크레딧 정책이 다름

바로가기:
- https://www.cloudskillsboost.google/catalog?category=Containers

### 3) K8sGPT Playground (Killercoda 기반)
- 단순 kubectl 실습을 넘어 장애 분석/진단 시나리오까지 확장 가능
- Killercoda에서 K8sGPT CLI 시나리오 제공

바로가기:
- https://docs.k8sgpt.ai/tutorials/playground/

## 2026 기준 추천 우선순위
1. KodeKloud (Free Labs + Public Playgrounds)
2. Killercoda Kubernetes Playground
3. iximiuz Labs Kubernetes Playgrounds
4. (심화) AWS EKS Workshop / K8sGPT Playground

## 업데이트된 주소 모음

```text
[활성/권장]
Killercoda Kubernetes Playground: https://killercoda.com/playgrounds/scenario/kubernetes
KodeKloud Free Labs (K8s):       https://kodekloud.com/free-labs/kubernetes
KodeKloud Public Playgrounds:    https://kodekloud.com/public-playgrounds
iximiuz Labs K8s Playgrounds:    https://labs.iximiuz.com/playgrounds?category=kubernetes&filter=all
GitHub Codespaces:               https://github.com/features/codespaces
AWS EKS Workshop:                https://www.eksworkshop.com/docs/introduction/setup/
Google Skills Boost (K8s):       https://www.cloudskillsboost.google/catalog?category=Containers
K8sGPT Playground:               https://docs.k8sgpt.ai/tutorials/playground/

[상태 변경/참고]
Play with Kubernetes (PWK):      https://labs.play-with-k8s.com/  (2026-03-01부터 unavailable 공지)
PWK Classroom:                   https://training.play-with-kubernetes.com/
```
## kubectl + Linux 혼합 명령어 치트시트 (현장 패턴 정리)

> **핵심 요약**
- `kubectl ...`로 시작하면 **Kubernetes API(클러스터 리소스)**를 조회/조작하는 흐름이 시작됩니다.

- `kubectl exec POD -- <cmd>`에서 `--` **뒤의 `<cmd>`는 Linux 명령이지만 “컨테이너(파드) 내부”**에서 실행됩니다.
- 위의 내용은 6.2 에서 연습함.

- `| grep/awk/sed/sort/head/tail`, `$()`, 변수(`POD=...`)가 보이면 **Linux 쉘이 kubectl 출력(텍스트)을 가공** 중입니다.

---

## 1) “대상(리소스)”로 먼저 구분하기

### A. Linux 명령어(호스트/로컬 OS 대상)
```
`ls`, `cd`, `grep`, `awk`, `sed`, `tail`, `journalctl`, `systemctl`, `ps`, `curl`, `ssh`
```

---
