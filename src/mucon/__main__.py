"""mucon CLI. Kullanım: `uv run python -m mucon --help`."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from mucon.config import DEFAULT_CONFIG_PATH, PROJECT_ROOT, AppConfig, load_config
from mucon.env.event_planning import VenueDB, generate_mock_venues, planning_window

app = typer.Typer(
    help="Eşit yetkili çok kullanıcılı LLM agent'larında talimat çakışması deneyleri.",
    no_args_is_help=True,
)

ConfigOpt = Annotated[Path, typer.Option("--config", "-c", help="Deney config dosyası")]
AppConfigOpt = Annotated[
    Path, typer.Option("--app-config", help="Proje config dosyası (configs/default.yaml)")
]


def _abs(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _venue_db(cfg: AppConfig, *, create: bool) -> VenueDB:
    """Mekan veritabanını yükler; yoksa ve `create` ise config seed'i ile üretip kaydeder."""
    path = _abs(cfg.paths.venue_db)
    if path.exists():
        return VenueDB.from_json(path)
    if not create:
        raise typer.BadParameter(f"{path} yok; önce `mucon generate` çalıştırın")
    g = cfg.generation
    db = VenueDB(
        generate_mock_venues(
            g.n_venues, cfg.seed, window_start=g.window_start, window_days=g.window_days
        )
    )
    db.to_json(path)
    typer.echo(f"{len(db.venues)} mekan üretildi → {path}")
    return db


@app.command()
def generate(
    n: Annotated[int, typer.Option("--n", help="Üretilecek senaryo sayısı")] = 50,
    out: Annotated[Path | None, typer.Option("--out", help="Çıktı klasörü")] = None,
    seed: Annotated[int | None, typer.Option(help="Seed (boşsa config'ten)")] = None,
    app_config: AppConfigOpt = DEFAULT_CONFIG_PATH,
) -> None:
    """Senaryo üret (mekan veritabanı yoksa önce onu üretir)."""
    from mucon.sim.scenario_generator import ScenarioGenerator

    cfg = load_config(app_config)
    g = cfg.generation
    gen = ScenarioGenerator(
        cfg.seed if seed is None else seed,
        db=_venue_db(cfg, create=True),
        n_users_range=(g.n_users_min, g.n_users_max),
        conflict_rate=g.conflict_rate,
        near_miss_rate=g.near_miss_rate,
        dates=planning_window(g.window_start, g.window_days),
    )
    out_dir = _abs(out or cfg.paths.scenarios_dir)
    paths = gen.save(gen.generate(n), out_dir)
    typer.echo(f"{len(paths)} senaryo → {out_dir}")


@app.command()
def label(
    annotator: Annotated[str, typer.Option("--annotator", "-a", help="ör. yusuf, eren")],
    n: Annotated[int, typer.Option("--n", help="Etiketlenecek senaryo sayısı (baştan)")] = 50,
    scenarios_dir: Annotated[Path | None, typer.Option("--scenarios")] = None,
    app_config: AppConfigOpt = DEFAULT_CONFIG_PATH,
) -> None:
    """Senaryoları terminalde etiketle → data/labels/<annotator>.jsonl (kaldığı yerden devam).

    Üretecin etiketleri gösterilmez. Girdi: "1-3 direct, 2-5 ind" | boş = çakışma yok |
    "?" = yardım | "q" = çık. İsteğe bağlı not: girdinin sonuna " # not" ekleyin.
    """
    from mucon.eval.agreement import (
        append_labels,
        labels_for_scenario,
        load_labels,
        parse_annotation,
    )
    from mucon.sim.scenario_generator import ScenarioGenerator

    cfg = load_config(app_config)
    if annotator == "generator":
        raise typer.BadParameter("'generator' üretecin ayrılmış etiketleyici adıdır")
    scenarios = ScenarioGenerator.load(_abs(scenarios_dir or cfg.paths.scenarios_dir))[:n]
    out = _abs(cfg.paths.labels_dir) / f"{annotator}.jsonl"
    done = {lb.scenario_id for lb in load_labels(out)}
    todo = [sc for sc in scenarios if sc.id not in done]
    typer.echo(f"{len(done)} senaryo zaten etiketli, {len(todo)} kaldı → {out}")
    help_text = (
        "Çakışan mesaj çiftlerini yazın: '1-3 direct, 2-5 range'. Türler: direct, range, "
        "indirect, revision (önek yeterli: dir, ra, ind, rev). Boş = çakışma yok. q = çık."
    )
    for k, sc in enumerate(todo, start=1):
        names = {p.user.id: p.user.name for p in sc.personas}
        msgs = sc.user_messages()
        typer.echo(f"\n[{k}/{len(todo)}] {sc.id}")
        for i, m in enumerate(msgs, start=1):
            typer.echo(f"  {i}. {names.get(m.user_id or '', '?'):<7} {m.text}")
        while True:
            raw = typer.prompt("çakışmalar", default="", show_default=False).strip()
            if raw == "q":
                return
            if raw == "?":
                typer.echo(help_text)
                continue
            text, _, notes = raw.partition("#")
            try:
                conflicts = parse_annotation(text, len(msgs))
            except ValueError as e:
                typer.echo(f"  hata: {e}")
                continue
            append_labels(out, labels_for_scenario(sc, conflicts, annotator, notes.strip()))
            break
    typer.echo("Bitti.")


