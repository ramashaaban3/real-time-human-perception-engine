import json
import csv
import time
from pathlib import Path
from unittest import case
import requests

ORCHESTRATOR_URL = "http://localhost:8000/v1/pipeline/run"
RESET_URL = "http://localhost:8002/v1/reasoning/reset"

TEST_CASES_PATH = Path("tests/test_cases.json")
RESULTS_CSV_PATH = Path("tests/results.csv")
SUMMARY_TXT_PATH = Path("tests/summary.txt")

REPEAT_PER_TEST = 3


def normalize_position(value):
    if value in ["left", "center", "right"]:
        return value
    return None


def is_false_trigger(expected_action, actual_action):
    return expected_action == "NO_ACTION" and actual_action != "NO_ACTION"


def send_image(image_path):
    with open(image_path, "rb") as f:
        files = {"image": (image_path.name, f, "image/jpeg")}
        start = time.perf_counter()
        response = requests.post(ORCHESTRATOR_URL, files=files, timeout=60)
        latency_ms = (time.perf_counter() - start) * 1000.0

    return response, round(latency_ms, 2)


def run_tests():
    if not TEST_CASES_PATH.exists():
        print("test_cases.json bulunamadı.")
        return

    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    rows = []

    for case in test_cases:
        case_id = case["id"]
        description = case["description"]
        image_path = Path(case["image_path"])
        expected_action = case["expected_action"]
        expected_people_min = case["expected_people_min"]
        expected_people_max = case["expected_people_max"]
        expected_position = case["expected_position"]
        category = case["category"]

        if not image_path.exists():
            print(f"{case_id}: görsel bulunamadı -> {image_path}")
            rows.append(
                {
                    "id": case_id,
                    "description": description,
                    "category": category,
                    "status": "missing_file",
                    "expected_action": expected_action,
                    "actual_action": "",
                    "action_correct": False,
                    "expected_people_min": expected_people_min,
                    "expected_people_max": expected_people_max,
                    "actual_people_count": "",
                    "people_count_correct": False,
                    "expected_position": expected_position,
                    "actual_position": "",
                    "position_correct": False,
                    "false_trigger": False,
                    "detection_error": True,
                    "position_error": False,
                    "latency_ms": "",
                    "avg_latency_ms": "",
                    "repeat_count": REPEAT_PER_TEST,
                    "reason": "image file not found",
                    "utterance_tr": "",
                    "source": "",
                }
            )
            continue

        try:
            requests.post(RESET_URL, timeout=10)
        except Exception as e:
            print(f"{case_id}: reset hatası -> {e}")

        last_response = None
        last_latency_ms = None
        latencies = []

        for repeat_idx in range(REPEAT_PER_TEST):
            response, latency_ms = send_image(image_path)
            last_response = response
            last_latency_ms = latency_ms
            latencies.append(latency_ms)

            time.sleep(0.15)

        avg_latency_ms = round(sum(latencies) / len(latencies), 2)

        if last_response is None or last_response.status_code != 200:
            error_text = "" if last_response is None else last_response.text

            rows.append(
                {
                    "id": case_id,
                    "description": description,
                    "category": category,
                    "status": "error",
                    "expected_action": expected_action,
                    "actual_action": "",
                    "action_correct": False,
                    "expected_people_min": expected_people_min,
                    
    "expected_people_max": expected_people_max,
                    "actual_people_count": "",
                    "people_count_correct": False,
                    "expected_position": expected_position,
                    "actual_position": "",
                    "position_correct": False,
                    "false_trigger": False,
                    "detection_error": True,
                    "position_error": False,
                    "latency_ms": last_latency_ms,
                    "avg_latency_ms": avg_latency_ms,
                    "repeat_count": REPEAT_PER_TEST,
                    "reason": error_text,
                    "utterance_tr": "",
                    "source": "",
                }
            )
            continue

        data = last_response.json()
        perception = data.get("perception", {})
        reasoning = data.get("reasoning", {})

        actual_people_count = perception.get("people_count")
        actual_position = normalize_position(
            perception.get("primary_person", {}).get("position")
        )
        actual_action = reasoning.get("action")
        reason = reasoning.get("reason", "")
        utterance_tr = reasoning.get("utterance_tr", "")
        source = reasoning.get("source", "")

        action_correct = actual_action == expected_action
        people_count_correct = expected_people_min <= actual_people_count <= expected_people_max
        position_correct = actual_position == expected_position

        false_trigger = is_false_trigger(expected_action, actual_action)
        detection_error = not people_count_correct
        position_error = not position_correct

        status = (
            "pass"
            if action_correct and people_count_correct and position_correct
            else "fail"
        )

        rows.append(
            {
                "id": case_id,
                "description": description,
                "category": category,
                "status": status,
                "expected_action": expected_action,
                "actual_action": actual_action,
                "action_correct": action_correct,
                "expected_people_min": expected_people_min,
                "expected_people_max": expected_people_max, 
                "actual_people_count": actual_people_count,
                "people_count_correct": people_count_correct,
                "expected_position": expected_position,
                "actual_position": actual_position,
                "position_correct": position_correct,
                "false_trigger": false_trigger,
                "detection_error": detection_error,
                "position_error": position_error,
                "latency_ms": last_latency_ms,
                "avg_latency_ms": avg_latency_ms,
                "repeat_count": REPEAT_PER_TEST,
                "reason": reason,
                "utterance_tr": utterance_tr,
                "source": source,
            }
        )

        print(
            f"{case_id} | {status} | "
            f"exp_action={expected_action}, actual_action={actual_action} | "
            f"exp_people={expected_people_min}-{expected_people_max}, actual_people={actual_people_count} | "
            f"exp_pos={expected_position}, actual_pos={actual_position} | "
            f"last_latency={last_latency_ms} ms | avg_latency={avg_latency_ms} ms"
        )

    fieldnames = [
        "id",
        "description",
        "category",
        "status",
        "expected_action",
        "actual_action",
        "action_correct",
        "expected_people_min",
        "expected_people_max",
        "actual_people_count",
        "people_count_correct",
        "expected_position",
        "actual_position",
        "position_correct",
        "false_trigger",
        "detection_error",
        "position_error",
        "latency_ms",
        "avg_latency_ms",
        "repeat_count",
        "reason",
        "utterance_tr",
        "source",
    ]

    with open(RESULTS_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    passed = sum(1 for r in rows if r["status"] == "pass")
    failed = sum(1 for r in rows if r["status"] == "fail")
    missing = sum(1 for r in rows if r["status"] == "missing_file")
    errors = sum(1 for r in rows if r["status"] == "error")

    action_correct_count = sum(1 for r in rows if r["action_correct"] is True)
    people_correct_count = sum(1 for r in rows if r["people_count_correct"] is True)
    position_correct_count = sum(1 for r in rows if r["position_correct"] is True)

    false_trigger_count = sum(1 for r in rows if r["false_trigger"] is True)
    detection_error_count = sum(1 for r in rows if r["detection_error"] is True)
    position_error_count = sum(1 for r in rows if r["position_error"] is True)

    valid_avg_latencies = [
        r["avg_latency_ms"]
        for r in rows
        if isinstance(r["avg_latency_ms"], (int, float))
    ]
    overall_avg_latency = (
        sum(valid_avg_latencies) / len(valid_avg_latencies)
        if valid_avg_latencies
        else 0.0
    )

    summary = f"""
TEST SUMMARY
============

Total tests: {total}
Passed: {passed}
Failed: {failed}
Missing files: {missing}
Runtime errors: {errors}

Action accuracy: {action_correct_count}/{total}
People count accuracy: {people_correct_count}/{total}
Position accuracy: {position_correct_count}/{total}

False trigger count: {false_trigger_count}
Detection error count: {detection_error_count}
Position error count: {position_error_count}

Repeat per test: {REPEAT_PER_TEST}
Average latency_ms: {round(overall_avg_latency, 2)}
"""

    with open(SUMMARY_TXT_PATH, "w", encoding="utf-8") as f:
        f.write(summary)

    print(summary)
    print(f"Sonuçlar kaydedildi: {RESULTS_CSV_PATH}")
    print(f"Özet kaydedildi: {SUMMARY_TXT_PATH}")


if __name__ == "__main__":
    run_tests()
