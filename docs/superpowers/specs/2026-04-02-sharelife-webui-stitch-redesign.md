# Sharelife WebUI Stitch Redesign (April 2026)

## Scope

Redesign all public WebUI pages with Stitch guidance and map the resulting visual system back to the production HTML/CSS without breaking existing runtime IDs and API bindings:

- `index.html` (unified console)
- `member.html` (member workspace)
- `admin.html` (admin workspace)
- `market.html` (standalone market)

## Stitch Outputs

Project:
- `projects/11867940733077632109`

Screens:
- Unified console landing: `051780c3ef3745e2983fe44dfeda5283`
- Member console: `5fca889fbf0446a68dc9692935feae65`
- Admin console: `520fdcd07eb84d76a22736bb6a317f7d`
- Market hub: `eaa4b9a8fa064255a5287e5c62fd8461`

Design system:
- `assets/dd11b6a1063c4249932d00c1c7724360` (Emerald Nocturne)

## Model Selection Note

Requested explicit model:
- `modelId=gemini_3_1_pro`

Observed behavior:
- Stitch MCP currently returns `Request contains an invalid argument.` when `modelId` is provided (including `gemini_3_1_pro` and alternative spellings).
- Generation succeeds when `modelId` is omitted; execution path reports `PRO_AGENT`.

Operational fallback:
- Use successful default Stitch generation outputs as design source.
- Keep request/response evidence in implementation notes.

## Applied Mapping (Production WebUI)

Implemented in `sharelife/webui/`:

1. Unified launch surface for role entry (`index.html`):
   - Added role-first cards for Member/Admin/Market.
   - Added trust chips and concise action hierarchy.
2. Hero trust badges across all pages:
   - `Sandbox trial`
   - `Rollback safe`
   - `Audit trace`
   - `Signed verified`
   - `Risk labeled`
3. Design language pass in `style.css`:
   - cinematic dark layering
   - larger breathing room
   - stronger card hierarchy and interaction lift
4. Full i18n wiring for new labels:
   - `en-US`, `zh-CN`, `ja-JP`

## Constraints Preserved

- Existing DOM IDs used by `app.js` and E2E tests were not removed.
- Existing endpoint wiring and command workflows were preserved.
- Advanced controls remain hidden behind developer mode in member/admin paths.
