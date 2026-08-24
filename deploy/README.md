# StringSence Docker Deployment

This stack runs one FastAPI worker, PostgreSQL, a one-shot Alembic migration,
and an optional remotely-managed Cloudflare Tunnel connector. PostgreSQL has no
host port and `cloudflared` can reach only the backend network.

## 1. Create deployment secrets

```bash
cp deploy/.env.production.example deploy/.env.production
openssl rand -hex 24  # POSTGRES_PASSWORD
openssl rand -hex 32  # JWT_SECRET_KEY
```

Replace every `replace-*` value. Keep `deploy/.env.production` untracked.
For the first start only, set `SEED_ADMIN_ENABLED=true` and provide a strong
admin identity. After the account exists, set it back to `false`.

## 2. Build and start without Cloudflare

Build from the curated context. This avoids sending `.env`, local uploads,
backups, virtual environments, generated output, or macOS AppleDouble files to
Docker:

```bash
./deploy/build-backend-image.sh
docker compose --env-file deploy/.env.production \
  -f compose.production.yaml up -d postgres migrate backend
docker compose --env-file deploy/.env.production \
  -f compose.production.yaml ps
docker compose --env-file deploy/.env.production \
  -f compose.production.yaml exec backend \
  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:3001/health').read().decode())"
```

The production backend intentionally publishes no host port. Use the internal
health command above until the tunnel is connected.

For a local browser acceptance run only, add the loopback-only override:

```bash
docker compose --env-file deploy/.env.production \
  -f compose.production.yaml -f compose.acceptance.yaml up -d postgres migrate backend
```

## 3. Connect Cloudflare Tunnel

Create a remotely-managed tunnel in the Cloudflare dashboard. Add a public
hostname such as `api.example.com` and set its service URL to:

```text
http://backend:3001
```

Copy the tunnel token into `CLOUDFLARE_TUNNEL_TOKEN`, ensure the same hostname is
in `TRUSTED_HOSTS`, then start the connector:

```bash
docker compose --env-file deploy/.env.production \
  -f compose.production.yaml --profile tunnel up -d cloudflared
```

Do not publish PostgreSQL or backend ports. Cloudflare Tunnel is outbound-only;
the host firewall only needs outbound TCP/UDP port 7844 for the connector.
Do not put Cloudflare Access login in front of the mobile API unless the mobile
client is changed to supply Access credentials.

## 4. Operate safely

```bash
docker compose --env-file deploy/.env.production \
  -f compose.production.yaml logs --tail=200 backend cloudflared
docker compose --env-file deploy/.env.production \
  -f compose.production.yaml exec -T postgres \
  pg_dump -U stringsense_app -d stringsense -Fc > stringsense.dump
```

Store database dumps outside the repository. Back up the uploads volume with
the database because payment proofs and catalog images are file-backed.

Updates should rebuild the image, run the one-shot migration, verify health,
and only then replace the backend container. Keep one backend worker until the
feedback follow-up job has database-level uniqueness or is moved to a scheduler.
