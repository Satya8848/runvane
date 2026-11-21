# StackPilot

A public problem-solving platform for DevOps engineers, DevSecOps, solution architects, programmers, Linux administrators, database administrators and cloud engineers.

| Feature | What it does |
| --- | --- |
| Problem playbooks | Day-to-day problems per role: symptoms, likely causes, diagnosis commands, fix, prevention |
| Search | One typo-tolerant search (Meilisearch) over playbooks, guides, questions, terms, interview items and public boards |
| Forum | Ask, answer, vote, accept, comment, report; every new question gets a labelled AI first draft |
| AI assistant | Chat grounded in platform content with sources; analysers for logs, errors, configs, SQL, Dockerfiles and pipelines. Secrets are masked before anything is sent |
| Architecture board | Diagram as code (Mermaid), templates, describe-to-diagram, AI review against the Well-Architected pillars, public/unlisted/private boards |
| Guides & interview prep | 28 setup guides, 100+ glossary terms, 130+ interview questions with quiz mode |

AI providers: Claude, Gemini, Groq and OpenAI through one gateway, with members' own keys, a daily quota per member and a monthly site budget.

## Run

```bash
cd deploy
cp env.example .env        # set passwords and keys
docker compose up -d mariadb redis meilisearch
docker compose --profile setup run --rm init      # create site, seed, index
docker compose up -d
```

Host nginx: `deploy/nginx-hub.conf` + `deploy/stackpilot-proxy.inc`. Admin: `/app` (Desk) → AI Settings for provider keys.

## Develop

`bench get-app`, `bench new-site … --install-app stackpilot`, `cd frontend && yarn install && yarn build`, `bench --site … run-tests --app stackpilot`.
