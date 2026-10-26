<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# How the battle engine works

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers what happens inside a battle: the server that applies the rules, the
per-battler clients that draw and take input, the messages between them, the turn
sequence, and battle scripts. The guides on specific changes build on it:
[moves.md](moves.md) (move data and effects), [abilities.md](abilities.md) (where each
kind of ability acts), [trainers.md](trainers.md) (parties, starting a battle, the AI).
[engine.md](engine.md) covers the tasks, overlays and heaps mentioned here.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `gBattleMainFunc`, `gBattleScriptingCommandsTable` | the **server**: `BattleContext_Main` runs one controller command per step (§4) |
| battle controllers (`BattleControllerPlayer`, `...Opponent`, `...LinkPartner`), `gBattleControllerExecFlags` | the **clients**: one `OpponentData` per battler, whatever side it is on (§3) |
| `BtlController_EmitPrintString` → `MarkBattlerForControllerExec` | `BattleController_Emit*` → `SendMessage` (§3) |
| `waitmessage`, `waitstate` | the `Wait` script command (§3) |
| `data/battle_scripts_1.s` (one big file), `gBattleScriptsForMoveEffects` | three folders of small files: move scripts, effect scripts, subscripts (§5) |
| `gBattlerAttacker`, `gBattlerTarget`, `gBattleMons` | `ctx->battlerIdAttacker`, `ctx->battlerIdTarget`, `ctx->battleMons` (§7) |
| `gBattleMoveDamage`, `gMoveResultFlags` | `ctx->damage` / `ctx->hpCalc`, `ctx->moveStatusFlag` |
| `gBattleCommunication`, `gBattleScripting` | script variables `BSCRIPT_VAR_*` (§5) |

## 1. Where the code is

**The file names are misleading.** `battle_controller_player.c` is the server for every
battle and has nothing to do with the player. `battle_controller_opponent.c` is the client
code for *all* battlers, the player's included.

