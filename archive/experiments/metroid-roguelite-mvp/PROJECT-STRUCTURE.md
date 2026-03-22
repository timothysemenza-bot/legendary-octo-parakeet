# Recommended Godot 4 Project Structure

```text
project-nebula/
  project.godot
  icon.svg
  README.md

  data/
    rooms.json
    items.json
    enemies.json
    biomes.json
    progression.json
    balance.json

  scenes/
    core/
      game.tscn
      run_manager.tscn
      floor_manager.tscn
    player/
      player.tscn
      projectile.tscn
    rooms/
      room_base.tscn
      room_start.tscn
      room_combat.tscn
      room_shop.tscn
      room_boss.tscn
    enemies/
      enemy_base.tscn
      charger.tscn
      turret.tscn
      burrower.tscn
    ui/
      hud.tscn
      map_overlay.tscn
      inventory_panel.tscn
      pause_menu.tscn

  scripts/
    core/
      run_manager.gd
      room_graph_generator.gd
      combat_director.gd
      save_manager.gd
      content_registry.gd
    systems/
      item_system.gd
      ability_gate_system.gd
      economy_system.gd
      difficulty_system.gd
    player/
      player_controller.gd
      weapon_controller.gd
    enemies/
      enemy_base.gd
      ai_charger.gd
      ai_turret.gd
      ai_burrower.gd
    ui/
      hud_controller.gd
      map_controller.gd

  assets/
    art/
      tilesets/
      sprites/
      vfx/
    audio/
      music/
      sfx/
    fonts/

  tests/
    generation/
      test_floor_connectivity.gd
      test_no_softlock_paths.gd
    systems/
      test_item_stack_order.gd
      test_drop_tables.gd
```

## Build order
1. Boot scene + player movement + one combat room
2. Enemy archetypes + room clear logic
3. Room graph generator + floor traversal
4. Item system + drops + shop
5. Ability gating + secret/challenge rooms
6. Boss encounter and run completion
7. Meta progression save loop

