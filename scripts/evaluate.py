import json
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.config import TEST_DIR, GT_FILE, EVAL_OUTPUT_DIR
from app.metrics import calculate_metrics, warmup_metrics
from app.reporter import Reporter, FileMetrics, EvalReport


console = Console()


def parse_ground_truth(test_file: str) -> dict:
    ground_truth = {}
    current_file = None
    current_steps = []
    current_roles = []

    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        console.print(f"[red]File not found: {test_file}[/red]")
        return {}

    for line in content.split('\n'):
        line = line.strip()

        if not line or line.startswith('Шаг'):
            continue

        if line.endswith('.png') or line.endswith('.jpg'):
            if current_file and current_steps:
                ground_truth[current_file] = {
                    'steps': current_steps,
                    'roles': current_roles
                }
            current_file = line
            current_steps = []
            current_roles = []
            continue

        match = re.match(r'^(\d+)[\.\)]\s*(.+?)(?:\s*\|\s*(.+))?$', line)
        if match:
            step_num = int(match.group(1))
            action = match.group(2).strip()
            role = match.group(3).strip() if match.group(3) else None

            current_steps.append({
                'number': step_num,
                'action': action,
                'role': role
            })
            if role:
                current_roles.append(role)

    if current_file and current_steps:
        ground_truth[current_file] = {
            'steps': current_steps,
            'roles': current_roles
        }

    return ground_truth


def find_result(results: list, filename: str):
    for result in results:
        source = Path(result.get('source_file', '')).name
        if source == filename:
            return result
    return None


def evaluate(results: list, ground_truth: dict, output_dir: str = str(EVAL_OUTPUT_DIR)) -> EvalReport:
    reporter = Reporter(output_dir)
    file_metrics = []

    console.print("[dim]Loading embedding model...[/dim]")
    warmup_metrics()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Evaluating...", total=len(ground_truth))

        for filename, gt_data in ground_truth.items():
            gt_steps = gt_data['steps']
            result = find_result(results, filename)

            if result:
                extracted = result.get('steps', [])
                metrics = calculate_metrics(extracted, gt_steps)

                file_metrics.append(FileMetrics(
                    filename=filename,
                    gt_count=len(gt_steps),
                    extracted_count=len(extracted),
                    metrics=metrics,
                    gt_steps=gt_steps,
                    extracted_steps=extracted
                ))
            else:
                metrics = calculate_metrics([], gt_steps)
                file_metrics.append(FileMetrics(
                    filename=filename,
                    gt_count=len(gt_steps),
                    extracted_count=0,
                    metrics=metrics,
                    gt_steps=gt_steps,
                    extracted_steps=[]
                ))

            progress.advance(task)

    report = reporter.generate_report(file_metrics)
    reporter.print_console(report)
    reporter.save_all(report)

    return report


def run_full_evaluation(test_dir: str = str(TEST_DIR), gt_file: str = str(GT_FILE)):
    from app.llm import warmup
    from app.pipeline import process_path

    console.print("[bold cyan]Loading LLM model...[/bold cyan]")
    warmup()

    console.print(f"\n[bold cyan]Processing {test_dir}...[/bold cyan]")
    results = process_path(test_dir)
    results_data = [r.model_dump() for r in results]

    gt = parse_ground_truth(gt_file)
    return evaluate(results_data, gt)


def evaluate_from_file(results_file: str, gt_file: str = str(GT_FILE)):
    with open(results_file, encoding='utf-8') as f:
        data = json.load(f)

    results = data.get('results', data) if isinstance(data, dict) else data
    gt = parse_ground_truth(gt_file)

    return evaluate(results, gt)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        if sys.argv[1] == '--run':
            run_full_evaluation()
        else:
            gt = sys.argv[2] if len(sys.argv) >= 3 else str(GT_FILE)
            evaluate_from_file(sys.argv[1], gt)
    else:
        console.print("[bold]Usage:[/bold]")
        console.print("  python evaluate.py --run                    Run extraction + evaluation")
        console.print("  python evaluate.py results.json             Evaluate existing results")
        console.print("  python evaluate.py results.json gt.txt      Custom ground truth file")
