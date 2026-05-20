# 느린 기동을 흉내내고 싶으면 SLOW_START=1, STARTUP_SLEEP=30 같은 env로 조절
SLOW_START = os.getenv("SLOW_START", "0") == "1"
STARTUP_SLEEP = int(os.getenv("STARTUP_SLEEP", "0"))

@app.on_event("startup")
def startup_hook():
    if SLOW_START and STARTUP_SLEEP > 0:
        time.sleep(STARTUP_SLEEP)

@app.get("/")
def root():
    return {"msg": "hello"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    return {"ready": True}
```

### `requirements.txt`
```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
```

### `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### AWS ECR 관련 설정
### ap-northeast-2 기준으로 보통 운영하는 건 Private ECR
![alt text](image-28.png)
![alt text](image-29.png)
![alt text](image-30.png)
![alt text](image-31.png)

### AWS CLI 설정
```
root@DESKTOP-D6A344Q:/home/Kube-Local# aws
Command 'aws' not found, but can be installed with:
snap install aws-cli  # version 1.44.24, or
apt  install awscli   # version 2.14.6-1
See 'snap info aws-cli' for additional versions.
```
---
```
apt-get update
apt-get install -y curl unzip less groff
```
---
```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install
```
---
```
aws --version
which aws
```
---
```
root@DESKTOP-D6A344Q:/home/Kube-Local# aws --version
which aws
aws-cli/2.33.12 Python/3.13.11 Linux/6.6.87.2-microsoft-standard-WSL2 exe/x86_64.ubuntu.24
/usr/local/bin/aws
```
---
```
aws configure
aws sts get-caller-identity
aws ecr describe-repositories --region ap-northeast-2
```
---
```
root@DESKTOP-D6A344Q:/home/Kube-Local# aws configure
aws sts get-caller-identity
aws ecr describe-repositories --region ap-northeast-2
```
---
```
AWS Access Key ID [None]: A.... 이하 생략
AWS Secret Access Key [None]: R... 이하 생략
Default region name [None]: ap-northeast-2
jsonult output format [None]:
{
    "UserId": "AIDARIBXLWVE6SSOENPWT",
    "Account": "086015456585",
    "Arn": "arn:aws:iam::086015456585:user/devuser"
}
{
    "repositories": [
        {
            "repositoryArn": "arn:aws:ecr:ap-northeast-2:본인 Account-ID:repository/본인 Repo",
            "registryId": "본인 Account-ID",
            "repositoryName": "본인 Repo",
            "repositoryUri": "086015456585.dkr.ecr.ap-northeast-2.amazonaws.com/edumgt/fastapi",
            "createdAt": "2026-01-31T14:59:36.706000+09:00",
            "imageTagMutability": "MUTABLE",
            "imageScanningConfiguration": {
                "scanOnPush": false
            },
            "encryptionConfiguration": {
                "encryptionType": "AES256"
            }
        }
    ]
}
```

### fastapi 의 python 모듈 ECR 로
```
REGION=ap-northeast-2
ACCOUNT_ID=<내_aws_account_id>
REPO=fastapi-health
TAG=1.0
IMAGE_LOCAL=$REPO:$TAG
IMAGE_ECR=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO:$TAG
```
---
```
root@DESKTOP-D6A344Q:/home/Kube-Local/fastapi# 
root@DESKTOP-D6A344Q:/home/Kube-Local/fastapi# REGION=ap-northeast-2
root@DESKTOP-D6A344Q:/home/Kube-Local/fastapi# ACCOUNT_ID=086015456585
root@DESKTOP-D6A344Q:/home/Kube-Local/fastapi# REPO=fastapi-health
root@DESKTOP-D6A344Q:/home/Kube-Local/fastapi# TAG=1.0
root@DESKTOP-D6A344Q:/home/Kube-Local/fastapi# IMAGE_LOCAL=$REPO:$TAG
root@DESKTOP-D6A344Q:/home/Kube-Local/fastapi# IMAGE_ECR=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO:$TAG
```
---
```
root@DESKTOP-D6A344Q:/home/Kube-Local/fastapi# ls -al
total 28
drwxr-xr-x 2 root root 4096 Jan 31 15:12 .
drwxr-xr-x 5 root root 4096 Jan 31 15:13 ..
-rw-r--r-- 1 root root  206 Jan 31 15:01 Dockerfile
-rw-r--r-- 1 root root  168 Jan 31 15:12 Readme.md
-rw-r--r-- 1 root root  564 Jan 31 15:00 main.py
-rw-r--r-- 1 root root  549 Jan 31 15:11 regecr.sh
-rw-r--r-- 1 root root   42 Jan 31 15:01 requirements.txt
root@DESKTOP-D6A344Q:/home/Kube-Local/fastapi# chmod +x regecr.sh
```

![alt text](image-32.png)
### ECR Pull 과정에서 repo 명 달라서 위에 2개 있음 - 상관없음
![alt text](image-33.png)
### 각자 AWS 계정에 따라 - 086015456585.dkr.ecr.ap-northeast-2.amazonaws.com/fastapi-health:1.0
### yaml 에서 image: 086015456585.dkr.ecr.ap-northeast-2.amazonaws.com/fastapi-health:1.0 부분 수정


> 이미지 빌드/푸시는 환경마다 다릅니다.  
> 실습에서는 사내 레지스트리나 개인 레지스트리에 위 이미지(`YOUR_REGISTRY/fastapi-health:latest`)를 올려 사용하세요.

---

## 2) (실패 재현) livenessProbe가 “틀린 포트”를 찌르는 Pod

아래 매니페스트는 FastAPI가 **8080**으로 뜨는데, livenessProbe가 **8000**을 체크해서 **항상 실패**합니다.

### `fastapi-liveness-bad.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: demo
---
apiVersion: v1
kind: Pod
metadata:
  name: fastapi-bad
  namespace: demo
  labels:
    app: fastapi-bad
spec:
  restartPolicy: Always
  containers:
    - name: app
      image: 086015456585.dkr.ecr.ap-northeast-2.amazonaws.com/fastapi-health:1.0
      ports:
        - containerPort: 8080
      # FastAPI는 8080인데 liveness는 8000을 찌름 => 실패 유도
      livenessProbe:
        httpGet:
          path: /healthz
          port: 8000
        initialDelaySeconds: 3
        periodSeconds: 5
        timeoutSeconds: 1
        failureThreshold: 2
```

적용:
```bash
kubectl apply -f fastapi-liveness-bad.yaml
```

---

## 3) 관찰: CrashLoopBackOff 확인

### 1) 상태 확인
```bash
kubectl -n demo get pod fastapi-bad -w
```
---
```
ubuntu@cp1:~$ kubectl apply -f fastapi-liveness-bad.yaml
namespace/demo unchanged
pod/fastapi-bad created
ubuntu@cp1:~$ kubectl -n demo get pod fastapi-bad -w
NAME          READY   STATUS         RESTARTS   AGE
fastapi-bad   0/1     ErrImagePull   0          14s
fastapi-bad   0/1     ImagePullBackOff   0          17s
```
---
```
ubuntu@cp1:~kubectl -n demo describe pod fastapi-bad | egrep -n "Failed|Back-off|pull|unauthorized|denied|not found|no basic auth|TLS|timeout"t"
24:    Liveness:       http-get http://:8000/healthz delay=3s timeout=1s period=5s #success=1 #failure=2
51:  Warning  Failed     36s (x4 over 2m8s)  kubelet            Failed to pull image "086015456585.dkr.ecr.ap-northeast-2.amazonaws.com/fastapi-health:1.0": failed to pull and unpack image "086015456585.dkr.ecr.ap-northeast-2.amazonaws.com/fastapi-health:1.0": failed to resolve reference "086015456585.dkr.ecr.ap-northeast-2.amazonaws.com/fastapi-health:1.0": pull access denied, repository does not exist or may require authorization: authorization failed: no basic auth credentials
52:  Warning  Failed     36s (x4 over 2m8s)  kubelet            Error: ErrImagePull
53:  Normal   BackOff    11s (x7 over 2m8s)  kubelet            Back-off pulling image "086015456585.dkr.ecr.ap-northeast-2.amazonaws.com/fastapi-health:1.0"
54:  Warning  Failed     11s (x7 over 2m8s)  kubelet            Error: ImagePullBackOff
```
---

### ECR 로그인 문제 부터 해결 필요 - CP 에 AWS CLI 설정
```
sudo apt-get update
sudo apt-get install -y curl unzip less groff
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
sudo ./aws/install
aws --version
```
---
```
ubuntu@cp1:~$ aws --version
aws-cli/2.33.12 Python/3.13.11 Linux/5.15.0-164-generic exe/x86_64.ubuntu.22
```
---
```
ubuntu@cp1:~$ aws configure
```
---
```
NS=demo
REGION=ap-northeast-2
ACCOUNT_ID=086015456585
SECRET_NAME=ecr-regcred

kubectl -n $NS create secret docker-registry $SECRET_NAME \
  --docker-server=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com \
  --docker-username=AWS \
  --docker-password="$(aws ecr get-login-password --region $REGION)"
```
---
```
secret/ecr-regcred created
```

### 토큰만 추출
```
aws ecr get-login-password --region ap-northeast-2
```
![alt text](image-34.png)

### Account 연동
```
kubectl -n demo patch serviceaccount default \
  -p '{"imagePullSecrets":[{"name":"ecr-regcred"}]}'
```
---
```
ubuntu@cp1:~$ kubectl -n demo patch serviceaccount default \
  -p '{"imagePullSecrets":[{"name":"ecr-regcred"}]}'
serviceaccount/default patched
```

### SA(serviceaccount) 확인
```
ubuntu@cp1:~$ kubectl -n demo get sa default -o yaml | egrep -n "imagePullSecrets|ecr-regcred"
2:imagePullSecrets:
3:- name: ecr-regcred
```
---
```
ubuntu@cp1:~$ kubectl -n demo get secret ecr-regcred
NAME          TYPE                             DATA   AGE
ecr-regcred   kubernetes.io/dockerconfigjson   1      6m28s
```


### pod 재생성
```
kubectl -n demo delete pod fastapi-bad
kubectl apply -f fastapi-liveness-bad.yaml
kubectl -n demo get pod fastapi-bad -w
```

### 정상이라면 ContainerCreating → Running으로 바뀝니다.
### (그 다음에야 liveness 실패로 CrashLoopBackOff 재현 단계로 넘어가요.)

```
ubuntu@cp1:~$ kubectl -n demo delete pod fastapi-bad
kubectl apply -f fastapi-liveness-bad.yaml
kubectl -n demo get pod fastapi-bad -w
pod "fastapi-bad" deleted from demo namespace
namespace/demo unchanged
pod/fastapi-bad created
```
---
```
NAME          READY   STATUS              RESTARTS   AGE
fastapi-bad   0/1     ContainerCreating   0          0s
fastapi-bad   1/1     Running             0          20s
fastapi-bad   1/1     Running             1 (1s ago)   32s
fastapi-bad   1/1     Running             2 (0s ago)   41s
fastapi-bad   1/1     Running             3 (0s ago)   51s
fastapi-bad   0/1     CrashLoopBackOff    3 (1s ago)   62s
fastapi-bad   1/1     Running             4 (29s ago)   90s
fastapi-bad   1/1     Running             5 (1s ago)    102s
fastapi-bad   0/1     CrashLoopBackOff    5 (1s ago)    112s
fastapi-bad   1/1     Running             6 (82s ago)   3m13s
fastapi-bad   0/1     CrashLoopBackOff    6 (0s ago)    3m26s
```


### 2) 이벤트에서 “Liveness probe failed” 확인 - 다른 창에서
```bash
kubectl -n demo describe pod fastapi-bad | egrep -n "Unhealthy|Liveness|probe|Back-off|Killing"
```
---
```
ubuntu@cp1:~$ kubectl -n demo describe pod fastapi-bad | egrep -n "Unhealthy|Liveness|probe|Back-off|Killing"
29:    Liveness:       http-get http://:8000/healthz delay=3s timeout=1s period=5s #success=1 #failure=2
60:  Normal   Killing    105s (x6 over 3m5s)   kubelet            Container app failed liveness probe, will be restarted
61:  Warning  Unhealthy  10s (x14 over 3m10s)  kubelet            Liveness probe failed: Get "http://10.42.2.23:8000/healthz": dial tcp 10.42.2.23:8000: connect: connection refused
62:  Warning  BackOff    9s (x11 over 2m34s)   kubelet            Back-off restarting failed container app in pod fastapi-bad_demo(d8e34a13-d9ee-421e-97f2-a5736fd99dfe)
```

### 3) 이전(직전) 컨테이너 로그 확인
```bash
kubectl -n demo logs fastapi-bad --previous
```
---
```
ubuntu@cp1:~$ kubectl -n demo logs fastapi-bad --previous
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
```

---

## 4) (해결 1) liveness 포트를 정상으로 수정

### `fastapi-liveness-good.yaml`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fastapi-good
  namespace: demo
  labels:
    app: fastapi-good
spec:
  restartPolicy: Always
  containers:
    - name: app
      image: YOUR_REGISTRY/fastapi-health:latest
      ports:
        - containerPort: 8080
      livenessProbe:
        httpGet:
          path: /healthz
          port: 8080
        initialDelaySeconds: 3
        periodSeconds: 10
        timeoutSeconds: 2
        failureThreshold: 3
      readinessProbe:
        httpGet:
          path: /ready
          port: 8080
        periodSeconds: 5
        timeoutSeconds: 2
        failureThreshold: 3
```

적용:
```bash
kubectl -n demo delete pod fastapi-bad
kubectl apply -f fastapi-liveness-good.yaml
kubectl -n demo get pod fastapi-good -w
```

---

## 5) (심화) 느린 기동 재현 + startupProbe로 보호하기

FastAPI가 30초 뒤에 뜨도록 설정하고, `startupProbe`로 기동 구간을 보호합니다.

### `fastapi-slow-startup.yaml`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fastapi-slow
  namespace: demo
spec:
  restartPolicy: Always
  containers:
    - name: app
      image: YOUR_REGISTRY/fastapi-health:latest
      env:
        - name: SLOW_START
          value: "1"
        - name: STARTUP_SLEEP
          value: "30"
      ports:
        - containerPort: 8080

      # ✅ startupProbe: 기동 중에는 여기만 체크 (liveness/readiness를 잠시 무력화)
      startupProbe:
        httpGet:
          path: /healthz
          port: 8080
        periodSeconds: 2
        failureThreshold: 20   # 2초*20=40초까지 기동 허용

      # ✅ liveness: 기동 완료 후 hung 여부만 보수적으로
      livenessProbe:
        httpGet:
          path: /healthz
          port: 8080
        periodSeconds: 10
        timeoutSeconds: 2
        failureThreshold: 3

      # ✅ readiness: 트래픽 수용 가능 여부
      readinessProbe:
        httpGet:
          path: /ready
          port: 8080
        periodSeconds: 5
        timeoutSeconds: 2
        failureThreshold: 3
```

적용:
```bash
kubectl apply -f fastapi-slow-startup.yaml
kubectl -n demo get pod fastapi-slow -w
kubectl -n demo describe pod fastapi-slow | egrep -n "Startup|Liveness|Readiness|Unhealthy|probe"
```

---

## 6) (옵션) Service 붙여서 내부 통신으로 확인

> 아래 Service는 `fastapi-good`의 라벨(`app: fastapi-good`)과 매칭됩니다.

### `fastapi-svc.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-svc
  namespace: demo
spec:
  selector:
    app: fastapi-good
  ports:
    - name: http
      port: 80
      targetPort: 8080
  type: ClusterIP
```

적용/테스트:
```bash
kubectl -n demo apply -f fastapi-svc.yaml
kubectl -n demo run curl --rm -it --image=curlimages/curl -- \
  curl -sS http://fastapi-svc/healthz
```

---

## 7) 체크리스트 요약

- **CrashLoopBackOff 재현**: livenessProbe가 실패(틀린 포트/경로/타임아웃) → kubelet kill/restart 반복
- **원인 확인**: `kubectl describe pod` 이벤트에서 `Liveness probe failed`, `Killing`, `Back-off`
- **해결**:
  - liveness가 찌르는 **포트/경로를 정확히**
  - 느린 기동이면 **startupProbe**로 보호
  - readiness는 트래픽 차단용으로 별도 설계


---

## 참고 문서
- [theory-liveness-probe.md](./theory-liveness-probe.md)
- [tips-kubectl-explain.md](./tips-kubectl-explain.md)
