import json
import os

new_dir = '/Users/SAMSUNG/Desktop/한이음/gpt api'
os.chdir(new_dir)

# JSON 파일에서 데이터를 불러옴
with open('dataset초보자.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# JSONL 파일에 데이터를 저장함
with open('dataset초보자.jsonl', 'w', encoding='utf-8') as f:
    for entry in data:
        json.dump(entry, f, ensure_ascii=False)
        f.write('\n')