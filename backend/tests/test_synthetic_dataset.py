from __future__ import annotations

import json
from pathlib import Path

from ml.data.synthetic.dataset_utils import validate_dataset
from ml.data.synthetic.generate_genuine_calls import GENUINE_CALLS
from ml.data.synthetic.generate_scam_calls import SCAM_CALLS, generate

ROOT_DIR = Path(__file__).resolve().parents[2]


def test_dataset_has_balanced_diverse_classes():
    calls = [*SCAM_CALLS, *GENUINE_CALLS]
    validate_dataset(calls)

    assert len(SCAM_CALLS) == 20
    assert len(GENUINE_CALLS) == 20
    assert {call["features"]["recipient_is_new"] for call in SCAM_CALLS} == {
        True,
        False,
    }
    assert {call["features"]["recipient_is_new"] for call in GENUINE_CALLS} == {
        True,
        False,
    }


def test_committed_dataset_is_reproducibly_generated():
    output_path = generate()
    generated = json.loads(output_path.read_text(encoding="utf-8"))
    committed = json.loads(
        (ROOT_DIR / "ml/data/synthetic/labeled_calls.json").read_text(encoding="utf-8")
    )

    assert generated == committed
    assert len({call["id"] for call in generated}) == 40
