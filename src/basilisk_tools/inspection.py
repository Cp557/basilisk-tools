"""Basilisk runtime inspection for instrumented scenarios."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from basilisk_tools.instrumentation import error_payload

DEFAULT_INSPECTION_TIMEOUT_SECONDS = 30.0


def _endpoint(endpoint: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": endpoint["id"],
        "module": endpoint.get("moduleTag"),
        "name": endpoint["name"],
        "direction": endpoint["direction"],
        "payload_type": endpoint["payloadType"],
        "is_linked": endpoint["isLinked"],
    }


def inspect_simulation(simulation: Any) -> dict[str, Any]:
    """Extract only structure provided by Basilisk's runtime graph."""
    graph_method = getattr(simulation, "GetMessageConnectionGraph", None)
    if not callable(graph_method):
        return {
            "supported": False,
            "reason": "Basilisk runtime does not expose GetMessageConnectionGraph.",
        }

    graph = graph_method(includeUnlinked=True, includeRecorders=True)
    modules = []
    processes: dict[str, dict[str, Any]] = {}
    for module in graph["modules"]:
        module_record = {
            "tag": module["tag"],
            "process": module["processName"],
            "process_priority": module["processPriority"],
            "task": module["taskName"],
            "task_priority": module["taskPriority"],
            "task_period_s": module["taskPeriod"],
            "model_priority": module["modelPriority"],
            "execution_index": module["executionIndex"],
            "inputs": [_endpoint(item) for item in module["inputs"]],
            "outputs": [_endpoint(item) for item in module["outputs"]],
        }
        modules.append(module_record)

        process = processes.setdefault(
            module["processName"],
            {
                "name": module["processName"],
                "priority": module["processPriority"],
                "tasks": {},
            },
        )
        task = process["tasks"].setdefault(
            module["taskName"],
            {
                "name": module["taskName"],
                "priority": module["taskPriority"],
                "period_s": module["taskPeriod"],
                "modules": [],
            },
        )
        task["modules"].append(module["tag"])

    process_records = []
    for process in processes.values():
        process["tasks"] = list(process["tasks"].values())
        process_records.append(process)

    return {
        "supported": True,
        "source": "Basilisk SimBaseClass.GetMessageConnectionGraph",
        "processes": process_records,
        "modules": modules,
        "execution_order": [module["tag"] for module in modules],
        "message_connections": [
            {
                "source": edge["source"],
                "source_name": edge["sourceName"],
                "target": edge["target"],
                "target_name": edge["targetName"],
                "payload_type": edge["payloadType"],
            }
            for edge in graph["edges"]
        ],
        "unlinked_inputs": [_endpoint(item) for item in graph["unlinkedInputs"]],
        "unresolved_inputs": [_endpoint(item) for item in graph["unresolvedInputs"]],
    }


def inspect_scenario(
    scenario_path: Path,
    *,
    timeout_seconds: float = DEFAULT_INSPECTION_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Inspect an instrumented scenario in a disposable child process."""
    scenario_path = scenario_path.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="bsk-inspect-") as temporary_directory:
        response_path = Path(temporary_directory) / "response.json"
        command = [
            sys.executable,
            "-m",
            "basilisk_tools.tool_worker",
            "inspect",
            "--response",
            str(response_path),
            str(scenario_path),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return error_payload(
                scenario_path,
                TimeoutError(
                    f"Inspection exceeded the {timeout_seconds:g} second timeout."
                ),
            )

        try:
            return json.loads(response_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            message = completed.stderr.strip() or (
                f"Inspection worker exited with code {completed.returncode}."
            )
            return error_payload(scenario_path, RuntimeError(message))
