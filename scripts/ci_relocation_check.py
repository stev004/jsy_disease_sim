from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from jersey_outbreak.scientific_verification import verify_scientific_artifact


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cli_result = subprocess.run(
        ["uv", "run", "jos", "intervention", "run", "--mode", "ci", "--seed", "123"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    print(cli_result.stdout.strip())
    summary = json.loads(cli_result.stdout)
    artifact_directory = Path(summary["artifact_directory"]).resolve()
    expected_parent = (root / "outputs" / "interventions").resolve()
    if artifact_directory.parent != expected_parent:
        raise ValueError(f"CLI did not use its default output location: {artifact_directory}")

    with tempfile.TemporaryDirectory(prefix="jos-ci-relocation-") as temporary_directory:
        copied_directory = Path(temporary_directory) / artifact_directory.name
        shutil.copytree(artifact_directory, copied_directory)
        shutil.rmtree(artifact_directory)
        verified = verify_scientific_artifact(copied_directory)
        if verified.artifact_type != "m7_intervention":
            raise ValueError(f"unexpected artifact type: {verified.artifact_type}")
        print(f"verifier success: {verified.artifact_type} {verified.artifact_id}")


if __name__ == "__main__":
    main()
