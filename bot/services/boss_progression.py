import random


class BossProgressionService:
    def __init__(self):
        self.boss_list = [
            "Sol Heredit",
            "TzKal-Zuk",
            "Yama", 
            "Great olm",
            "Phosani's Nightmare",
            "TOA - 300 invocation",
            "Doom of Mokhaiotl (1-8)",
            "Corrupted Hunleff",
            "The Leviathan",
            "The Wisperer",
            "Corporeal Beast",
            "Vardorvis",
            "TOA - 150 invocation",
            "Duke Sucellus",
            "Phantom Muspah",
            "Vorkath",
            "Zulrah",
            "TzTok-Jad",
            "Crystalline Hunleff",
            "K'ril Tsutsaroth",
            "Hueycoatl",
            "General Graardor",
            "Commander Zilyana",
            "Kree'arra",
            "Callisto",
            "Venenatis",
            "Vet'ion",
            "TOB - entry mode",
            "Royal Titans",
            "Zalcano",
            "Kalphite Queen",
            "Perilous Moons",
            "Artio",
            "Sarachnis",
            "Chaos Elemental",
            "Dagannoth Kings",
            "Spindel",
            "Deranged Archeologist",
            "King Black Dragon",
            "Calvar'ion",
            "Amoxliatl",
            "Giant Mole",
            "Scorpia",
            "Crazy Archeologist",
            "Scurrius",
            "Bryophyta",
            "Barrows Brothers",
            "Obor"
        ]
        self.difficulty_boss_lists = {
            "easy": list(reversed([
                "TOA - 150 invocation",
                "Phantom Muspah",
                "Vorkath",
                "Zulrah",
                "TzTok-Jad",
                "Crystalline Hunleff",
                "TOB - entry mode",
                "Royal Titans",
                "Zalcano",
                "Perilous Moons",
                "Artio",
                "Sarachnis",
                "Dagannoth Rex",
                "Spindel",
                "Deranged Archeologist",
                "King Black Dragon",
                "Calvar'ion",
                "Amoxliatl",
                "Giant Mole",
                "Scorpia",
                "Crazy Archeologist",
                "Scurrius",
                "Bryophyta",
                "Barrows Brothers",
                "Obor"
            ])),
            "normal": list(reversed([
                "Phosani's Nightmare",
                "TOA - 300 invocation",
                "Doom of Mokhaiotl (1-7)",
                "Corrupted Hunleff",
                "The Leviathan",
                "The Wisperer",
                "Corporeal Beast",
                "Vardorvis",
                "TOA - 150 invocation",
                "Duke Sucellus",
                "Phantom Muspah",
                "Vorkath",
                "Zulrah",
                "TzTok-Jad",
                "Crystalline Hunleff",
                "K'ril Tsutsaroth",
                "Hueycoatl",
                "General Graardor",
                "Commander Zilyana",
                "Kree'arra",
                "Callisto",
                "Venenatis",
                "Vet'ion",
                "TOB - entry mode",
                "Royal Titans",
                "Zalcano",
                "Perilous Moons",
                "Artio",
                "Sarachnis",
                "Dagannoth Kings",
                "Spindel",
                "Deranged Archeologist",
                "King Black Dragon",
                "Calvar'ion",
                "Amoxliatl",
                "Giant Mole",
                "Scorpia",
                "Crazy Archeologist",
                "Scurrius",
                "Bryophyta",
                "Barrows Brothers",
                "Obor"
            ])),
            "hard": list(reversed(self.boss_list.copy())),
            "extreme": ["Corrupted Hunleff"],
        }
    
    def get_boss_name(self, boss_index: int) -> str:
        if 0 <= boss_index < len(self.boss_list):
            return self.boss_list[-(boss_index + 1)]
        return "Unknown Boss"
    
    def get_next_boss(self, progress: int, mode: str = "normal") -> str:
        return self.get_next_boss_for_difficulty(progress, mode)
    
    def get_max_bosses_for_mode(self, mode: str) -> int:
        if mode == "extreme":
            return -1
        return len(self.difficulty_boss_lists.get(mode, []))
    
    def get_mode_info(self, mode: str) -> dict:
        mode_configs = {
            "easy": {
                "emoji": "🌱",
                "name": "Easy Mode",
                "description": "Obor → TOA 150 Invocation",
                "color_name": "green"
            },
            "normal": {
                "emoji": "🛡️",
                "name": "Normal Mode",
                "description": "Obor → Phosani's Nightmare",
                "color_name": "blue"
            },
            "hard": {
                "emoji": "🔥",
                "name": "Hard Mode",
                "description": "Obor → Sol Heredit",
                "color_name": "red"
            },
            "extreme": {
                "emoji": "💀",
                "name": "Extreme Mode",
                "description": "Corrupted Hunleff → Infinite Random",
                "color_name": "purple"
            }
        }
        return mode_configs.get(mode, mode_configs["normal"])
    
    def get_difficulty_boss_list(self, mode: str) -> list[str]:
        return self.difficulty_boss_lists.get(mode, [])
    
    def get_next_boss_for_difficulty(self, progress: int, mode: str) -> str:
        if mode == "extreme":
            if progress == 0:
                return "Corrupted Hunleff"
            else:
                return None
        
        boss_list = self.get_difficulty_boss_list(mode)
        if progress >= len(boss_list):
            return None
        return boss_list[progress]
    
    def get_random_boss_for_extreme(self) -> str:
        return random.choice(self.boss_list)
    
    def is_difficulty_complete(self, progress: int, mode: str) -> bool:
        if mode == "extreme":
            return False
        boss_list = self.get_difficulty_boss_list(mode)
        return progress >= len(boss_list)
