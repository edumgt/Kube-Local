#!/usr/bin/env bash
# Docker Hub 이미지 빌드 & 푸시 스크립트
# 사용법: DOCKER_USER=<도커허브계정> bash build-push.sh

set -e

DOCKER_USER="${DOCKER_USER:-kimdypm}"
REPO="fastapi-health"
TAG="1.0"
IMAGE="${DOCKER_USER}/${REPO}:${TAG}"

echo "=== Building ${IMAGE} ==="
docker build -t "${IMAGE}" .

echo "=== Pushing ${IMAGE} ==="
docker push "${IMAGE}"

echo ""
echo "완료! 매니페스트에서 image: 를 아래로 수정하세요:"
echo "  image: ${IMAGE}"
