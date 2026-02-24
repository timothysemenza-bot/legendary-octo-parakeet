# Creative Agents for JWBLNG Mockup

## 1) Open Adobe apps and folders

```powershell
cd C:\Users\timot\Documents\Proposal-Microsite\jwblng-mvp
powershell -ExecutionPolicy Bypass -File .\agents\open-creative-cloud-apps.ps1 -OpenAll
```

Or open selected apps:

```powershell
powershell -ExecutionPolicy Bypass -File .\agents\open-creative-cloud-apps.ps1 -OpenIllustrator -OpenAfterEffects -OpenFolders
```

## 2) Sync exported assets (iteration-first)

Run one-shot sync (default):

```powershell
powershell -ExecutionPolicy Bypass -File .\agents\creative-export-sync-agent.ps1
```

Default watch folder:

`%USERPROFILE%\Downloads\jwblng-exports`

Export assets from Adobe to that folder with the exact filenames used in:

- `assets/stock/README.md`
- `assets/motion/README.md`

Continuous background watch (optional):

```powershell
powershell -ExecutionPolicy Bypass -File .\agents\creative-export-sync-agent.ps1 -Watch
```

## 3) Supported injected assets

- Hero video loops (`hero-loop.mp4`, `portal-loop.mp4`)
- Lottie JSON animations (`learning-pulse.json`, `network-flow.json`, `portal-engagement.json`)
- Branded SVG icon sprite (`assets/icons.svg`)
