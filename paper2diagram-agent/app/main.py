import json
import sys
from app.orchestrator.pipeline import PaperToDiagramPipeline


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.main /absolute/path/to/paper.pdf [max_pages]")
        raise SystemExit(1)

    pdf_path = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    pipeline = PaperToDiagramPipeline()
    result = pipeline.run(pdf_path=pdf_path, max_pages=max_pages)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
