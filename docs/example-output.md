# Example Output

Paths and run identifiers below are shortened; field names and values match the
v1 structured contracts.

## Environment

```json
{
  "basilisk": {"ok": true, "requirement": "==2.11.1", "version": "2.11.1"},
  "basilisk_tools": {"version": "0.1.0"},
  "errors": [],
  "ok": true,
  "python": {"ok": true, "requirement": ">=3.11", "version": "3.11.15"},
  "schema_version": 1
}
```

## Inspection

```json
{
  "scenario": "point_mass_vs_j2_leo",
  "supported": true,
  "cases": [
    {
      "name": "point-mass",
      "runtime": {
        "execution_order": ["leoSpacecraft", "Rec:SCStatesMsg"],
        "message_connections": [
          {"source_name": "scStateOutMsg", "target_name": "recordedMsg"}
        ],
        "supported": true
      }
    }
  ],
  "schema_version": 1
}
```

## Run result

```json
{
  "artifacts": {
    "metadata": ".bsk/runs/<run-id>/metadata.json",
    "result": ".bsk/runs/<run-id>/result.json",
    "verification": ".bsk/runs/<run-id>/artifacts/verification.json"
  },
  "elapsed_seconds": 1.48,
  "error": null,
  "exit_code": 0,
  "run_id": "<run-id>",
  "schema_version": 1,
  "status": "success"
}
```

## Verification check

```json
{
  "actual": -8.347856358096783e-7,
  "expected": -8.338059273387823e-7,
  "name": "j2.j2_raan_rate",
  "passed": true,
  "tolerance": 1.6676118546775647e-8,
  "units": "rad/s"
}
```

Use `--json` and read the complete generated files when automating decisions;
these excerpts are presentation aids, not substitutes for run artifacts.
