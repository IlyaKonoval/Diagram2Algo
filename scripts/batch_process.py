import json
import logging
import sys
from pathlib import Path

import click
from tqdm import tqdm

from app.models import BatchResult
from app.pipeline import process_path
from app.llm import warmup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--input-dir",
    "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Input directory with diagram files",
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    default="results.json",
    help="Output JSON file",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "jsonl", "csv"]),
    default="json",
    help="Output format",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
def main(input_dir: Path, output_file: Path, format: str, verbose: bool):
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    click.echo("Loading model...")
    if not warmup():
        click.echo("Warning: Model warmup failed", err=True)

    click.echo(f"Processing files in {input_dir}...")

    all_results = []
    files = list(input_dir.rglob("*"))
    files = [f for f in files if f.is_file()]

    with tqdm(total=len(files), desc="Processing") as pbar:
        for file_path in files:
            try:
                results = process_path(file_path)
                all_results.extend(results)

                success_count = len([r for r in results if not r.error])
                if verbose:
                    click.echo(f"  {file_path.name}: {success_count} extractions")

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")

            pbar.update(1)

    successful = len([r for r in all_results if not r.error])
    failed = len([r for r in all_results if r.error])

    batch_result = BatchResult(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=all_results,
    )

    if format == "json":
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(batch_result.model_dump(), f, indent=2, ensure_ascii=False)

    elif format == "jsonl":
        with open(output_file, "w", encoding="utf-8") as f:
            for result in all_results:
                f.write(json.dumps(result.model_dump(), ensure_ascii=False) + "\n")

    elif format == "csv":
        import csv
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "source_file", "page_or_slide", "diagram_type",
                "step_number", "actor", "action", "target", "note",
                "confidence", "error"
            ])

            for result in all_results:
                if result.steps:
                    for step in result.steps:
                        writer.writerow([
                            result.source_file,
                            result.page_or_slide or "",
                            result.diagram_type or "",
                            step.number,
                            step.actor or "",
                            step.action,
                            step.target or "",
                            step.note or "",
                            result.confidence,
                            result.error or "",
                        ])
                else:
                    writer.writerow([
                        result.source_file,
                        result.page_or_slide or "",
                        result.diagram_type or "",
                        "", "", "", "", "",
                        result.confidence,
                        result.error or "",
                    ])

    click.echo(f"\nResults saved to {output_file}")
    click.echo(f"Total: {len(files)} files, {successful} successful, {failed} failed")
    click.echo(f"Total steps extracted: {sum(len(r.steps) for r in all_results)}")


if __name__ == "__main__":
    main()
