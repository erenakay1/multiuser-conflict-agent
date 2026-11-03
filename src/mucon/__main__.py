"""mucon CLI. Kullanım: `uv run python -m mucon --help`."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    help="Eşit yetkili çok kullanıcılı LLM agent'larında talimat çakışması deneyleri.",
    no_args_is_help=True,
)

ConfigOpt = Annotated[Path, typer.Option("--config", "-c", help="Deney config dosyası")]


@app.command()
def generate(
    n: Annotated[int, typer.Option("--n", help="Üretilecek senaryo sayısı")] = 50,
    out: Annotated[Path, typer.Option("--out", help="Çıktı klasörü")] = Path("data/scenarios"),
    seed: Annotated[int | None, typer.Option(help="Seed (boşsa config'ten)")] = None,
) -> None:
    """Senaryo üret."""
    # TODO(H3): ScenarioGenerator bağlantısı
    raise NotImplementedError


@app.command("detect-eval")
def detect_eval(config: ConfigOpt = Path("configs/experiments/example.yaml")) -> None:
    """Çakışma dedektörlerini etiketli veride değerlendir (P/R/F1)."""
    # TODO(H5): dedektör değerlendirmesi
    raise NotImplementedError


@app.command()
def run(
    config: ConfigOpt = Path("configs/experiments/example.yaml"),
    yes: Annotated[bool, typer.Option("--yes", help="Maliyet onayını atla")] = False,
) -> None:
    """Strateji × dedektör × senaryo deneyini koş."""
    # TODO(H7): runner.run_experiment bağlantısı (önce estimate_cost + onay)
    raise NotImplementedError


@app.command()
def analyze(
    results_dir: Annotated[Path, typer.Argument(help="results/<tarih>_<deney>/ klasörü")],
) -> None:
    """Sonuçları özetle: metrikler, Wilcoxon, grafikler."""
    # TODO(H8): analiz
    raise NotImplementedError


if __name__ == "__main__":
    app()
