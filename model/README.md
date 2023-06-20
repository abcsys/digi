# Model
Code generators and scripts to build, share, and deploy digis.

## Adding secrets
If you would like to run your digi with secrets, you can add secret files to the `secrets` subdirectory of your digi home (normally `~/.digi/secrets`).

For good practice, try to title the file the same name as your secret name, i.e. `my-digi-auth.yaml`.

Populate the secret file with the following contents:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-digi-auth
type: Opaque
stringData:
  username: "username"
  password: "password"
```

In the above example, change `my-digi-auth` to your secret's name.

For more information about Kubernetes secret files, view the documentation [here](https://kubernetes.io/docs/tasks/configmap-secret/managing-secret-using-config-file/).

In order to use your secret, edit your `actor.yaml` file.

- One of the ways you can utilize your secret is by adding it as an environment variable to your digi. Under your `env` group, you can specify that an enviornment variable should be pulled from a secret as such:

```yaml
env:
- name: MY_DIGI_AUTH_USERNAME
  valueFrom:
    secretKeyRef:
      name: my-digi-auth
      key: username
      optional: false
- name: MY_DIGI_AUTH_PASSWORD
  valueFrom:
    secretKeyRef:
      name: my-digi-auth
      key: password
      optional: true
```

Finally, run your digi using the `-s` flag, which will specify the secret file to be used. For example, `digi run my-digi mydigi1 -s ~/.digi/my-digi-auth.yaml`.
