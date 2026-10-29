import json
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app


def export_openapi():
    openapi_schema = app.openapi()
    project_root = os.path.dirname(backend_dir)
    docs_dir = os.path.join(project_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    target_path = os.path.join(docs_dir, "openapi.json")

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"OpenAPI specification successfully exported to: {target_path}")
    print(f"Total paths documented: {len(openapi_schema.get('paths', {}))}")


if __name__ == "__main__":
    export_openapi()
