#!/usr/bin/env bash
# 로컬 레지스트리 이미지 빌드 & 푸시 스크립트
# 사용법: bash build-push.sh

set -e

REGISTRY="192.168.253.148:5000"
REPO="fastapi-health"
TAG="1.0"
IMAGE="${REGISTRY}/${REPO}:${TAG}"

echo "=== Building ${IMAGE} ==="
docker build -t "${IMAGE}" .

echo "=== Pushing ${IMAGE} ==="
docker push "${IMAGE}"

echo ""
echo "완료! 매니페스트에서 image: 를 아래로 수정하세요:"
echo "  image: ${IMAGE}"
