apiVersion: admissionregistration.k8s.io/v1beta1
kind: ValidatingWebhookConfiguration
metadata:
  name: dspace-webhook
  labels:
    app: dspace-webhook
    kind: validating
webhooks:
  - name: dspace-webhook.digi.dev
    clientConfig:
      service:
        name: dspace-webhook
        namespace: default
        path: "/validating"
      caBundle: CA_BUNDLE
    rules:
      - operations: ["*"]
        # add api groups and versions below
        apiGroups: ["kome.io"]
        apiVersions: ["*"]
        resources: ["*"]
