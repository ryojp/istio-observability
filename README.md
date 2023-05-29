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
docker build --push -t localhost:5000/fastapi_app fastapi_app/
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
curl localhost/chain
```

5. Open Jaeger dashboard:
```sh
istioctl dashboard jaeger
```

## Cleanup
```sh
kubectl delete ns demo
```


## Troubleshooting

### `curl localhost/chain` returns `404 Not Found` HTML from NGINX

In this case, you are likely to have `NGINX Ingress Controller` deployed on your system, and it served the `curl` request instead of the `Istio Ingress Gateway`.  
Please delete your ingress and run again.

For example, if you are using `microk8s`, you can run `microk8s disable ingress`

### `curl localhost` hangs

Make sure that you can connect to the upstream web app directly using port-forward:
```sh
# On one terminal window
kubectl -n demo port-forward app-a-deployment-b75df8b88-46gqc 8080:80 # Please change the pod name appropriately
# On another terminal window
curl localhost:8080
```

If this returns a response, the problem is likely to be on the Ingress Gateway of Istio.

For some environments including `microk8s` on Ubuntu (in my case, Xubuntu 22.04), `LoadBalancer` does not seem to work.
As the [official doc](https://istio.io/latest/docs/tasks/traffic-management/ingress/ingress-control/#using-node-ports-of-the-ingress-gateway-service) mentions, change the `spec.type` of `ingress-gateway` from `LoadBalancer` to `NodePort` to fix this.
```sh
kubectl -n istio-system edit svc istio-ingressgateway
```

Next, get the port number that maps to `80` by:
```sh
$ kubectl -n istio-system get svc istio-ingressgateway
NAME                   TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)                                                                      AGE
istio-ingressgateway   NodePort   10.152.183.198   <none>        15021:32569/TCP,80:30419/TCP,443:32250/TCP,31400:30769/TCP,15443:32302/TCP   66m
```

In this case, `localhost:30419` is what you want. Try `curl localhost:30419` to verify it.


### Istio does not seem to handle requests...
In case you get errors like `upstream connect error or disconnect/reset before headers. reset reason: connection termination` even though you are sure that the upstream service is up and running, restart the Istio:
```sh
kubectl -n istio-system rollout restart deploy
```

### Deleting a namespace hangs...

I found a solution on [StackOverflow](https://stackoverflow.com/a/53661717).

Replace the `NAMESPACE` below and run:
```sh
export NAMESPACE=your-rogue-namespace
export PROXYPORT=8011
kubectl proxy --port=$PROXYPORT &
kubectl get namespace $NAMESPACE -o json |jq '.spec = {"finalizers":[]}' >temp.json
curl -k -H "Content-Type: application/json" -X PUT --data-binary @temp.json 127.0.0.1:$PROXYPORT/api/v1/namespaces/$NAMESPACE/finalize
rm temp.json
kill $(ps ax | grep "proxy --port=$PROXYPORT" | grep -v grep | cut -f1 -d' ')
```
