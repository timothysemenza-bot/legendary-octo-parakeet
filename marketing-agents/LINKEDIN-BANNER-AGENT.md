# LinkedIn Banner Agent

Generate clean LinkedIn banner variants with one command.

## Command

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-linkedin-banner.ps1 `
  -Title "Boss Key" `
  -Subtitle "Business Development Acceleration" `
  -OutputPath ".\boss-key-website\assets\logos\linkedin\boss-key-linkedin-banner-generated.svg"
```

## Inputs you can change

- `-Title`
- `-Subtitle`
- `-Accent` (hex, default `#C5162E`)
- `-BgStart` and `-BgEnd` (hex gradient)
- `-OutputPath`

## Optional

- Add `-Open` to open the generated file immediately.

## Notes

- Output is SVG at LinkedIn cover dimensions: `1584 x 396`.
- Open the SVG in Illustrator for final type tweaks if needed, then export JPG/PNG for upload.
