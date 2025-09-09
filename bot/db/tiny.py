from datetime import datetime
from pathlib import Path

from tinydb import TinyDB, Query


class EventDatabase:
    def __init__(self, db_path="data/event_bot.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = TinyDB(db_path)
        self.participants = self.db.table('participants')
        self.submissions = self.db.table('submissions')
        self.completions = self.db.table('completions')
        self.extreme_archive = self.db.table('extreme_archive')
        self.discord_resources = self.db.table('discord_resources')
    
    def is_joined(self, guild_id: int, user_id: int) -> bool:
        User = Query()
        result = self.participants.search(
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )
        return len(result) > 0
    
    def join_user(self, guild_id: int, user_id: int) -> bool:
        return self.join_user_with_mode(guild_id, user_id, "normal")
    
    def join_user_with_mode(self, guild_id: int, user_id: int, mode: str) -> bool:
        if self.is_joined(guild_id, user_id):
            return False
        
        self.participants.insert({
            'guild_id': guild_id,
            'user_id': user_id,
            'progress': 0,
            'mode': mode,
            'joined_at': datetime.utcnow().isoformat()
        })
        return True
    
    def leave_user(self, guild_id: int, user_id: int) -> bool:
        User = Query()
        removed = self.participants.remove(
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )
        return len(removed) > 0
    
    def reset_user(self, guild_id: int, user_id: int) -> bool:
        if not self.is_joined(guild_id, user_id):
            return False
        
        User = Query()
        self.participants.update(
            {'progress': 0, 'reset_at': datetime.utcnow().isoformat()},
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )
        return True
    
    def add_completion(self, guild_id: int, user_id: int, before_url: str, after_url: str) -> bool:
        if not self.is_joined(guild_id, user_id):
            return False
        
        User = Query()
        user_data = self.participants.search(
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )[0]
        
        new_progress = user_data['progress'] + 1
        current_time = datetime.utcnow().isoformat()
        
        self.participants.update(
            {'progress': new_progress, 'last_completion': current_time},
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )
        
        self.submissions.insert({
            'guild_id': guild_id,
            'user_id': user_id,
            'step': new_progress,
            'before_url': before_url,
            'after_url': after_url,
            'ts': current_time
        })
        
        return True
    
    def get_user_progress(self, guild_id: int, user_id: int) -> int:
        if not self.is_joined(guild_id, user_id):
            return 0
        
        User = Query()
        user_data = self.participants.search(
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )
        return user_data[0]['progress'] if user_data else 0
    
    def get_user_mode(self, guild_id: int, user_id: int) -> str:
        if not self.is_joined(guild_id, user_id):
            return 'normal'
        
        User = Query()
        user_data = self.participants.search(
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )
        return user_data[0].get('mode', 'normal') if user_data else 'normal'
    
    def set_user_progress(self, guild_id: int, user_id: int, progress: int, mode: str) -> bool:
        User = Query()
        if not self.is_joined(guild_id, user_id):
            self.join_user_with_mode(guild_id, user_id, mode)
        self.participants.update(
            {
                'progress': max(0, int(progress)),
                'mode': mode,
                'last_completion': datetime.utcnow().isoformat()
            },
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )
        return True

    def set_next_extreme_boss(self, guild_id: int, user_id: int, boss_name: str | None) -> None:
        User = Query()
        self.participants.update(
            {'next_extreme_boss': boss_name},
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )

    def get_next_extreme_boss(self, guild_id: int, user_id: int) -> str | None:
        User = Query()
        row = self.participants.get((User.guild_id == guild_id) & (User.user_id == user_id))
        if row:
            return row.get('next_extreme_boss')
        return None
    
    def get_leaderboard(self, guild_id: int, limit: int = 10) -> list:
        User = Query()
        guild_participants = self.participants.search(User.guild_id == guild_id)
        
        sorted_participants = sorted(
            guild_participants,
            key=lambda x: (-x['progress'], x.get('last_completion', '9999-12-31'))
        )
        
        return sorted_participants[:limit]
    
    def mark_difficulty_complete(self, guild_id: int, user_id: int, difficulty: str, completion_time: str) -> bool:
        if not self.is_joined(guild_id, user_id):
            return False
        
        self.completions.insert({
            'guild_id': guild_id,
            'user_id': user_id,
            'difficulty': difficulty,
            'completion_time': completion_time,
            'completion_order': self.get_next_completion_order(guild_id, difficulty)
        })
        self.leave_user(guild_id, user_id)
        return True
    
    def get_completed_difficulties(self, guild_id: int, user_id: int) -> list[str]:
        User = Query()
        completions = self.completions.search(
            (User.guild_id == guild_id) & (User.user_id == user_id)
        )
        return [completion['difficulty'] for completion in completions]
    
    def get_next_completion_order(self, guild_id: int, difficulty: str) -> int:
        User = Query()
        existing_completions = self.completions.search(
            (User.guild_id == guild_id) & (User.difficulty == difficulty)
        )
        return len(existing_completions) + 1
    
    def get_finalized_leaderboard(self, guild_id: int, difficulty: str) -> list[dict]:
        User = Query()
        completions = self.completions.search(
            (User.guild_id == guild_id) & (User.difficulty == difficulty)
        )
        
        sorted_completions = sorted(completions, key=lambda x: x['completion_order'])
        return sorted_completions
    
    def get_live_leaderboard(self, guild_id: int, difficulty: str) -> list[dict]:
        User = Query()
        guild_participants = self.participants.search(User.guild_id == guild_id)
        
        mode_participants = [user for user in guild_participants if user.get('mode', 'normal') == difficulty]
        
        sorted_participants = sorted(
            mode_participants,
            key=lambda x: (-x['progress'], x.get('last_completion', '9999-12-31'))
        )
        
        return sorted_participants

    def archive_extreme_participant(self, guild_id: int, user_id: int) -> bool:
        User = Query()
        rows = self.participants.search((User.guild_id == guild_id) & (User.user_id == user_id))
        if not rows:
            return False
        row = rows[0]
        if row.get('mode') != 'extreme':
            return False
        self.extreme_archive.upsert({
            'guild_id': guild_id,
            'user_id': user_id,
            'progress': row.get('progress', 0),
            'last_completion': row.get('last_completion', ''),
            'next_extreme_boss': row.get('next_extreme_boss')
        }, (User.guild_id == guild_id) & (User.user_id == user_id))
        self.participants.remove((User.guild_id == guild_id) & (User.user_id == user_id))
        return True

    def get_extreme_live_with_archive(self, guild_id: int) -> list[dict]:
        User = Query()
        active = [u for u in self.participants.search(User.guild_id == guild_id) if u.get('mode') == 'extreme']
        archived = self.extreme_archive.search(User.guild_id == guild_id)
        active_ids = {u['user_id'] for u in active}
        combined = active + [a for a in archived if a['user_id'] not in active_ids]
        for u in combined:
            if 'mode' not in u:
                u['mode'] = 'extreme'
        combined_sorted = sorted(combined, key=lambda x: (-x.get('progress', 0), x.get('last_completion', '9999-12-31')))
        return combined_sorted
    
    def store_discord_resource(self, guild_id: int, resource_type: str, resource_id: int, metadata: dict = None):
        Resource = Query()
        self.discord_resources.upsert({
            'guild_id': guild_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat()
        }, (Resource.guild_id == guild_id) & (Resource.resource_type == resource_type))
    
    def get_discord_resource(self, guild_id: int, resource_type: str) -> int:
        Resource = Query()
        result = self.discord_resources.search(
            (Resource.guild_id == guild_id) & (Resource.resource_type == resource_type)
        )
        return result[0]['resource_id'] if result else None
    
    def remove_discord_resource(self, guild_id: int, resource_type: str) -> bool:
        Resource = Query()
        removed = self.discord_resources.remove(
            (Resource.guild_id == guild_id) & (Resource.resource_type == resource_type)
        )
        return len(removed) > 0
    
    def close(self):
        self.db.close()


_db_instance = None

def get_database() -> EventDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = EventDatabase()
    return _db_instance
