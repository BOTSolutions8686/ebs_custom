# BOT HR PWA — How It Survives HRMS Updates

## Short answer

| Question | Answer |
|----------|--------|
| If we only edit `hrms`, do updates delete our work? | **Yes** — `bench update` replaces `apps/hrms` |
| Can everything live in `ebs_custom`? | **Yes** — in folder `ebs_custom/hrms_overlay/` |
| Does it apply automatically? | **Yes** — on `install-app` and every `migrate` |
| Do we edit `hrms` on the server by hand? | **No** — only install/update `ebs_custom` |

---

## How it works

```
ebs_custom (your app — safe, in git)
├── hrms_overlay/          ← all PWA + BOT HR files stored HERE
│   ├── frontend/...
│   └── hrms/public/manifest/...
└── patches/apply_hrms_pwa_overlay.py

        │  bench install-app ebs_custom
        │  bench migrate
        ▼

apps/hrms (upstream — gets overwritten on update)
        ← overlay copies files in automatically
        ← yarn build (auto if yarn is on server)
```

**When HRMS updates:**
1. `bench update` replaces files in `apps/hrms`
2. `bench migrate` runs `ebs_custom` → copies everything back from `hrms_overlay/`
3. PWA is rebuilt automatically (if `yarn` is on server)

---

## Server commands

```bash
cd ~/frappe-ebsuat/apps/ebs_custom
git pull

cd ~/frappe-ebsuat
bench --site ebsuat.metadaftr.com migrate
bench restart
```

If you see a yellow warning, run:

```bash
cd apps/hrms/frontend && yarn install && yarn build
cd ~/frappe-ebsuat && bench build --app hrms && bench restart
```

---

## Files you edit in future

Only edit files under:

```text
ebs_custom/hrms_overlay/
```

Then push to git → pull on server → `bench migrate` → done.
