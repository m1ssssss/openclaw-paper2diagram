import json
import sys
from app.openclaw.agent import OpenClawAdapter


USAGE = (
    "Usage:\n"
    "  python -m app.openclaw_main local /absolute/path/to/paper.pdf [max_pages]\n"
    "  python -m app.openclaw_main runtime\n"
)


def main() -> None:
    if len(sys.argv) < 2:
        print(USAGE)
        raise SystemExit(1)

    mode = sys.argv[1].strip().lower()
    adapter = OpenClawAdapter()

    if mode == "local":
        if len(sys.argv) < 3:
            print(USAGE)
            raise SystemExit(1)
        pdf_path = sys.argv[2]
        max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        request = {
            "skill": "paper_to_diagram",
            "payload": {"pdf_path": pdf_path, "max_pages": max_pages},
        }
        result = adapter.run_local(request)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if mode == "runtime":
        adapter.serve_with_openclaw()
        return

    print(USAGE)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
