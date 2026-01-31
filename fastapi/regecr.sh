#!/usr/bin/env bash
set -euo pipefail

REGION=ap-northeast-2
ACCOUNT_ID=086015456585
REPO=fastapi-health
TAG=1.0

IMAGE_LOCAL=$REPO:$TAG
IMAGE_ECR=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO:$TAG

aws ecr create-repository --region $REGION --repository-name $REPO >/dev/null 2>&1 || true

aws ecr get-login-password --region $REGION \
| docker login --username AWS --password-stdin \
  $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

docker build -t $IMAGE_LOCAL .
docker tag $IMAGE_LOCAL $IMAGE_ECR
docker push $IMAGE_ECR

echo "Pushed: $IMAGE_ECR"
