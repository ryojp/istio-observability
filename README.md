# Istio Observability

This repo is based on https://github.com/blueswen/fastapi-jaeger, which integrates Jaeger through OpenTelemetry into FastAPI using Docker Compose.

## Prerequisites

1. Deploy `Istio` by installing `istioctl` and running:
```sh
istioctl install --set profile=demo -y
```

2. Deploy Jaeger etc. to the namespace `istio-system` by running:
```sh
kubectl apply -f k8s/addons
```

3. Deploy local registry by:
```sh
docker run -d -p 5000:5000 --restart always --name registry registry:2
```

## Setup

1. Build and push `fastapi_app` image to `localhost:5000`:
```sh
docker build -t localhost:5000/fastapi_app fastapi_app/

docker push localhost:5000/fastapi_app
```

2. Create a namespace `demo` with `istio-injection` label:
```sh
kubectl apply -f k8s/istio-namespace.yml
```

3. Deploy FastAPI apps into the namespace `demo`:
```sh
kubectl apply -f k8s
```

4. Issue requests to the FastAPI app:
```sh
curl http://localhost/chain
```

5. Open Jaeger dashboard:
```sh
istioctl dashboard jaeger
```

## Current Limitations

Somehow Jaeger UI does not correlate requests that (should have) the same correlation ID.
Now, they are displayed as individual requests, such as those between `app-a` and `app-b`, `app-a` and `app-c`, etc.
