#!/bin/bash
# ============================================================
# 웹 공격(과부하) 시나리오 - ReplicaSet + HPA Pod 증감 실습
# ============================================================
# 시나리오 흐름:
#   1. ReplicaSet + Service + HPA 배포 (초기 2개 Pod)
#   2. 부하 생성기 1개 → 평상시 트래픽 확인
#   3. 부하 생성기 10개로 증가 → 공격 시뮬레이션 → Pod 자동 증가 관찰
#   4. 부하 생성기 제거 → Pod 자동 감소 관찰
# ============================================================

MANIFEST_DIR="$(dirname "$0")/kube-manifests"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

pause() {
  echo ""
  echo -e "${YELLOW}▶ $1${NC}"
  read -rp "  [Enter 키로 계속]"
}

section() {
  echo ""
  echo -e "${BLUE}════════════════════════════════════════${NC}"
  echo -e "${BLUE}  $1${NC}"
  echo -e "${BLUE}════════════════════════════════════════${NC}"
}

# ── STEP 1: 배포 ──────────────────────────────────────────
section "STEP 1: ReplicaSet + Service 배포"
kubectl apply -f "$MANIFEST_DIR/02-replicaset-definition.yml"
kubectl apply -f "$MANIFEST_DIR/03-replicaset-nodeport-servie.yml"
echo -e "${GREEN}✓ ReplicaSet, Service 배포 완료${NC}"
echo ""
kubectl get rs myapp2-rs
echo ""

pause "STEP 2: HPA(HorizontalPodAutoscaler) 배포로 이동"

# ── STEP 2: HPA 배포 ──────────────────────────────────────
section "STEP 2: HPA 배포 (min=2, max=10, CPU 50% 기준)"
kubectl apply -f "$MANIFEST_DIR/04-hpa-definition.yml"
echo ""
echo -e "${GREEN}HPA 상태 확인 (TARGETS에 CPU 사용률 표시)${NC}"
sleep 5
kubectl get hpa myapp2-hpa
echo ""
echo -e "${YELLOW}현재 Pod 수: $(kubectl get rs myapp2-rs -o jsonpath='{.status.readyReplicas}')개${NC}"

pause "STEP 3: 부하 생성기 1개 배포 (평상시 트래픽)"

# ── STEP 3: 부하 생성기 배포 (약한 부하) ─────────────────
section "STEP 3: 부하 생성기 1개 - 평상시 트래픽"
kubectl apply -f "$MANIFEST_DIR/05-load-generator.yml"
echo ""
echo -e "${GREEN}✓ 부하 생성기 1개 시작${NC}"
echo "30초 대기 후 CPU 사용률 확인..."
sleep 30
echo ""
kubectl get hpa myapp2-hpa
echo ""
echo -e "${YELLOW}Pod 수: $(kubectl get rs myapp2-rs -o jsonpath='{.status.readyReplicas}')개 (부하 낮음 → 유지)${NC}"

pause "STEP 4: 부하 생성기 10개로 증가 → 웹 공격 시뮬레이션"

# ── STEP 4: 공격 시뮬레이션 (강한 부하) ──────────────────
section "STEP 4: 웹 공격 시뮬레이션 - 부하 생성기 10개"
kubectl scale deployment load-generator --replicas=10
echo ""
echo -e "${RED}⚡ 공격 시작! 부하 생성기 10개로 확장${NC}"
echo ""

echo "━━━ Pod 증가 추이 모니터링 (30초 간격) ━━━"
for i in 1 2 3 4 5 6; do
  sleep 30
  PODS=$(kubectl get rs myapp2-rs -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "?")
  CPU=$(kubectl get hpa myapp2-hpa -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization}' 2>/dev/null || echo "?")
  DESIRED=$(kubectl get hpa myapp2-hpa -o jsonpath='{.status.desiredReplicas}' 2>/dev/null || echo "?")
  echo "  [$(date '+%H:%M:%S')] Pod 실행: ${PODS}개 | CPU: ${CPU}% | HPA 목표: ${DESIRED}개"
done

echo ""
kubectl get hpa myapp2-hpa
echo ""
kubectl get pods -l app=myapp2

pause "STEP 5: 공격 중단 → Pod 자동 감소 관찰"

# ── STEP 5: 부하 중단 ────────────────────────────────────
section "STEP 5: 공격 중단 - 부하 생성기 제거"
kubectl delete -f "$MANIFEST_DIR/05-load-generator.yml"
echo ""
echo -e "${GREEN}✓ 부하 생성기 제거 완료${NC}"
echo ""

echo "━━━ Pod 감소 추이 모니터링 (30초 간격, HPA stabilization 60초) ━━━"
for i in 1 2 3 4 5 6; do
  sleep 30
  PODS=$(kubectl get rs myapp2-rs -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "?")
  CPU=$(kubectl get hpa myapp2-hpa -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization}' 2>/dev/null || echo "?")
  DESIRED=$(kubectl get hpa myapp2-hpa -o jsonpath='{.status.desiredReplicas}' 2>/dev/null || echo "?")
  echo "  [$(date '+%H:%M:%S')] Pod 실행: ${PODS}개 | CPU: ${CPU}% | HPA 목표: ${DESIRED}개"
done

echo ""
kubectl get hpa myapp2-hpa
echo ""
kubectl get pods -l app=myapp2

# ── 최종 정리 ─────────────────────────────────────────────
section "시나리오 완료"
echo -e "${GREEN}증감 시나리오 완료. 리소스 정리 명령어:${NC}"
echo ""
echo "  # 전체 삭제"
echo "  kubectl delete -f $MANIFEST_DIR/04-hpa-definition.yml"
echo "  kubectl delete -f $MANIFEST_DIR/02-replicaset-definition.yml"
echo "  kubectl delete -f $MANIFEST_DIR/03-replicaset-nodeport-servie.yml"
echo ""
echo "  # 실시간 Pod 모니터링 (별도 터미널)"
echo "  watch -n 2 'kubectl get pods -l app=myapp2 && echo && kubectl get hpa myapp2-hpa'"
