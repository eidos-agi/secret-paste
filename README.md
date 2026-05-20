# secret-paste

Tiny local CLI for handing secrets to an AI-assisted workflow without pasting
the secret into chat, shell history, logs, or command arguments.

`secret-paste` opens a local password-style GUI prompt, then either:

- runs a child command with the secret set as an environment variable, or
- writes the secret to a `0600` file for another command to read.

It never prints the secret.

This is designed for AI-assisted sessions where the assistant invokes the
command but the human needs a safe local paste box. Use `--terminal` only when
you explicitly want a shell prompt with echo disabled.

## Install

```bash
python3 -m pip install -e .
```

For local use without installing:

```bash
./secret-paste --help
```

## Use

Run a command with a prompted secret in its environment:

```bash
secret-paste run --env CLOUDFLARE_API_TOKEN -- \
  curl -sS -H 'Authorization: Bearer $CLOUDFLARE_API_TOKEN' \
  https://api.cloudflare.com/client/v4/user/tokens/verify
```

Use terminal input instead of the GUI prompt:

```bash
secret-paste run --terminal --env CLOUDFLARE_API_TOKEN -- \
  curl -sS -H 'Authorization: Bearer $CLOUDFLARE_API_TOKEN' \
  https://api.cloudflare.com/client/v4/user/tokens/verify
```

Write a secret to a temporary file:

```bash
secret-paste write --path /tmp/cloudflare-token
```

Write via terminal:

```bash
secret-paste write --terminal --path /tmp/cloudflare-token
```

The file is created with mode `0600`. Remove it when finished.

## Boundary

This tool is only a local paste bridge. It is not a vault, password manager, or
secret-rotation system. Prefer a real vault for durable storage.
