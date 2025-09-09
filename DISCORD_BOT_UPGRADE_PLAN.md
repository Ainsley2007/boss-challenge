# Discord Boss Challenge Bot - Upgrade Plan

## Overview
This plan outlines the implementation of additional difficulty modes (Easy and Extreme) and improved leaderboard system with separate tracking per difficulty.

**Key Principles**:
- Maintain existing code structure and patterns
- Reuse existing functionality wherever possible
- Extend current systems rather than rewriting
- Preserve backward compatibility
- Follow established coding conventions

## Current State Analysis
- **Current Difficulties**: Normal (Obor → Phosani's Nightmare, 8 bosses) and Hard (Obor → Sol Heredit, 50 bosses)
- **Current Structure**: Single boss list with mode-based filtering
- **Current Channels**: `boss-challenge-normal`, `boss-challenge-hard`, `boss-completions`
- **Current Leaderboards**: Single leaderboard mixing all modes

## Phase 1: Boss List Restructuring and New Difficulties

### 1.1 Update Boss Progression Service
**File**: `bot/services/boss_progression.py`

**Changes**:
- **Reuse**: Keep existing `boss_list` and `get_boss_name()` method
- **Extend**: Update `get_mode_info()` to include Easy and Extreme modes
- **Extend**: Update `get_max_bosses_for_mode()` for new difficulties
- **Extend**: Update `get_next_boss()` to handle extreme mode random generation
- Add difficulty index mappings for each mode:
  - **Easy**: 25 bosses (Obor → TOA 150 Invocation)
  - **Normal**: 45 bosses (Obor → Phosani's Nightmare) 
  - **Hard**: 50 bosses (Obor → Sol Heredit)
  - **Extreme**: Starts at Corrupted Hunleff, then infinite random bosses

**New Methods**:
- `get_difficulty_boss_list(mode: str) -> list[str]` - Get ordered boss list for specific difficulty
- `get_difficulty_boss_indexes(mode: str) -> list[int]` - Get master list indexes for difficulty
- `get_next_boss_for_difficulty(progress: int, mode: str) -> str` - Get next boss in difficulty progression
- `get_random_boss_for_extreme() -> str` - Get random boss for extreme mode
- `is_difficulty_complete(progress: int, mode: str) -> bool` - Check if difficulty is finished

### 1.2 Update Mode Information
**New Mode Configurations**:
```python
modes = {
    "easy": {
        "emoji": "🌱",
        "name": "Easy Mode", 
        "description": "Obor → TOA 150 Invocation (25 bosses)",
        "color_name": "green",
        "boss_count": 25
    },
    "normal": {
        "emoji": "🐉",
        "name": "Normal Mode",
        "description": "Obor → Phosani's Nightmare (45 bosses)", 
        "color_name": "blue",
        "boss_count": 45
    },
    "hard": {
        "emoji": "💀",
        "name": "Hard Mode",
        "description": "Obor → Sol Heredit (50 bosses)",
        "color_name": "red", 
        "boss_count": 50
    },
    "extreme": {
        "emoji": "🔥",
        "name": "Extreme Mode",
        "description": "Corrupted Hunleff → Infinite Random",
        "color_name": "purple",
        "boss_count": -1  # Infinite
    }
}
```

### 1.3 Boss List Mapping
**Difficulty-Specific Boss Lists** (mapped to master boss list indexes):
- **Easy**: Specific 25 bosses from Obor to TOA 150 Invocation
- **Normal**: Specific 45 bosses from Obor to Phosani's Nightmare
- **Hard**: All 50 bosses from Obor to Sol Heredit
- **Extreme**: Starts with Corrupted Hunleff, then random selection from entire boss list

**Implementation Approach**:
- Create difficulty-specific boss index arrays
- Map each difficulty's boss names to their positions in the master list
- Handle extreme mode with special logic for random boss selection
- Maintain boss progression order within each difficulty

## Phase 2: Channel Organization with Categories

### 2.1 Create Boss Challenge Category
**File**: `bot/main.py` - Update `ensure_leaderboard_channels()`

**Changes**:
- **Reuse**: Keep existing channel creation logic and error handling
- **Extend**: Add category creation/retrieval before channel creation
- **Extend**: Update channel creation to include category assignment
- **Reuse**: Maintain existing `create_normal_mode_content()` and `create_hard_mode_content()` calls

**New Channel Structure**:
```
📁 Boss Challenge
├── #boss-challenge-easy
├── #boss-challenge-normal  
├── #boss-challenge-hard
├── #boss-challenge-extreme
└── #boss-completions
```

### 2.2 Update Channel Creation Logic
- Add category creation/retrieval
- Update channel topics with difficulty descriptions
- Ensure proper permissions for the category

## Phase 3: Database Schema Updates

### 3.1 Add Completion Tracking
**File**: `bot/db/tiny.py`

**Changes**:
- **Reuse**: Keep existing `participants` and `submissions` tables
- **Extend**: Add new fields to existing participant records
- **Reuse**: Maintain existing database methods and patterns

**New Tables**:
- `completions` table for tracking finished difficulties
- `leaderboards` table for finalized leaderboards per difficulty

**New Methods**:
- `mark_difficulty_complete(guild_id, user_id, difficulty, completion_time)`
- `get_completed_difficulties(guild_id, user_id) -> list[str]`
- `get_finalized_leaderboard(guild_id, difficulty) -> list[dict]`
- `get_live_leaderboard(guild_id, difficulty) -> list[dict]`

### 3.2 Update Participant Schema
**Add Fields**:
- `completed_difficulties: list[str]` - Track which difficulties user has finished
- `extreme_progress: int` - Special tracking for infinite extreme mode

## Phase 4: Enhanced Leaderboard System

### 4.1 Separate Leaderboards Per Difficulty
**File**: `bot/cogs/commands/leaderboard_manager.py`

**Changes**:
- **Reuse**: Keep existing `get_user_display_name()` and `get_rank_medal()` methods
- **Reuse**: Maintain existing embed creation patterns
- **Extend**: Add difficulty-specific leaderboard methods
- **Reuse**: Keep existing `create_normal_mode_content()` and `create_hard_mode_content()` patterns

**New Leaderboard Types**:
1. **Live Leaderboards**: Show current progress for active participants
2. **Finalized Leaderboards**: Show completion order for finished participants

**New Methods**:
- `create_live_leaderboard_embed(difficulty, guild_id)`
- `create_finalized_leaderboard_embed(difficulty, guild_id)`
- `update_all_difficulty_leaderboards(guild_id)`

### 4.2 Leaderboard Display Logic
- **Live Leaderboards**: Show current boss progress, next boss, completion percentage
- **Finalized Leaderboards**: Show completion order, completion time, total time taken
- **Combined View**: Option to see both live and finalized in one embed

## Phase 5: Command Updates

### 5.1 Update Join Command
**File**: `bot/cogs/commands/join_command.py`

**Changes**:
- **Reuse**: Keep existing validation and error handling logic
- **Reuse**: Maintain existing success/failure response patterns
- **Extend**: Add Easy and Extreme mode choices to existing choices
- **Extend**: Update welcome messages with difficulty-specific information
- **Reuse**: Keep existing leaderboard update calls

### 5.2 Update Submit Command  
**File**: `bot/cogs/commands/submit_command.py`

**Changes**:
- **Reuse**: Keep existing image validation and upload logic
- **Reuse**: Maintain existing progress update patterns
- **Extend**: Handle extreme mode random boss generation
- **Extend**: Check for difficulty completion
- **Reuse**: Keep existing leaderboard update calls

### 5.3 New Leaderboard Command Options
**File**: `bot/cogs/commands/leaderboard_command.py`

**Changes**:
- **Reuse**: Keep existing embed creation and error handling
- **Extend**: Add difficulty and type parameters to existing command
- **Reuse**: Maintain existing user display name logic

**New Parameters**:
- `difficulty`: Show leaderboard for specific difficulty
- `type`: "live" or "finalized" leaderboard
- `combined`: Show both live and finalized

## Phase 6: UI/UX Improvements

### 6.1 Enhanced Channel Content
**File**: `bot/cogs/commands/leaderboard_manager.py`

**Changes**:
- **Reuse**: Extend existing `create_normal_mode_content()` and `create_hard_mode_content()` patterns
- **Reuse**: Keep existing embed creation and field addition logic
- **Extend**: Create difficulty-specific boss progression embeds
- **Extend**: Add completion status indicators
- **Extend**: Show difficulty unlock requirements

### 6.2 Better Progress Tracking
- Visual progress bars in embeds
- Completion percentage displays
- Next boss previews with difficulty indicators

## Phase 7: Migration and Testing

### 7.1 Data Migration
- Create migration script for existing participants
- Ensure backward compatibility with current data
- Test with existing guild data

### 7.2 Testing Checklist
- [ ] All 4 difficulties work correctly
- [ ] Channel categories are created properly
- [ ] Leaderboards update correctly per difficulty
- [ ] Completion tracking works
- [ ] Extreme mode random boss generation
- [ ] Multiple difficulty participation
- [ ] Database migrations complete successfully

## Implementation Order

1. **Phase 1**: Boss list restructuring (foundation)
2. **Phase 2**: Channel organization (infrastructure) 
3. **Phase 3**: Database updates (data layer)
4. **Phase 4**: Leaderboard system (core functionality)
5. **Phase 5**: Command updates (user interface)
6. **Phase 6**: UI/UX improvements (polish)
7. **Phase 7**: Migration and testing (deployment)

## Success Criteria

- [ ] Users can participate in all 4 difficulties
- [ ] Each difficulty has its own channel in organized category
- [ ] Separate live and finalized leaderboards per difficulty
- [ ] Easy mode completion unlocks other difficulties
- [ ] Extreme mode provides infinite random boss progression
- [ ] All existing functionality preserved
- [ ] Clean, organized channel structure

## Notes

- Maintain backward compatibility with existing participants
- Use Discord embeds for better visual presentation
- Follow existing code style and conventions
- Ensure proper error handling for all new features
- Test thoroughly with multiple guilds and users
