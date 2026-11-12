# Frontline Python skeleton

Fill in `NotImplementedError` / `# TODO` stubs. Design docs:

- `docs/design/commander_captains_mode.md`
- `docs/design/frontline_feasibility.md`

## Layout

| Path | Role |
|------|------|
| `wars_game/gamerules/frontline.py` | `Frontline` + `FrontlineInfo` (registered in `gamerules/__init__.py`) |
| `wars_game/frontline/roles.py` | Commander / captain / shared owner |
| `wars_game/frontline/faction_points.py` | Personal Lambda / Overwatch FP |
| `wars_game/frontline/milestones.py` | 5 kills / 100 req / capture → 1 FP |
| `wars_game/frontline/respawn.py` | HQ FIFO starter queue |
| `wars_game/frontline/camera.py` | FPS vs locked RTS |
| `wars_game/frontline/body_switch.py` | Morph cpt / replace regulars |
| `wars_game/frontline/buildings.py` | Operate / bunker / HQ popup |
| `wars_game/units/cpt_starters.py` | Placeholder until real `unit_cpt_*` infos |
| `wars_game/resources.py` | `lambda` / `overwatch` ResourceInfo stubs |

## Suggested fill order

1. Roles + shared `ownernumber` in `StartGame`
2. Spawn + `SetControlledUnit` starters
3. Personal FP + kill milestone
4. Respawn queue
5. Camera lock
6. Body switch / operate buildings
