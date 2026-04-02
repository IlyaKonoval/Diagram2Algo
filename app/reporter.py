import csv
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from app.config import EVAL_OUTPUT_DIR
from app.metrics import MetricsResult


@dataclass
class FileMetrics:
    filename: str
    gt_count: int
    extracted_count: int
    metrics: MetricsResult
    gt_steps: list = field(default_factory=list)
    extracted_steps: list = field(default_factory=list)


@dataclass
class EvalReport:
    timestamp: str
    total_files: int
    evaluated_files: int
    total_gt_steps: int
    total_extracted: int
    avg_semantic_f1: float
    avg_sequence_score: float
    avg_role_accuracy: float
    avg_count_accuracy: float
    avg_composite: float
    file_metrics: list[FileMetrics] = field(default_factory=list)


class Reporter:

    def __init__(self, output_dir: str = str(EVAL_OUTPUT_DIR)):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.console = Console()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_report(self, file_metrics: list[FileMetrics]) -> EvalReport:
        evaluated = [m for m in file_metrics if m.extracted_count > 0 or m.gt_count > 0]

        total_gt = sum(m.gt_count for m in file_metrics)
        total_ex = sum(m.extracted_count for m in file_metrics)

        if evaluated:
            avg_semantic_f1 = sum(m.metrics.semantic_f1 for m in evaluated) / len(evaluated)
            avg_sequence = sum(
                (m.metrics.sequence_lcs + m.metrics.sequence_edit_distance) / 2
                for m in evaluated
            ) / len(evaluated)
            avg_role = sum(m.metrics.role_accuracy for m in evaluated) / len(evaluated)
            avg_count = sum(m.metrics.step_count_accuracy for m in evaluated) / len(evaluated)
            avg_composite = sum(m.metrics.composite_score for m in evaluated) / len(evaluated)
        else:
            avg_semantic_f1 = avg_sequence = avg_role = avg_count = avg_composite = 0

        return EvalReport(
            timestamp=self.timestamp,
            total_files=len(file_metrics),
            evaluated_files=len(evaluated),
            total_gt_steps=total_gt,
            total_extracted=total_ex,
            avg_semantic_f1=avg_semantic_f1,
            avg_sequence_score=avg_sequence,
            avg_role_accuracy=avg_role,
            avg_count_accuracy=avg_count,
            avg_composite=avg_composite,
            file_metrics=file_metrics
        )

    def print_console(self, report: EvalReport):
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]Diagram2Algo Evaluation Report[/bold cyan]\n"
            f"[dim]{report.timestamp}[/dim]",
            border_style="cyan"
        ))

        table = Table(
            title="Per-File Results",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )

        table.add_column("File", style="cyan", width=15)
        table.add_column("GT", justify="right", style="yellow", width=4)
        table.add_column("Ex", justify="right", style="yellow", width=4)
        table.add_column("Sem F1", justify="right", width=7)
        table.add_column("Seq", justify="right", width=6)
        table.add_column("Role", justify="right", width=6)
        table.add_column("Score", justify="right", width=7)

        for m in report.file_metrics:
            score = m.metrics.composite_score
            score_style = "green" if score >= 0.7 else "yellow" if score >= 0.4 else "red"
            seq_score = (m.metrics.sequence_lcs + m.metrics.sequence_edit_distance) / 2

            table.add_row(
                m.filename[:15],
                str(m.gt_count),
                str(m.extracted_count),
                f"{m.metrics.semantic_f1:.2f}",
                f"{seq_score:.2f}",
                f"{m.metrics.role_accuracy:.2f}",
                f"[{score_style}]{score:.2f}[/{score_style}]"
            )

        self.console.print(table)

        score_style = "green" if report.avg_composite >= 0.7 else "yellow" if report.avg_composite >= 0.4 else "red"

        summary_text = (
            f"[bold]Files:[/bold] {report.evaluated_files}/{report.total_files}  "
            f"[bold]GT:[/bold] {report.total_gt_steps}  "
            f"[bold]Extracted:[/bold] {report.total_extracted}\n\n"
            f"[bold]Semantic F1:[/bold] {report.avg_semantic_f1:.2f}  "
            f"[bold]Sequence:[/bold] {report.avg_sequence_score:.2f}  "
            f"[bold]Role:[/bold] {report.avg_role_accuracy:.2f}  "
            f"[bold]Count:[/bold] {report.avg_count_accuracy:.2f}\n\n"
            f"[bold {score_style}]Composite Score: {report.avg_composite:.2f}[/bold {score_style}]"
        )

        self.console.print(Panel(
            summary_text,
            title="Summary",
            border_style=score_style
        ))

        self.console.print("\n[dim]Score = 0.4*Semantic_F1 + 0.3*Sequence + 0.2*Role + 0.1*Count[/dim]")

    def save_csv(self, report: EvalReport) -> Path:
        csv_path = self.output_dir / f"eval_{self.timestamp}.csv"

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'filename', 'gt_count', 'extracted_count',
                'semantic_precision', 'semantic_recall', 'semantic_f1',
                'sequence_lcs', 'sequence_edit', 'role_accuracy',
                'step_count_accuracy', 'composite_score'
            ])

            for m in report.file_metrics:
                writer.writerow([
                    m.filename,
                    m.gt_count,
                    m.extracted_count,
                    round(m.metrics.semantic_precision, 4),
                    round(m.metrics.semantic_recall, 4),
                    round(m.metrics.semantic_f1, 4),
                    round(m.metrics.sequence_lcs, 4),
                    round(m.metrics.sequence_edit_distance, 4),
                    round(m.metrics.role_accuracy, 4),
                    round(m.metrics.step_count_accuracy, 4),
                    round(m.metrics.composite_score, 4)
                ])

        self.console.print(f"[dim]CSV saved:[/dim] {csv_path}")
        return csv_path

    def save_detailed_json(self, report: EvalReport) -> Path:
        json_path = self.output_dir / f"eval_{self.timestamp}_detailed.json"

        data = {
            'timestamp': report.timestamp,
            'summary': {
                'total_files': report.total_files,
                'evaluated_files': report.evaluated_files,
                'total_gt_steps': report.total_gt_steps,
                'total_extracted': report.total_extracted,
                'avg_semantic_f1': report.avg_semantic_f1,
                'avg_sequence_score': report.avg_sequence_score,
                'avg_role_accuracy': report.avg_role_accuracy,
                'avg_count_accuracy': report.avg_count_accuracy,
                'avg_composite_score': report.avg_composite
            },
            'files': []
        }

        for m in report.file_metrics:
            data['files'].append({
                'filename': m.filename,
                'metrics': {
                    'gt_count': m.gt_count,
                    'extracted_count': m.extracted_count,
                    'semantic_precision': m.metrics.semantic_precision,
                    'semantic_recall': m.metrics.semantic_recall,
                    'semantic_f1': m.metrics.semantic_f1,
                    'sequence_lcs': m.metrics.sequence_lcs,
                    'sequence_edit_distance': m.metrics.sequence_edit_distance,
                    'role_accuracy': m.metrics.role_accuracy,
                    'step_count_accuracy': m.metrics.step_count_accuracy,
                    'composite_score': m.metrics.composite_score
                },
                'matched_pairs': [
                    {'extracted_idx': ex, 'gt_idx': gt, 'similarity': round(sim, 3)}
                    for ex, gt, sim in m.metrics.matched_pairs
                ],
                'gt_steps': m.gt_steps,
                'extracted_steps': m.extracted_steps
            })

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.console.print(f"[dim]Detailed JSON saved:[/dim] {json_path}")
        return json_path

    def save_html(self, report: EvalReport) -> Path:
        html_path = self.output_dir / f"eval_{self.timestamp}.html"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Diagram2Algo Evaluation - {report.timestamp}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 1400px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #eee; }}
        h1 {{ color: #00d4ff; }}
        h2 {{ color: #00d4ff; margin-top: 40px; }}
        .summary {{ background: #16213e; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-top: 15px; }}
        .metric-box {{ background: #0f3460; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 28px; font-weight: bold; }}
        .metric-label {{ font-size: 12px; color: #888; margin-top: 5px; }}
        .good {{ color: #00ff88; }}
        .mid {{ color: #ffaa00; }}
        .bad {{ color: #ff4444; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
        th {{ background: #0f3460; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #333; }}
        tr:hover {{ background: #1f4068; }}
        .comparison {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px; }}
        .col {{ background: #16213e; padding: 15px; border-radius: 8px; }}
        .col h3 {{ margin-top: 0; color: #00d4ff; font-size: 14px; }}
        .step {{ padding: 8px; margin: 5px 0; background: #0f3460; border-radius: 4px; font-size: 13px; }}
        .matched {{ border-left: 3px solid #00ff88; }}
        .unmatched {{ border-left: 3px solid #ff4444; opacity: 0.7; }}
        details {{ margin-bottom: 10px; }}
        summary {{ cursor: pointer; padding: 12px; background: #16213e; border-radius: 4px; }}
        summary:hover {{ background: #1f4068; }}
        .formula {{ background: #0f3460; padding: 15px; border-radius: 8px; font-family: monospace; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>Diagram2Algo Evaluation Report</h1>
    <p style="color: #888;">{report.timestamp}</p>

    <div class="summary">
        <div>Files: <b>{report.evaluated_files}/{report.total_files}</b> |
             GT Steps: <b>{report.total_gt_steps}</b> |
             Extracted: <b>{report.total_extracted}</b></div>

        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-value {'good' if report.avg_semantic_f1 >= 0.7 else 'mid' if report.avg_semantic_f1 >= 0.4 else 'bad'}">{report.avg_semantic_f1:.2f}</div>
                <div class="metric-label">Semantic F1</div>
            </div>
            <div class="metric-box">
                <div class="metric-value {'good' if report.avg_sequence_score >= 0.7 else 'mid' if report.avg_sequence_score >= 0.4 else 'bad'}">{report.avg_sequence_score:.2f}</div>
                <div class="metric-label">Sequence</div>
            </div>
            <div class="metric-box">
                <div class="metric-value {'good' if report.avg_role_accuracy >= 0.7 else 'mid' if report.avg_role_accuracy >= 0.4 else 'bad'}">{report.avg_role_accuracy:.2f}</div>
                <div class="metric-label">Role Accuracy</div>
            </div>
            <div class="metric-box">
                <div class="metric-value {'good' if report.avg_count_accuracy >= 0.7 else 'mid' if report.avg_count_accuracy >= 0.4 else 'bad'}">{report.avg_count_accuracy:.2f}</div>
                <div class="metric-label">Count Accuracy</div>
            </div>
            <div class="metric-box">
                <div class="metric-value {'good' if report.avg_composite >= 0.7 else 'mid' if report.avg_composite >= 0.4 else 'bad'}">{report.avg_composite:.2f}</div>
                <div class="metric-label">Composite Score</div>
            </div>
        </div>

        <div class="formula">
            Score = 0.4 * Semantic_F1 + 0.3 * Sequence + 0.2 * Role + 0.1 * Count
        </div>
    </div>

    <h2>Per-File Results</h2>
    <table>
        <tr>
            <th>File</th>
            <th>GT</th>
            <th>Ex</th>
            <th>Semantic F1</th>
            <th>Sequence</th>
            <th>Role</th>
            <th>Count</th>
            <th>Score</th>
        </tr>
"""

        for m in report.file_metrics:
            score = m.metrics.composite_score
            score_class = 'good' if score >= 0.7 else 'mid' if score >= 0.4 else 'bad'
            seq_score = (m.metrics.sequence_lcs + m.metrics.sequence_edit_distance) / 2

            html += f"""        <tr>
            <td>{m.filename}</td>
            <td>{m.gt_count}</td>
            <td>{m.extracted_count}</td>
            <td>{m.metrics.semantic_f1:.2f}</td>
            <td>{seq_score:.2f}</td>
            <td>{m.metrics.role_accuracy:.2f}</td>
            <td>{m.metrics.step_count_accuracy:.2f}</td>
            <td class="{score_class}">{score:.2f}</td>
        </tr>\n"""

        html += """    </table>

    <h2>Detailed Comparison</h2>
"""

        for m in report.file_metrics:
            matched_gt = {gt_idx for _, gt_idx, _ in m.metrics.matched_pairs}
            matched_ex = {ex_idx for ex_idx, _, _ in m.metrics.matched_pairs}

            seq_score = (m.metrics.sequence_lcs + m.metrics.sequence_edit_distance) / 2
            html += f"""    <details>
        <summary>
            <b>{m.filename}</b> —
            Score: {m.metrics.composite_score:.2f} |
            Semantic F1: {m.metrics.semantic_f1:.2f} |
            Sequence: {seq_score:.2f} |
            Matched: {len(m.metrics.matched_pairs)}/{m.gt_count}
        </summary>
        <div class="comparison">
            <div class="col">
                <h3>Ground Truth ({m.gt_count} steps)</h3>
"""
            for i, step in enumerate(m.gt_steps):
                action = step.get('action', 'N/A')
                role = step.get('role', '')
                role_str = f" [{role}]" if role else ""
                matched_class = "matched" if i in matched_gt else "unmatched"
                html += f'                <div class="step {matched_class}">{step.get("number", i+1)}. {action}{role_str}</div>\n'

            html += """            </div>
            <div class="col">
                <h3>Extracted ({ex_count} steps)</h3>
""".replace('{ex_count}', str(m.extracted_count))

            for i, step in enumerate(m.extracted_steps):
                action = step.get('action', 'N/A')
                actor = step.get('actor', step.get('role', ''))
                actor_str = f" [{actor}]" if actor else ""
                matched_class = "matched" if i in matched_ex else "unmatched"
                html += f'                <div class="step {matched_class}">{step.get("number", i+1)}. {action}{actor_str}</div>\n'

            html += """            </div>
        </div>
    </details>
"""

        html += """
    <h2>Metrics Explanation</h2>
    <div class="summary">
        <p><b>Semantic F1:</b> Uses sentence embeddings to match steps by meaning, not exact text. Handles synonyms, translations, paraphrases.</p>
        <p><b>Sequence:</b> Average of LCS ratio and edit distance. Measures if steps are in correct order.</p>
        <p><b>Role Accuracy:</b> For matched steps, what percentage have the correct actor/role.</p>
        <p><b>Count Accuracy:</b> How close the extracted step count is to ground truth.</p>
    </div>
</body>
</html>"""

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        self.console.print(f"[dim]HTML report saved:[/dim] {html_path}")
        return html_path

    def save_all(self, report: EvalReport) -> dict[str, Path]:
        return {
            'csv': self.save_csv(report),
            'json': self.save_detailed_json(report),
            'html': self.save_html(report)
        }
