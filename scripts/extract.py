import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from app.config import TEST_DIR
from app.llm import warmup
from app.pipeline import process_image
from app.preprocessing import preprocess_image
from PIL import Image


console = Console()


def format_result(result) -> None:
    console.print()
    title = f"[bold cyan]{result.source_file}[/bold cyan]"
    if result.diagram_type:
        title += f"  [dim]({result.diagram_type})[/dim]"

    console.print(Panel(title, box=box.ROUNDED))

    if result.error:
        console.print(f"[red]Ошибка: {result.error}[/red]")
        return

    if not result.steps:
        console.print("[yellow]Шаги не найдены[/yellow]")
        return

    console.print("\n[bold]Алгоритм:[/bold]\n")

    for step in result.steps:
        num = step.number or "•"
        action = step.action or "—"

        line = f"  [cyan]{num}.[/cyan] "

        if step.actor:
            line += f"[yellow]{step.actor}[/yellow]: "

        line += f"{action}"

        if step.target and step.target != step.actor:
            line += f" [dim]→ {step.target}[/dim]"

        console.print(line)

        if step.note and step.note != step.action:
            console.print(f"      [dim italic]({step.note})[/dim italic]")

    console.print(f"\n[dim]Всего шагов: {len(result.steps)}[/dim]")
    if result.confidence:
        conf_color = "green" if result.confidence >= 0.7 else "yellow" if result.confidence >= 0.4 else "red"
        console.print(f"[dim]Уверенность: [{conf_color}]{result.confidence:.0%}[/{conf_color}][/dim]")


def extract_and_show(image_path: str) -> None:
    path = Path(image_path)
    if not path.exists():
        console.print(f"[red]Файл не найден: {image_path}[/red]")
        return

    console.print("[dim]Загрузка модели...[/dim]")
    warmup()

    console.print(f"[dim]Обработка {path.name}...[/dim]")

    image = Image.open(path)
    processed = preprocess_image(image)
    result = process_image(processed, str(path))

    format_result(result)


def main():
    if len(sys.argv) < 2:
        console.print("[bold]Использование:[/bold]")
        console.print("  python extract.py <image.png>")
        console.print("\n[bold]Пример:[/bold]")
        console.print(f'  python extract.py "{TEST_DIR / "149.png"}"')
        return

    extract_and_show(sys.argv[1])


if __name__ == "__main__":
    main()