@app.command("agreement")
def agreement_cmd(
    a: Annotated[str, typer.Argument(help="Etiketleyici A (ör. yusuf)")],
    b: Annotated[str, typer.Argument(help="Etiketleyici B (ör. eren veya generator)")],
    app_config: AppConfigOpt = DEFAULT_CONFIG_PATH,
    show: Annotated[int, typer.Option(help="Gösterilecek uyuşmazlık sayısı")] = 20,
) -> None:
    """İki etiketleyici arasındaki uyum (Cohen's κ). 'generator' = üretecin altın etiketleri."""
    from mucon.eval.agreement import agreement, load_labels
    from mucon.schemas import ConflictLabel
    from mucon.sim.scenario_generator import ScenarioGenerator

    cfg = load_config(app_config)

    def labels_of(name: str) -> list[ConflictLabel]:
        if name == "generator":
            scs = ScenarioGenerator.load(_abs(cfg.paths.scenarios_dir))
            return [lb for sc in scs for lb in sc.gold_labels]
        path = _abs(cfg.paths.labels_dir) / f"{name}.jsonl"
        if not path.exists():
            raise typer.BadParameter(f"{path} yok")
        return load_labels(path)

    rep = agreement(labels_of(a), labels_of(b))
    typer.echo(
        f"{rep.n_scenarios} senaryo, {rep.n_pairs} mesaj çifti | "
        f"çakışma sayısı {a}={rep.n_conflicts_a}, {b}={rep.n_conflicts_b}\n"
        f"ikili (var/yok): uyum={rep.binary_accuracy:.3f}  κ={rep.binary_kappa:.3f}\n"
        f"tür (5 sınıf):   uyum={rep.type_accuracy:.3f}  κ={rep.type_kappa:.3f}"
    )
    for d in rep.disagreements[:show]:
        typer.echo(f"  {d.scenario_id} {'-'.join(d.message_ids)}: {a}={d.a} {b}={d.b}")


@app.command("extract-eval")
def extract_eval(
    n: Annotated[int, typer.Option("--n", help="Değerlendirilecek senaryo sayısı")] = 50,
    experiment: Annotated[
        bool, typer.Option("--experiment", help="EXPERIMENT_MODEL (API) kullan")
    ] = False,
    yes: Annotated[bool, typer.Option("--yes", help="API maliyet onayını atla")] = False,
    app_config: AppConfigOpt = DEFAULT_CONFIG_PATH,
) -> None:
    """Kısıt çıkarıcıyı senaryoların altın kısıtlarına karşı değerlendir (P/R)."""
    from mucon.extract.constraint_extractor import ConstraintExtractor, score_extraction
    from mucon.llm.client import LLMClient
    from mucon.schemas import Session
    from mucon.sim.scenario_generator import ScenarioGenerator

    cfg = load_config(app_config)
    scenarios = ScenarioGenerator.load(_abs(cfg.paths.scenarios_dir))[:n]
    n_msgs = sum(len(sc.user_messages()) for sc in scenarios)
    llm = LLMClient.from_config(cfg, experiment=experiment)
    if llm.provider != "ollama" and not yes:
        typer.confirm(
            f"{llm.provider}/{llm.model} ile ~{n_msgs} çağrı (~{n_msgs * 900} token) yapılacak. "
            "Devam?",
            abort=True,
        )
    g = cfg.generation
    extractor = ConstraintExtractor(
        llm, dates=planning_window(g.window_start, g.window_days), seed=cfg.seed
    )

    gold, pred, rows, n_err = [], [], [], 0
    for k, sc in enumerate(scenarios, start=1):
        session = Session(id=f"x-{sc.id}", scenario_id=sc.id, users=[p.user for p in sc.personas])
        for m in sc.user_messages():
            out = extractor.extract_safe(m, session)
            n_err += out is None
            got = out or []
            exp_ = [c for c in sc.gold_constraints if c.source_message_id == m.id]
            gold += exp_
            pred += got
            rows.append(
                {
                    "scenario_id": sc.id,
                    "message_id": m.id,
                    "text": m.text,
                    "gold": [c.model_dump(mode="json") for c in exp_],
                    "pred": None if out is None else [c.model_dump(mode="json") for c in got],
                }
            )
        typer.echo(f"  [{k}/{len(scenarios)}] {sc.id}")

    score = score_extraction(gold, pred, n_messages=n_msgs, n_errors=n_err)
    run_dir = _abs(cfg.paths.results_dir) / f"{date.today().isoformat()}_extract-v0-{llm.model}"
    run_dir = run_dir.with_name(run_dir.name.replace(":", "-").replace("/", "-"))
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(app_config, run_dir / "config.yaml")
    (run_dir / "predictions.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    summary = {
        "model": llm.model,
        "provider": str(llm.provider),
        "n_scenarios": len(scenarios),
        "n_calls": llm.n_calls,
        "usage": llm.total_usage.model_dump(),
        **score.model_dump(),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    typer.echo(json.dumps(summary, indent=2))
    typer.echo(f"→ {run_dir}")


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
