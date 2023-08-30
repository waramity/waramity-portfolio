from app import redis, db
from app.models import Prompt

import re

def sync_copies():
    prompt_copies_keys = [key for key in redis.keys() if re.search(r'prompt:([A-Fa-f0-9*]+):copies', key.decode('utf-8'))]
    for key in prompt_copies_keys:
        value = redis.get(key)
        prompt_id = re.search(r'prompt:([A-Fa-f0-9*]+):copies', key.decode('utf-8')).group(1)
        prompt = Prompt.query.get(prompt_id)
        if prompt:
            prompt.copies += int(value)
    db.session.commit()
    redis.flushdb()
