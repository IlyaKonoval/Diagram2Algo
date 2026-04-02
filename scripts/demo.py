import json
import sys
from pathlib import Path

from app.llm import warmup
from app.pipeline import process_path

def demo_single_image(image_path: str):
    print(f"\n{'='*60}")
    print("DEMO: Single Image Processing")
    print(f"{'='*60}")
    print(f"Input: {image_path}")

    results = process_path(image_path)

    for result in results:
        print(f"\nDiagram type: {result.diagram_type or 'unknown'}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Steps found: {len(result.steps)}")

        if result.error:
            print(f"Error: {result.error}")
            continue

        print("\nExtracted steps:")
        for step in result.steps:
            actor = step.actor or "?"
            target = step.target or ""
            target_str = f" -> [{target}]" if target else ""
            print(f"  {step.number}. [{actor}] {step.action}{target_str}")

def demo_batch(directory: str, limit: int = 5):
    print(f"\n{'='*60}")
    print("DEMO: Batch Processing")
    print(f"{'='*60}")
    print(f"Directory: {directory}")
    print(f"Limit: {limit} files\n")

    results = process_path(directory)

    total_steps = 0
    successful = 0

    for i, result in enumerate(results[:limit]):
        if not result.error:
            successful += 1
            total_steps += len(result.steps)

        filename = Path(result.source_file).name
        print(f"[{i+1}] {filename}")

        if result.error:
            print(f"    ERROR: {result.error}")
        else:
            print(f"    Type: {result.diagram_type or 'unknown'}")
            print(f"    Steps: {len(result.steps)}")
            if result.steps:
                first_step = result.steps[0]
                print(f"    First: {first_step.action[:50]}...")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Processed: {min(limit, len(results))} files")
    print(f"Successful: {successful}")
    print(f"Total steps extracted: {total_steps}")

def demo_api_example():
    print(f"\n{'='*60}")
    print("DEMO: API Usage Example")
    print(f"{'='*60}")

    print("""
To test the API:

1. Start the server:
   uvicorn main:app --reload

2. Health check:
   curl http://localhost:8000/api/health

3. Extract from image:
   curl -X POST http://localhost:8000/api/extract -F "file=@image.png"

4. Open Swagger UI:
   http://localhost:8000/docs
""")

def main():
    print("=" * 60)
    print("Diagram2Algo Demo")
    print("=" * 60)

    print("\nLoading model (may take a while on first run)...")
    if not warmup():
        print("ERROR: Failed to load model")
        sys.exit(1)
    print("Model ready!\n")

    test_dir = Path("docs")
    test_images = list(test_dir.rglob("*.png"))

    if not test_images:
        print("No test images found!")
        demo_api_example()
        return

    print(f"Found {len(test_images)} images in {test_dir}")

    demo_single_image(str(test_images[0]))

    if len(test_images) > 1:
        demo_batch(str(test_images[0].parent), limit=5)

    demo_api_example()

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
