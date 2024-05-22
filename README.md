# ProjectSet API

## Env variables


```
export JWT_SECRET_KEY=
export X_API_KEY=
export JWT_EXP=31536000
export JWT_HEADER="JWT"
export ADMIN_DISABLE="n"
export AUTH_TYPES="ldap,oauth"
export ADMIN_PASSWD=
export PWORKERS=1
export PWORKERS_SLEEP=15
export APP_CONF=./app.yaml
export OPENAI_API_KEY=
export OPENAI_MODEL=
export PROMT=

```

### App config 

See app.yaml.example

### Deployment 

```

kubectl create ns projectset-app-system

kubectl create secret generic app-conf --from-file=app.yaml=app.yaml --namespace projectset-app-system

kubectl apply -f ./deploy/manifests.yaml
  
```

proxy app

```
kubectl port-forward service/projectset-app-service -n projectset-app-system 8082:8082


open http://localhost:8082

```


## Development

### Run locally

```
LOGLEVEL=DEBUG PYENV=/opt/homebrew/bin/ make run

```

### Run tests

```
LOGLEVEL=DEBUG PYENV=/opt/homebrew/bin/ make tests
```

### Run proxy ldap

```
sudo kubectl port-forward service/openldap -n ldap 389:389
```


