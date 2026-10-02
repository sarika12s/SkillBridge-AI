import os
import re
from pathlib import Path

root = Path('.')
SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret[_-]?key|password|token|private[_-]?key)\s*[:=]\s*[\'"][^\'"]{8,}[\'"]')
]

# Whitelisted default development / sample tokens
WHITELIST_SNIPPETS = [
    "CHANGE_THIS",
    "skillbridge_ai_dev_secret_key",
    "skillbridge_docker_secret_key",
    "postgres",
    "root",
    "secret",
    "Bearer",
    "password123",
    "access_token",
]

suspicious = []
for p in root.rglob('*'):
    if p.is_dir():
        continue
    # Exclude virtual environments, node_modules, git, caches
    parts = set(p.parts)
    if any(x in parts for x in ['venv', 'node_modules', '.git', '.pytest_cache', 'dist', '__pycache__']):
        continue
    if p.name in ['.env', '.env.txt', 'package-lock.json']:
        continue
    if p.suffix in ['.py', '.ts', '.tsx', '.json', '.yml', '.yaml', '.ini', '.sql', '.md', '.txt']:
        try:
            content = p.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            for line_no, line in enumerate(lines, 1):
                for pat in SECRET_PATTERNS:
                    if pat.search(line):
                        if not any(w in line for w in WHITELIST_SNIPPETS):
                            suspicious.append((str(p), line_no, line.strip()[:60]))
        except Exception:
            pass

print(f"Total potential secret alerts: {len(suspicious)}")
for f, l, preview in suspicious:
    print(f"  {f}:{l} -> {preview}")
