# MVP Design Spec

## 1) Vision
Create a standalone 2D top-down action roguelite where each run is built from procedural room networks, itemized build mutation, and region-based traversal upgrades.

Design target:
- Fast, readable room combat
- High replayability via item/room permutations
- Exploration tension from traversal gating and map uncertainty

## 2) Player Fantasy
You are a lone exo-explorer descending through hostile alien sectors, salvaging ancient tech modules and adapting your suit mid-run.

## 3) Core Loop (per run)
1. Enter sector floor with incomplete map
2. Clear combat rooms to earn currency/resources
3. Choose pathing: safer route vs challenge route
4. Find upgrades (passive modules + active tech)
5. Unlock traversal options (Bomb Charge, Dash Shift, Grapple Line)
6. Defeat sector boss
7. Move deeper with escalating enemy complexity

Meta loop:
1. Return to hub
2. Spend persistent resources on unlock pools (new items, room variants, enemy variants)
3. Start new seeded run

## 4) MVP Scope (first playable)
Include:
- 1 playable character
- 2 sectors (Biome A + Biome B)
- 1 mini-boss type + 2 major bosses
- 20 normal room templates
- 6 combat enemy archetypes
- 30 passive items
- 6 active abilities
- 3 traversal modules
- Shop + challenge room + reward room
- Seeded run generation and basic save system

Exclude (post-MVP):
- Co-op
- Narrative cinematics
- Advanced NPC questlines
- Online services

## 5) Combat Model
- Twin-stick aiming (mouse/right stick) with auto-fire toggle option
- Base projectile can be modified by item effect stack
- Rooms lock on entry and unlock when threat budget is zero
- Enemy waves can spawn in phases based on room budget

Primary player stats:
- `hp_max`, `hp_current`
- `damage`
- `fire_rate`
- `projectile_speed`
- `range`
- `move_speed`
- `luck` (affects proc and reward odds)

## 6) Ability Gating (Metroid-style layer)
Traversal modules are found in designated reward pools and update reachable room graph nodes:
- `bomb_charge`: open cracked tiles / secret paths
- `dash_shift`: cross gap lanes and dodge through hazard bursts
- `grapple_line`: attach to anchor nodes to bypass pits or lasers

Rule:
- Runs are always completable without softlocks
- Generator validates at least one boss path with currently obtainable modules

## 7) Item System
Item categories:
- Passive module (always-on stat/effect)
- Active tech (cooldown-based)
- Suit relic (rare transformational effect)

Synergy approach:
- Effect components tagged (e.g., `projectile`, `on_hit`, `aura`, `summon`)
- Resolve in deterministic pipeline order:
1. Stat modifiers
2. Projectile mutators
3. On-hit events
4. Room/global auras

## 8) Run Generation
Each floor is a graph of typed rooms:
- `start`, `combat`, `elite`, `shop`, `challenge`, `reward`, `boss`, `secret`

Generation constraints:
- Boss distance from start >= configured minimum
- Shop appears once per floor (except special floor rules)
- At least one optional branch exists
- Special rooms weighted by floor depth

## 9) Enemy AI Archetypes (MVP)
- Charger: closes gap rapidly, low HP
- Turret: stationary projectile pattern
- Burrower: temporary invulnerability pop-up attacks
- Swarmer: group pressure unit
- Shield Drone: frontal protection behavior
- Caster: telegraphed area hazard placement

## 10) Economy and Rewards
Currencies:
- `credits` (run-local spend)
- `alloy` (persistent unlock currency)

Drop model:
- Room clear can drop credits/ammo/heal
- Elite rooms bias toward item drops
- Challenge rooms offer high-value, high-risk rewards

## 11) Difficulty Curve
Floor scaling:
- Enemy HP multiplier
- Spawn budget increase
- Hazard density increase

Adaptive guardrails:
- If player HP is critically low, slightly raise heal drop chance
- Avoid excessive unfair burst combinations in early floors

## 12) Technical Architecture
- Engine: Godot 4.x
- Language: GDScript for MVP
- Data-driven configs loaded from JSON at boot
- Core systems:
  - `RunManager`
  - `RoomGraphGenerator`
  - `CombatDirector`
  - `ItemSystem`
  - `AbilityGateSystem`
  - `SaveManager`
  - `ContentRegistry`

## 13) Milestones
Milestone 1: Vertical slice
- 1 sector, 8 rooms, 1 boss, 10 items

Milestone 2: MVP alpha
- Full two-sector loop with meta unlocks

Milestone 3: MVP beta
- Balance pass, bug fixing, controller support, save stability

## 14) Legal/IP Guardrails
- Do not use copyrighted names, sprites, sound effects, maps, or code from Nintendo or Isaac
- Keep mechanics at abstract pattern level
- Build all content assets from original sources

