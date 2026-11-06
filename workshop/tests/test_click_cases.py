from pr_review_workshop.click_cases import observe, source_root
from pr_review_workshop.contracts import read_json


def test_pinned_case_metadata():
    manifest = read_json("workshop-manifest.json")
    assert manifest["case_issue"] == 3362 and manifest["case_reporter"] == "Melebius"
    assert len(manifest["source_sha"]) == 40
    assert (source_root() / "LICENSE.txt").is_file()


def test_reproduced_report_on_baseline():
    result = observe("baseline")
    assert not result["hyphen_tokens_intact"]


def test_partial_fix_has_sibling_boundary_failure():
    result = observe("partial")
    assert result["hyphen_tokens_intact"] and not result["long_token_intact"]


def test_repair_and_unchanged_behavior():
    result = observe("repaired")
    assert result["hyphen_tokens_intact"] and result["long_token_intact"]
    assert result["ordinary_text_wraps"] and result["hypothesis_not_production_fix"]
