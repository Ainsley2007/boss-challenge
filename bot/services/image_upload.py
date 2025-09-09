import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiohttp


class ImageUploadService:
    def __init__(self, storage_path="data/images"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_from_url(self, image_url: str, guild_id: int, user_id: int, image_type: str = "unknown", step: int = 1) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        return None
                    image_data = await response.read()
            
            guild_dir = self.storage_path / f"guild_{guild_id}"
            user_dir = guild_dir / f"user_{user_id}"
            type_dir = user_dir / image_type if image_type in ["before", "after"] else user_dir
            
            type_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            
            file_ext = self._get_file_extension(image_url, response.headers.get('content-type', ''))
            
            filename = f"step_{step}_{timestamp}_{unique_id}{file_ext}"
            file_path = type_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            abs_file_path = file_path.resolve()
            cwd = Path.cwd().resolve()
            
            try:
                relative_path = abs_file_path.relative_to(cwd)
                return str(relative_path)
            except ValueError:
                return str(abs_file_path)
            
        except Exception as e:
            print(f"Error saving image locally: {e}")
            return None
    
    def _get_file_extension(self, url: str, content_type: str) -> str:
        if '.' in url.split('/')[-1]:
            ext = '.' + url.split('.')[-1].split('?')[0].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                return ext
        
        content_type_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png', 
            'image/gif': '.gif',
            'image/webp': '.webp'
        }
        
        return content_type_map.get(content_type.lower(), '.jpg')
    
    def get_file_url(self, file_path: str) -> str:
        return f"file://{Path(file_path).absolute()}"
    
    def file_exists(self, file_path: str) -> bool:
        return Path(file_path).exists()
    
    def is_configured(self) -> bool:
        return self.storage_path.exists()


_upload_service = None

def get_image_service() -> ImageUploadService:
    global _upload_service
    if _upload_service is None:
        _upload_service = ImageUploadService()
    return _upload_service
