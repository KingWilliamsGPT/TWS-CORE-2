# dotenv-vault-python-example
A simple Python project **example** that securely loads secrets using dotenv-vault
Ensuring secure production grade environment variable management


### Setup
```bash
$ python -m venv env
$ source env/bin/activate # Or env/Scripts/activate for Windows
$ make install # Or pip install -r requirements.txt

# should install successfully installed cffi-1.17.1 cryptography-45.0.5 pycparser-2.22 python-dotenv-1.1.1 python-dotenv-vault-0.7.0
```

### Optional
```
$ cp .env.example .env # for linux/powershell/max Or copy .env.example .env (CMD)
```

Put someting in the `.env` file.

```ini
SUPER_SECRET="I secretely love K-Pop music"
```


# Create an account with Dotenv Vault 

- Go to https://vault.dotenv.org/
- Create a project
- Add secret keys like as seen in the image below
![setenvonline](.git-assets/setenvonline.png)

- Copy the Vault ID something like `(vlt_85...c0)` and use it like this


```bash
$ npx dotenv-vault@latest new vlt_85...cc0  # make env-new

5d...cc0
Need to install the following packages:
dotenv-vault@1.27.0
Ok to proceed? (y) y

npm warn deprecated lodash.template@4.5.0: This package is deprecated. Use https://socket.dev/npm/package/eta instead.
npm warn deprecated @oclif/screen@3.0.8: Package no longer supported. Contact Support at https://www.npmjs.com/support for more info.
local:    Adding .env.vault (DOTENV_VAULT)... done
local:    Added to .env.vault (DOTENV_VAULT=vlt_851f0...)

Next run npx dotenv-vault@latest push

```

- Now you can login with this command or just run `make env-pull` OR `make env-push` which would automaticaly ask you to login

```bash
$ npx dotenv-vault@latest login  # make env-login
```

- Do this whenever you wanna see your project on your browser at [**vault.dotenv.org**](https://vault.dotenv.org)

```bash
$ npx dotenv-vault@latest open  # make env-open
```


# Team Secret Sharing (Pull-Only by Default)

Only project owners/admins can push secrets.

Teammates can **ONLY PULL** once they:
- Get access via your Dotenv Vault dashboard.
- Run:
```bash
$ npx dotenv-vault@latest login #make env-login
$ npx dotenv-vault@latest new <VAULT_ID> #make env-new
$ npx dotenv-vault@latest pull  #make env-pull
```
