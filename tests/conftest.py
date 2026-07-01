import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "aeo_agent"))

# *_smoke.py scripts hit live APIs (Firecrawl, Anthropic) and have no assertions -
# they're for manual end-to-end runs, not the automated suite, so skip them here.
collect_ignore_glob = ["*_smoke.py"]
