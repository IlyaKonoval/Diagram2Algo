import sys
import time
from pathlib import Path

from PIL import Image

from app.config import settings, DOCS_DIR
from app.llm import get_provider, warmup
from app.preprocessing import preprocess_image
from app.prompts import IMAGE_PROMPT_EN
from app.postprocessing import parse_llm_response


def main():
    print("=" * 60)
    print("Diagram2Algo Model Test")
    print("=" * 60)

    provider = get_provider()
    print(f"\nProvider: {provider.name}")
    print(f"Model: {provider.model_id}")

    print("\n[1/3] Warming up...")
    start = time.time()
    if not warmup():
        print("ERROR: Warmup failed")
        sys.exit(1)
    print(f"Ready in {time.time() - start:.1f}s")

    test_images = list(DOCS_DIR.rglob("*.png"))[:3]
    if not test_images:
        print(f"No test images found in {DOCS_DIR}")
        return

    for i, image_path in enumerate(test_images):
        print(f"\n[{i + 2}/3] Processing: {image_path.name}")
        try:
            image = Image.open(image_path)
            print(f"  Original size: {image.size}")

            processed = preprocess_image(image)
            print(f"  Processed size: {processed.size}")

            print("  Running inference...")
            start = time.time()
            response = provider.image_inference(processed, IMAGE_PROMPT_EN)
            elapsed = time.time() - start

            result = parse_llm_response(response, str(image_path))

            print(f"  Diagram type: {result.diagram_type or 'unknown'}")
            print(f"  Steps found: {len(result.steps)}")
            print(f"  Inference time: {elapsed:.1f}s")

            if result.steps:
                for step in result.steps[:3]:
                    actor = step.actor or "?"
                    print(f"    {step.number}. [{actor}] {step.action}")

        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
