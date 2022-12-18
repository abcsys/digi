#!/bin/bash
source ./.env

# temporary: use cluster-ip address for apiserver
# TODO: expose apiserver using load-balancer
APISERVER_IP=$(kubectl -n kube-system get pod -l component=kube-apiserver -o=jsonpath="{.items[0].metadata.annotations.kubeadm\.kubernetes\.io/kube-apiserver\.advertise-address\.endpoint}")
printf -v APISERVER "https://%s" $APISERVER_IP


# Create a secret to hold a token for the default service account
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: default-token
  annotations:
    kubernetes.io/service-account.name: default
type: kubernetes.io/service-account-token
EOF

# Wait for the token controller to populate the secret with a token:
while ! kubectl describe secret default-token | grep -E '^token' >/dev/null; do
  echo "waiting for token..." >&2
  sleep 1
done

# Get the token value
TOKEN=$(kubectl get secret default-token -o jsonpath='{.data.token}' | base64 --decode)

# Format the curl request to register dspace
USER=$2
DSPACE=$3
CA_CERT=$(cat $4)
CLIENT_CERT=$(cat $5)
CLIENT_KEY=$(cat $6)
DATA=$( jq -n \
    --arg user "${USER}" \
    --arg dspace "${DSPACE}" \
    --arg ip "${APISERVER}" \
    --arg token "${TOKEN}" \
    --arg ca_cert "${CA_CERT}" \
    --arg cert "${CLIENT_CERT}" \
    --arg key "${CLIENT_KEY}" \
    '{user: $user, dspace: $dspace, ip: $ip, token: $token, ca_cert: $ca_cert, cert: $cert, key: $key}' \
)

ADDR=$1
URL_STR="%s/registerDspace/"
printf -v URL "$URL_STR" "$ADDR"

curl $URL \
    --request PUT \
    --header "Content-Type: application/json" \
    --data "$DATA"