| File (`src/battle/`) | What it is |
|---|---|
| `battle_022378C0.c` | `Battle_Run`: the battle application's outer states (link setup, vs screen, battle, end screen, evolution) and the overlay swaps |
| `battle_main.c` | creating and freeing a battle: graphics, `BattleSystem` from `BattleSetup`, the per-step loop `Battle_BattleMain`, choosing the link server |
| `battle_controller_player.c` | **the server**: `BattleContext_Main` and the 46 controller commands (the turn sequence), accuracy, disobedience |
| `battle_command.c` | **battle script commands**: `RunBattleScript` and one `BtlCmd_*` function per command |
| `battle_util.c` | rules helpers for both: damage (`CalcMoveDamage`), speed order, abilities, held items, side-effect tables, the script stack |
| `battle_controller.c` | **messages from the server**: every `BattleController_Emit*` and the message queues |
| `battle_controller_opponent.c` | **the clients**: `OpponentData_RunCommand` and its 68 handlers; the input tasks for the player, AI, link, recording, Safari and Pal Park |
| `battle_system.c` | `BattleSystem` getters and setters, message formatting |
| `trainer_ai.c` | the trainer AI ([trainers.md](trainers.md#the-ai)) |
| `battle_input.c`, `battle_cursor.c`, `battle_finger.c` | the touch-screen menus |
| `battle_party_menu.c`, `battle_bag_menu.c` | the in-battle party and bag screens |
| `battle_anim_*.c` | move and ball animations |
| `battle_hp_bar.c`, `party_gauge.c` | health bars, the party ball gauge |

The scripts are in `files/battledata/script/` (§5). The command table that numbers the
script commands is in assembly: `sBattleScriptCommandTable` in
[asm/overlay_12_battle_command.s](../../asm/overlay_12_battle_command.s). Battle text is
`files/msgdata/msg/msg_0197.json`, and attack messages ("X used Y!") are `msg_0003`.

The code is split across several overlays ([engine.md §5](engine.md#5-overlays)):
`OVY_12` (the core), `OVY_6`, `OVY_7` (animations), `OVY_10` (trainer AI) and `OVY_8`
(party and bag). `OVY_7`, `OVY_8` and `OVY_10` share an address, so only one of them is
loaded at a time, and code in one must not call the others.

## 2. A battle from start to end

A battle is an application, `gOverlayTemplate_Battle` in
[src/launch_application.c](../../src/launch_application.c). Its argument, `BattleSetup`
([include/battle/battle_setup.h](../../include/battle/battle_setup.h)), carries the
parties, trainers, battle type, terrain and options in. It carries the outcome
(`winFlag`) and the updated parties back out ([trainers.md](trainers.md#starting-a-battle) shows how a script
starts one). Its `exec`, `Battle_Run`, steps through:

1. Creates `HEAP_ID_BATTLE` (0xB0000 bytes). Everything in the battle is allocated from it.
2. Link battles only: connects, then shows the party preview and the vs screen.
3. Loads `OVY_6` and `OVY_7`. `Battle_BattleInit` sets up the graphics and `Battle_BattleMain` runs the battle (§3).
4. Shows the end-of-battle screen if there is one, then destroys the heap.
5. Runs the evolution scene once for each Pokémon that should evolve
   (`BattleSystem_CheckEvolution`).

`BattleSystem` (in `battleSystem`) is the whole battle: graphics, message printers,
parties, the server's `BattleContext *ctx`, and one `OpponentData *opponentData[4]` per
battler.

## 3. The server and the clients

The battle is split in two halves that only talk through messages:

```
            BattleContext  (the server: one, on one console)
            rules, HP, status, turn order, scripts
                 |                       ^
   commands: "print this", "play that",  |  replies: chosen action, move, target
   "update this HP bar"   (direction 1)  |  (direction 0), and "command done"
                 v                       |  (direction 2)
   OpponentData[0]  OpponentData[1]  OpponentData[2]  OpponentData[3]
   (clients: one per battler: sprite, HP bar, messages, and where its input comes from)
```

- **The server** (`BattleContext`, `ctx`) holds the state of the battle: the
  `battleMons`, field and side conditions, the turn order, the running script. It never
  draws anything. To show something, it sends a command to a battler's client.
- **A client** (`OpponentData`) draws its battler and gets its decisions. It never changes
  the rules state. Each client has a set of **input tasks** that decide where its choices
  come from (`OpponentData_SetInputTasks`):

  | Input | Battlers |
  |---|---|
  | player (touch menus) | the player's own battlers |
  | AI (`TrainerAI_SelectCommand` etc.) | trainer and wild opponents, the AI partner |
  | link | battlers controlled by another console |
  | recorded | Battle Video playback |
  | Safari, Pal Park | the special command menus |

In single-player the server and the four clients run on the same DS. In a **link battle**
one console is chosen as the server (`BattleSystem_ChooseLinkServer`, from a value each
player sends). It runs `BattleContext_Main`; every console runs the clients, and messages
travel over the wireless link. That is why the server must never touch graphics, and why
everything a client needs comes in its packet.

### Steps

`Battle_BattleMain` is one step of the server followed by one step of each client, with
messages delivered in between. In single-player it runs **two steps per frame** (60 per
second), and in a link battle one (30 per second). Script commands that count frames
(`WaitTime`, `WaitButtonABTime`) add 2 per step in a link battle to keep the same speed.

### Messages

Three queues, each with a 4-byte header (`BattleController_SendLocalMessage`):

| Direction | From → to | Lands in | Sent by |
|---|---|---|---|
| 1 | server → one battler's client | `opponentData[b]->controllerData` | `BattleController_Emit*` (75 functions in `battle_controller.c`) |
| 0 | client → server | `ctx->battleBuffer[b]` (256 bytes) | `BattleController_EmitSelectedCommand`, `...SelectedMove`, `...SelectedTarget`, `...SelectedBagItem`, `...PartyMenuResult`, `...AlertMessageAck` |
| 2 | client → server: "finished command N" | clears an entry in `ctx->linkBuffer` | `BattleController_EmitClearCommand(battleSystem, battlerId, command)` |

A packet is a struct whose first byte is the client command number. The layouts are in
[include/battle/battle_controller_packets.h](../../include/battle/battle_controller_packets.h).
Messages are delivered one at a time between steps, and only into an empty inbox. Until
then a message waits in its queue, a 0x1000-byte ring.

### Waiting for the clients

Every command sent to a client is recorded in `ctx->linkBuffer[console][battler]` (up to
16 per battler). The client removes it with `EmitClearCommand` when it has **finished**,
which for a message or animation is many frames after it started. The `Wait` script
command (`BtlCmd_Wait`) holds the script until the buffer is empty. So the usual script
pattern is "send, `Wait`":

```
    PrintAttackMessage          // the client starts printing
    Wait                        // ... until every client reports done
    PlayMoveAnimation BATTLER_CATEGORY_ATTACKER
    Wait
```

`Link_QueueNotEmpty` is **misnamed**: it returns `TRUE` when the buffer *is* empty. After
1800 steps without emptying, the link times out with a communication error.

**A client command that never sends `EmitClearCommand` hangs the battle** at the next
`Wait`. Most handlers in `battle_controller_opponent.c` start a SysTask that does the work
over several frames, then clear the inbox (`OpponentData_ClearCommand`) so the next packet
can arrive. The task sends `EmitClearCommand` and destroys itself when done
(`Task_WaitBattleMessage` is a short example).

### Choosing actions

The selection screen is the same mechanism in reverse. The server sends
`SelectCommand`, `SelectMove`, `SelectTarget`, `SelectItem` or `ShowMonList` to each
client. The client's input task (menu, AI or link) decides and replies with
`EmitSelected*` (direction 0) and `EmitClearCommand`. `SelectionScreenInput` on the
server reads `ctx->battleBuffer` until every battler has chosen. The choices go into
`ctx->playerActions[battler]`.

## 4. The turn: controller commands

The server is a state machine. `ctx->command` is the current controller command, and
`BattleContext_Main` runs `sPlayerBattleCommands[ctx->command]` once per step. The
names (`enum ControllerCommand`) are in `include/constants/battle.h`; many are still
numbers. If the battle has an
outcome (win, loss, run, catch), `BattleContext_Main` switches to `BattleEnd` (42) by
itself.

```
GET_BATTLE_MON -> START_ENCOUNTER -> TRAINER_MESSAGE -> SEND_OUT
                                          ^                 |
                                          |                 v
   TURN_END <- UPDATE_FIELD_CONDITION_EXTRA <- ...   SELECTION_SCREEN_INIT
      ^       (Future Sight, Perish Song, Trick Room)       |
      |                                                      v
   UPDATE_MON_CONDITION      (Leftovers, Leech Seed,        SELECTION_SCREEN_INPUT   each client chooses
      ^                       poison, burn, Bad Dreams...)   |
      |                                                      v
   UPDATE_FIELD_CONDITION    (screens, Wish, weather,       CALC_EXECUTION_ORDER -> BEFORE_TURN
      ^                       Gravity)                       |         (Focus Punch, Rage, Quick Claw)
      ^                                                      |
      |  all actions done                                    v
      +------------------------------------------ 8  ExecuteNextAction  <-------+
                                                     | by playerActions[next].command
                                                     v                           |
                     FIGHT_INPUT / ITEM_INPUT / POKEMON_INPUT / RUN_INPUT / SAFARI_*
                                                     |                           |
                                                     v                           |
                     (a move, below)  ...  40 ActionEnd  ------------------------+
```

Speed is sorted again before every action (`SortMonsBySpeed` in `ExecuteNextAction`), so a
speed change mid-turn affects who moves next.

**A move** (`FIGHT_INPUT`, 13):

| # | Function | Does |
|---|---|---|
| 23 | `TryMove` | Quick Claw; sleep, freeze, paralysis, confusion and other status checks; disobedience; PP; Magic Coat; target redirection. Then it loads the **move script** and runs it |
| 24 | `CheckMoveHit` | accuracy and evasion; type effectiveness; immunities (Levitate, Volt Absorb...) |
| 25 | `DirectSideEffect` | the effect of a status move (Swords Dance, Thunder Wave) |
| 26 | `CheckMoveFailure` | out of PP, missed → their subscripts |
| 27 | `UseMove` | `BATTLE_SUBSCRIPT_USE_MOVE`: "X used Y!" and the animation |
| 28 | `HpCalc` | apply the damage: `BATTLE_SUBSCRIPT_UPDATE_HP` (flash, HP bar, faint check) |
| 29 | `AfterDamage` | critical hit message, "It's super effective!", secondary effects of damaging moves (burn chance...), Rage, King's Rock flinch |
| 31 | `AfterMoveEffects` | abilities and items that react to the hit (Synchronize, Static, berries) |
| 32 | `CheckMultiHit` | next hit of a multi-hit move: back to 24 |
| 34 | `FaintAfterMove` | faint messages |
| 35 | `NextMoveTarget` | spread moves: next target, back to 23 |
| 36 | `CheckSelfDestruct` | Selfdestruct and Explosion |
| 37 | `AfterMoveItems` | Shell Bell, Life Orb recoil |
| 39 | `UpdateMoveHistory` | last move used, for Encore, Mirror Move, Disable... |
| 40 | `ActionEnd` | reset per-action state, back to 8 |

**Running a script from a controller command.** Every command that needs a battle script
uses the same three lines: load the script, say which command comes next, and switch to
`RUN_SCRIPT` (22), which runs it until `End`:

```c
ReadBattleScriptFromNarc(ctx, NARC_a_0_0_1, BATTLE_SUBSCRIPT_MISSED); // which script
ctx->commandNext = CONTROLLER_COMMAND_34;                              // where to go after it
ctx->command = CONTROLLER_COMMAND_RUN_SCRIPT;
```

A command that runs a script and then continues *itself* sets
`ctx->commandNext = ctx->command`. It keeps a state counter (`ctx->tryMoveState`,
`ctx->afterMoveEffectState`...) so that it resumes where it left off and doesn't start the
same script again.

## 5. Battle scripts

### The three kinds

| Kind | Folder (`files/battledata/script/`) | NARC | Indexed by | Started by |
|---|---|---|---|---|
| move script | `move_script/move_script_NNNN_Name.s` | `a/0/0/0` | move id | `TryMove` (23), `GoToMoveScript` |
| effect script | `effect_script/effect_script_NNNN.s` | `a/0/3/0` | `MOVE_EFFECT_*` | `GoToEffectScript` (the move's `effect`) |
| subscript | `subscript/subscript_NNNN_Name.s` | `a/0/0/1` | `BATTLE_SUBSCRIPT_*` | controller commands (136 places), `Call`, `GoToSubscript` |

A file's position in its folder's `meson.build` list is its id. The `BATTLE_SUBSCRIPT_*`
names are in
[include/constants/battle_subscript.h](../../include/constants/battle_subscript.h).

### Following one move

Pound:

```
move_script_0001_Pound.s        GoToEffectScript                  -> effect 0
effect_script_0000.s            CalcCrit / CalcDamage / End        sets ctx->damage
  (the controller continues: 24 hit check, 26, 27 UseMove)
subscript_0001_UseMove.s        Call BATTLE_SUBSCRIPT_ATTACK_MESSAGE_AND_ANIMATION
subscript_0076_...              PrintAttackMessage / Wait / PlayMoveAnimation / Wait
  (28 HpCalc)
subscript_0002_UpdateHp.s       PlayMoveHitSound / FlickerMon / Wait / UpdateHealthBar / Wait / TryFaintMon
```

Swords Dance (effect 50) has no damage. Its effect script only records what should happen:

```
    UpdateVar OPCODE_SET, BSCRIPT_VAR_SIDE_EFFECT_FLAGS_DIRECT, MOVE_SIDE_EFFECT_TO_ATTACKER|MOVE_SUBSCRIPT_PTR_ATTACK_UP_2_STAGES
    End
```

At command 25, `BattleSystem_TryDirectSideEffect` reads the flags. The low 23 bits
(`MOVE_SUBSCRIPT_PTR_*`) index `sMoveStatusChangeScripts` in `battle_util.c`, which gives
the subscript (here `UpdateStatStage`). The high bits (`MOVE_SIDE_EFFECT_TO_ATTACKER`,
`_TO_DEFENDER`, `_ON_HIT`...) say who it applies to and when. The three flag variables differ
in timing:

| Variable | Applied | Used by |
|---|---|---|
| `SIDE_EFFECT_FLAGS_DIRECT` | at 25, before the move's message | status moves: the effect *is* the move |
| `SIDE_EFFECT_FLAGS_INDIRECT` | at 29, after damage, if `secondaryEffectChance` rolls | damaging moves with a side effect (Ember's burn) |
| `SIDE_EFFECT_FLAGS_ABILITY` | at 29, with the indirect ones | nothing in the retail scripts sets it; abilities such as Static run their own subscripts ([abilities.md](abilities.md#where-an-ability-can-act)) |

So most effects need no script logic of their own. A new effect is usually a short effect
script that sets a flag or variable, plus a subscript if the result is new.

### The format

Each command is a list of 32-bit words: the command number, then its arguments. The
macros in [asm/macros/btlcmd.inc](../../asm/macros/btlcmd.inc) write them:

```
    .macro CompareVarToValue op, var, val, jump
    .long 32
    .long \op
    .long \var
    .long \val
    .long (\jump-.) / 4 - 1      // a jump is an offset within this file
    .endm
```

- **Jumps** (`GoTo`, and the last argument of every `Compare*`, `Check*` and `Try*`) go to
  a label in the same file. The compare commands jump when the condition is true.
- **`Call BATTLE_SUBSCRIPT_X`** runs another file and returns. The stack is **4 deep**.
- **`GoToSubscript`**, **`GoToEffectScript`** and **`GoToMoveScript`** replace the current
  file and don't return.
- **`End`** returns from a `Call`, or ends the script.
- A script file must be **under 1600 bytes** (400 words): `ReadBattleScriptFromNarc`
  asserts on it. Split long logic into subscripts.

**When it runs.** In single-player, `RunBattleScript` runs commands one after another in
the same step until one stops for the step (`Wait`, `WaitTime`, `WaitButtonABTime`,
`End`, and a few others that set `ctx->battleContinueFlag`). A link battle runs one command
per step.

### Variables and operators

Scripts read and change the server's state through numbered variables (`BSCRIPT_VAR_*`,
71 of them, [include/constants/battle_script.h](../../include/constants/battle_script.h)),
mapped to `ctx` fields by `BattleScriptGetVarPointer`. Examples: `BSCRIPT_VAR_DAMAGE`,
`_HP_CALC`, `_BATTLER_ATTACKER`, `_MOVE_NO_CUR`, `_BATTLE_STATUS`, `_FIELD_CONDITION`,
`_MESSAGE`, `_POWER_MULTI`.

| Command | Does |
|---|---|
| `UpdateVar op, var, value` | `op` from [include/constants/opcode.h](../../include/constants/opcode.h): `OPCODE_SET`, `_ADD`, `_SUB`, `_MUL`, `_DIV`, `_FLAG_ON`, `_FLAG_OFF`... |
| `UpdateVarFromVar op, var, var2` | the same with a variable |
| `CompareVarToValue op, var, value, jump` | `OPCODE_EQU`, `_NEQ`, `_GT`, `_LTE`, `_FLAG_SET`, `_FLAG_NOT`, `_AND` |
| `CompareMonDataToValue op, battler, BMON_DATA_x, value, jump` | a field of a battling Pokémon (101 `BMON_DATA_*` in `constants/battle.h`) |
| `UpdateMonData op, battler, BMON_DATA_x, value` | change one |

Commands that act on a Pokémon take a **battler category** (`BATTLER_CATEGORY_*` in
`constants/battle.h`) instead of a slot: `_ATTACKER`, `_DEFENDER`, `_SIDE_EFFECT_MON` (the
one a side effect applies to), `_FAINTED_MON`, `_SWITCHED_MON`, `_ABILITY_MON`, `_ALL`,
`_MSG_TEMP`... `BattleSystem_GetBattlerIDBySide` turns one into a battler id.

### The commands

There are 225 (0-224), listed with their arguments in `btlcmd.inc`. By kind:

| Kind | Examples |
|---|---|
| send to clients (follow with `Wait`) | `PrintMessage`, `PrintAttackMessage`, `PlayMoveAnimation`, `PlayBattleAnimation`, `UpdateHealthBar`, `FlickerMon`, `PlayFaintAnimation`, `PokemonSendOut`, `PlaySound`, `ShowParty` |
| wait | `Wait`, `WaitTime`, `WaitButtonABTime`, `WaitMonSelection`, `WaitYesNoResult` |
| flow | `GoTo`, `Call`, `CallFromVar`, `GoToSubscript`, `GoToEffectScript`, `GoToMoveScript`, `End` |
| compare and branch | `CompareVarToValue`, `CompareMonDataToValue`, `CheckAbility`, `CheckItemHoldEffect`, `CheckSideCondition`, `IfSameSide`, `IfTurnFlag`, `CheckSubstitute` |
| variables and data | `UpdateVar`, `UpdateVarFromVar`, `UpdateMonData`, `UpdateMonDataFromVar`, `Random`, `DivideVarByValue` |
| damage | `CalcCrit`, `CalcDamage`, `CalcMaxDamage`, `ApplyTypeEffectiveness`, `CheckMoveHit`, `SetMultiHit` |
| stats and status | `ChangeStatStage`, `ResetAllStatChanges`, `ClearVolatileStatus`, `SetHealthbarStatus`, `TryFaintMon` |
| one move's special logic | `TryReflect`, `TrySubstitute`, `Transform`, `Metronome`, `CalcFlailPower`, `CalcHiddenPowerParams`, `TryFling`... (about 80 `Try*`/`Calc*` commands) |
| messages | `PrintMessage`, `PrintGlobalMessage`, `BufferMessage`, `PrintTrainerMessage`, `PrintSendOutMessage` |
| end of battle | `CalcExpGain`, `StartGetExpTask`, `PayPrizeMoney`, `StartCatchMonTask`, `GenerateEndOfBattleItem`, `SetLinkBattleResult` |

`PrintMessage` takes a message id from `msg_0197` and a tag that says what to fill in
(`TAG_NICKNAME_ABILITY` and so on, in `constants/message_tags.h`), followed by battler
categories. See [abilities.md](abilities.md#when-you-need-your-own-message-or-script) for
adding a message or a subscript.

### Adding a script command

Use one only when no combination of existing commands does the job (most new behaviour is
easier in C, in a controller command or a `battle_util.c` helper).

1. Write the function in `src/battle/battle_command.c` and declare it in
   `include/battle/battle_command.h`:

   ```c
   BOOL BtlCmd_CheckIsShiny(BattleSystem *battleSystem, BattleContext *ctx) {
       BattleScriptIncrementPointer(ctx, 1);            // skip the command number

       int side = BattleScriptReadWord(ctx);           // arguments, in order
       int jump = BattleScriptReadWord(ctx);

       int battlerId = BattleSystem_GetBattlerIDBySide(battleSystem, ctx, side);
       if (ctx->battleMons[battlerId].shiny) {
           BattleScriptIncrementPointer(ctx, jump);     // take the jump
       }
       return FALSE;                                    // TRUE is only for ending the script
   }
   ```

   To wait across steps, set `ctx->battleContinueFlag = TRUE` and step the pointer back
   onto the command (`BattleScriptIncrementPointer(ctx, -N)`), as `BtlCmd_WaitTime` does.
2. Add `.word BtlCmd_CheckIsShiny` **after** `.word BtlCmd_EndScript` at the end of
   `sBattleScriptCommandTable` in `asm/overlay_12_battle_command.s`. Inserting it anywhere
   else renumbers every command after it and breaks every script.
3. Add the macro to `asm/macros/btlcmd.inc`, using the next number (225):

   ```
       .macro CheckIsShiny battler, jump
       .long 225
       .long \battler
       .long (\jump-.) / 4 - 1
       .endm
   ```

Commands 222 and 223 (`COMMAND_DE`, `COMMAND_DF`) are named only by number. 222 checks
whether a trainer has a given battle message and 223 starts a screen fade.

## 6. Adding a client command

For something the server should *show* that no existing command does: a new sprite
effect, say.

1. A packet struct in `battle_controller_packets.h`, starting with `u8 command`.
2. An `Emit` function in `battle_controller.c` that fills it and calls
   `SendMessage(battleSystem, 1, battlerId, &packet, sizeof(packet))`.
3. A handler appended to `sOpponentCommandHandlers` in `battle_controller_opponent.c`.
   Its index is the command number.
4. The handler, or the SysTask it starts, must end with
   `BattleController_EmitClearCommand(battleSystem, battlerId, command)`. It must also
   call `OpponentData_ClearCommand(opponentData)` so that the next packet can be
   delivered.
5. A script command that calls the `Emit` function (§5), used with a `Wait` after it.

Everything the client needs must be in the packet. In a link battle the client may be on
another console, with no access to `ctx`.

## 7. Glossary

| Term | Meaning |
|---|---|
| battler, `battlerId` | a position on the field, 0-3. `BATTLER_PLAYER` 0, `BATTLER_ENEMY` 1, `BATTLER_PLAYER2` 2, `BATTLER_ENEMY2` 3: **odd is the enemy side**. Single battles use 0 and 1 |
| battler type | the slot's screen position (`BATTLER_TYPE_SOLO_PLAYER`, `..._PLAYER_SIDE_SLOT_1`...). `BattleSystem_GetBattlerType`; `& BATTLER_TYPE_IS_ENEMY` tests the side |
| side | 0 = player, 1 = enemy. `fieldSideConditionFlags[side]` holds Reflect, Spikes, Tailwind... |
| partner | the other battler on the same side in a double battle: `BattleSystem_GetBattlerIdPartner` |
| `BattleSystem` | the whole battle: graphics, parties, server and clients |
| `BattleContext`, `ctx` | the server's rules state |
| `OpponentData` | a client: one per battler, either side |
| `BattleSetup` | the arguments a battle starts with and the results it returns |
| `BattleMon`, `ctx->battleMons[b]` | a Pokémon on the field: stats, stat stages, types, ability, HP, status. Copied back to the party with `CopyBattleMonToPartyMon` |
| `selectedMonIndex[b]` | the party slot of the Pokémon in battler `b` |
| `status` | the lasting status: sleep turns, poison, burn, freeze, paralysis, bad poison (`STATUS_*`) |
| `status2` | volatile conditions cleared on switching: confusion, flinch, attract, Focus Energy, Substitute, Transform... (`STATUS2_*`) |
| `moveEffectFlags` | more volatile conditions set by moves: Leech Seed, Curse, Ingrain, Yawn, charge turns... (`MOVE_EFFECT_FLAG_*`) |
| `statChanges[]` | stat stages, 0-12 with 6 as neutral (`DEFAULT_STAT_STAGE`) |
| `fieldCondition` | weather, Gravity, Trick Room... (`FIELD_CONDITION_*`) |
| `battleStatus`, `battleStatus2` | per-action flags, such as "no blink" or "move succeeded" |
| `moveStatusFlag` | the result of the current move: missed, super effective, not very effective, failed, OHKO... (`MOVE_STATUS_*`) |
| `battlerIdAttacker`, `battlerIdTarget` | who is using the move and who it hits now |
| `battlerIdStatChange` | who the current side effect applies to (`BATTLER_CATEGORY_SIDE_EFFECT_MON`) |
| `battlerIdTemp`, `msgTemp`, `moveTemp`, `itemTemp`, `abilityTemp`, `calcTemp` | scratch values that scripts and messages use |
| `moveNoCur` | the move being used now (after Metronome, Sleep Talk...) |
| `damage` | the damage being worked out. `hpCalc` is the HP change applied by `UpdateHealthBar` (negative = damage) |
| `turnOrder` | battlers by speed (Trick Room applied); `executionOrder` is the order actions run in, with switching and items first |
| `playerActions[b]` | what battler `b` chose this turn |
| controller command | a step of the server's state machine (`CONTROLLER_COMMAND_*`, §4) |
| client command | a numbered display or input job sent to a client (§3, §6) |
| subscript | a shared battle script (§5) |
| side effect | what a move does besides damage, named by `MOVE_SUBSCRIPT_PTR_*` (§5) |
| `linkBuffer` | the server's record of client commands not yet finished. `Wait` waits for it to empty |
| `battleBuffer[b]` | where client `b`'s replies land |
| AI flags, `aiFlags` | which AI routines a trainer uses ([trainers.md](trainers.md#ai-flags)) |

## Where to look

| To change | Look in |
|---|---|
| the order of a turn, what happens between two steps | the controller command in `battle_controller_player.c` (§4) |
| accuracy, disobedience, status that stops a move | `BattleSystem_CheckMoveHit`, `TryDisobedience`, `BattleControllerPlayer_CheckAttackerStatus` |
| damage, critical hits, speed order | `CalcMoveDamage`, `TryCriticalHit`, `CheckSortSpeed` in `battle_util.c` |
| what a move effect does | its `effect_script_NNNN.s` and the subscripts it reaches ([moves.md](moves.md#effects)) |
| which subscript a side effect runs | `sMoveStatusChangeScripts` in `battle_util.c` |
| an ability or held item | [abilities.md](abilities.md#where-an-ability-can-act) |
| a message's text | `msg_0197.json`; the script line that prints it |
| what a client shows for a command | its handler in `sOpponentCommandHandlers` |
| how the AI chooses | `trainer_ai.c` and `Task_AISelectCommand` ([trainers.md](trainers.md#the-ai)) |
| what a battle starts with or returns | `BattleSetup`, [trainers.md](trainers.md#starting-a-battle) |
