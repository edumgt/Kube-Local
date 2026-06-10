#!/bin/bash

REGISTRY="localhost:5000"
BE_SRC="/home/ubuntu/kubernetes-lab/00-Docker-Images/02-kube-backend-helloworld-springboot/kube-helloworld"
FE_SRC="/home/ubuntu/kubernetes-lab/00-Docker-Images/03-kube-frontend-nginx/V1-Release"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

deploy_be() {
  echo "[BE] 변경 감지 → 빌드 시작"
  docker build -t "${REGISTRY}/kube-helloworld:1.0.0" "${BE_SRC}" && \
  docker push "${REGISTRY}/kube-helloworld:1.0.0" && \
  kubectl rollout restart deployment/my-backend-rest-app && \
  kubectl rollout status deployment/my-backend-rest-app
  echo "[BE] 배포 완료"
}

take_screenshot() {
  echo "[screenshot] FE 화면 캡처 시작..."
  cd "${SCRIPT_DIR}" && node screenshot.js
}

deploy_fe() {
  echo "[FE] 변경 감지 → 빌드 시작"
  docker build -t "${REGISTRY}/kube-frontend-nginx:1.0.0" "${FE_SRC}" && \
  docker push "${REGISTRY}/kube-frontend-nginx:1.0.0" && \
  kubectl rollout restart deployment/my-frontend-nginx-app && \
  kubectl rollout status deployment/my-frontend-nginx-app
  echo "[FE] 배포 완료"
  take_screenshot
}

echo "감시 시작..."
echo "  BE: ${BE_SRC}"
echo "  FE: ${FE_SRC}"

inotifywait -m -r -e close_write,create,delete \
  --exclude '(\.class$|target/|\.DS_Store)' \
  "${BE_SRC}/src" "${BE_SRC}/Dockerfile" \
  "${FE_SRC}" 2>/dev/null |
while read -r dir event file; do
  path="${dir}${file}"
  echo "[변경] ${path} (${event})"

  if [[ "${path}" == "${BE_SRC}"* ]]; then
    deploy_be
  elif [[ "${path}" == "${FE_SRC}"* ]]; then
    deploy_fe
  fi
done