import argparse
import json
from pathlib import Path

from app.services.string_import_service import import_strings_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    summary = import_strings_jsonl(Path(args.input))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
