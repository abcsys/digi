# dSpace Admission Webhook

This is the admission webhook for reviewing dSpace API requests. It maintains states about the shadows and digi-graph and reviews each API request against it.

Based on [slok/kubewebhook](https://github.com/slok/kubewebhook/) 

### steps

#### Set up the validating webhook

- Deploy the validating webhook certificates: `kubectl apply -f ./cmd/deploy/webhook-certs.yaml`.
- Deploy the validating webhook: `kubectl apply -f ./cmd/deploy/webhook.yaml`.
- Register the validating webhook for the apiserver: `kubectl apply -f ./cmd/deploy/webhook-registration.yaml`.

TBD: rename this webhook to mount