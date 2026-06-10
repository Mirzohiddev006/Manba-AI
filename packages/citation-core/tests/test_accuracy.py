"""Etalon to'plamda aniqlik o'lchovi — CI sifat darvozasi.

Hisobot: har tur bo'yicha aniqlik + umumiy. Umumiy aniqlik
--accuracy-threshold (standart 0.97) dan past bo'lsa — test yiqiladi.
"""

from __future__ import annotations

from collections import defaultdict

from citation_core import Pipeline, SourceType


def test_etalon_accuracy(etalon_pairs: list[dict], accuracy_threshold: float) -> None:
    pipe = Pipeline()  # LLM siz — sof qoidaviy rejim o'lchanadi
    by_type: dict[str, list[bool]] = defaultdict(list)
    failures: list[str] = []

    for pair in etalon_pairs:
        result = pipe.parse_one(pair["input"])
        ok = result.formatted_text == pair["expected"]
        type_ok = result.source_type == SourceType(pair["type"])
        by_type[pair["type"]].append(ok and type_ok)
        if not (ok and type_ok):
            failures.append(
                f"\n[{pair['type']}] kirish : {pair['input'][:90]}"
                f"\n  kutilgan: {pair['expected'][:90]}"
                f"\n  olingan : {result.formatted_text[:90]}"
                f"\n  tur     : {result.source_type} (kutilgan {pair['type']})"
            )

    total = sum(len(v) for v in by_type.values())
    correct = sum(sum(v) for v in by_type.values())
    accuracy = correct / total if total else 0.0

    print("\n========== ANIQLIK HISOBOTI (qoidaviy rejim) ==========")
    for stype, results in sorted(by_type.items()):
        acc = sum(results) / len(results)
        print(f"  {stype:18s} {sum(results):3d}/{len(results):3d}  {acc:6.1%}")
    print(f"  {'JAMI':18s} {correct:3d}/{total:3d}  {accuracy:6.1%}")
    print("=======================================================")

    assert accuracy >= accuracy_threshold, (
        f"Aniqlik {accuracy:.1%} < eshik {accuracy_threshold:.0%}."
        + "".join(failures[:10])
    )


def test_type_detection(etalon_pairs: list[dict]) -> None:
    """Tur aniqlash alohida o'lchanadi (formatdan mustaqil)."""
    pipe = Pipeline()
    wrong = []
    for pair in etalon_pairs:
        result = pipe.parse_one(pair["input"])
        if result.source_type != SourceType(pair["type"]):
            wrong.append(f"{pair['input'][:60]} → {result.source_type} != {pair['type']}")
    assert not wrong, "Tur xatolari:\n" + "\n".join(wrong)
