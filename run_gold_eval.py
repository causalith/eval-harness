from runpy import run_path
from pathlib import Path

run_path(str(Path(__file__).resolve().parent / "scripts" / "run_gold_eval.py"), run_name="__main__")
