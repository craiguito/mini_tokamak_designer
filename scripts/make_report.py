from pathlib import Path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(f"Reports are generated automatically by runs under {root / 'data' / 'reports'}")

