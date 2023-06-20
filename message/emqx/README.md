# EMQX Digi Space
## Running
In order to run the EMQX digi space, use `digi space start emqx`.

## Authentication
By default, this EMQX digi will allow all connections without username/password authentication. If you would like to require username/password authentication in order to connect to the broker, you can follow these steps:

### Set EMQX Web Dashboard Admin Account
In your digi home directory (normally `~/.digi`), you should find a `secrets` subdirectory. Create file `emqx.yaml` with the following contents:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ .Values.name }}
type: Opaque
stringData:
  username: "username"
  password: "password"
```

Replace `username` and `password` with your desired username and password.

**NOTE**: all passwords must be at least 8 characters in length.

### Start EMQX Digi Space
Execute `digi space start emqx` to start the space with the new credentials.

### Log Into Web Dashboard
The EMQX web dashboard is exposed on port 30004 on the local network as a NodePort. Simply connect to `http://localhost:30004` using a web browser and log in using your new account.

### Delete other accounts
If you have run the EMQX space before with a different configuration, your old account may still be listed as a user. You can manually delete the accounts once you've logged into the dashboard.

### Enable Authentciation
- Click "Authentication" on the sidebar
- Click "Create +" at the top right
- Click "Password-Based", and click "Next"
- Click "Built-in Database", and click "Next"
- Click "Create"
- Click "Users"
- Add a user with a custom username and password

Now, all MQTT connections will require one of the listed usernames/passwords to match in order to authenticate the connection!
