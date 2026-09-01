Implemented and verified. No commit made.

Files changed:

- [cli.py](/private/tmp/jsy_v12_carryins/src/jersey_outbreak/cli.py:1215): added `jos verify bundle-selftest`.
- [bundle_selftest.py](/private/tmp/jsy_v12_carryins/src/jersey_outbreak/bundle_selftest.py): copy/verify/transcript implementation.
- [test_v12_bundle_selftest.py](/private/tmp/jsy_v12_carryins/tests/test_v12_bundle_selftest.py): four acceptance/regression tests.

Acceptance evidence:

1. Failing first:

```text
FFFF                                                                     [100%]
No such command 'bundle-selftest'.
4 failed in 4.82s
```

After implementation:

```text
....                                                                     [100%]
4 passed in 4.60s
```

2–5. Covered by the four tests: successful M7 self-test, artifact immutability, tampered-copy failure transcript, safe transcript-location enforcement.

6.

```text
231 tests collected without the new file
235 tests collected with the new file

235 passed, 5 warnings in 609.86s (0:10:09)
```

7.

```text
ruff check .:
All checks passed!

ruff format --check .:
129 files already formatted

mypy:
Success: no issues found in 1 source file

compileall:
exit 0, no output
```

8.

```text
Usage: jos verify bundle-selftest [OPTIONS] {artifact_dir}

Verify a copied scientific artifact and write its relocation transcript.

Arguments:
  artifact_dir  Scientific artifact directory. [required]

Options:
  --transcript-dir  Directory for the bundle-level transcript.
  --keep-copy      Retain the temporary relocated copy for inspection.
  --help           Show this message and exit.
```

9.

```text
 M src/jersey_outbreak/cli.py
?? src/jersey_outbreak/bundle_selftest.py
?? tests/test_v12_bundle_selftest.py

 src/jersey_outbreak/cli.py | 26 ++++++++++++++++++++++++++
 1 file changed, 26 insertions(+)
```

`git diff --stat` omits untracked files; only the three permitted paths appear in status.

Exact passed transcript from criterion 2:

```json
{
  "copied_to": "/var/folders/9m/jy2pqmz52y1760jssxqt1_lh0000gn/T/jos-bundle-selftest-xvttgovw/jos-intervention-m7-ci-seed-123-0edca19826c7",
  "created_at": "2026-09-01T20:08:06.196141+00:00",
  "dirty_worktree_flag": true,
  "git_commit": "b0ff28702bd62581fff9bc758dd38b83075eb420",
  "identities": {
    "agreement": {
      "artifact_bundle_hash": true,
      "artifact_id": true
    },
    "artifact_id": "jos-intervention-m7-ci-seed-123-0edca19826c7",
    "artifact_type": "m7_intervention",
    "copy": {
      "artifact_id": "jos-intervention-m7-ci-seed-123-0edca19826c7",
      "artifact_type": "m7_intervention",
      "hashes": {
        "artifact_bundle_hash": "0edca19826c72a5c304df4083e2a149d165bb13422f94eb05b922c9ee7907604",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.config_hash": "ee3a43f68086fe08d09344a6d1630e0d793097a7786c4937c97880c18fce6495",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.logical_content_hash": "18781cc48d3a25590674e686a107177971351b4bd23684b9397b51d39b4ebac6",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.m2_logical_content_hash": "28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.m3_logical_content_hash": "f072042f07db46a94fd61781eb9ee99545a6dc169d34b83d6de21ffdf56e3ce3",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.m4_logical_content_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.parameter_set_hash": "a049826fa23d5d2d27fe57926c48b109ac6840e400cde2ffb910733709cbc92d",
        "latent_logical_content_hash": "18781cc48d3a25590674e686a107177971351b4bd23684b9397b51d39b4ebac6",
        "latent_outcome_hash": "648e3683a09074426f96269c7b567f6aefca67b62868d8ea1eb0d5ec0beb64ad",
        "logical_content_hash": "0edca19826c72a5c304df4083e2a149d165bb13422f94eb05b922c9ee7907604",
        "m2_logical_content_hash": "28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0",
        "m3_logical_content_hash": "f072042f07db46a94fd61781eb9ee99545a6dc169d34b83d6de21ffdf56e3ce3",
        "m4_logical_content_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657",
        "m5_disease_config_hash": "a049826fa23d5d2d27fe57926c48b109ac6840e400cde2ffb910733709cbc92d",
        "run_config_hash": "ee3a43f68086fe08d09344a6d1630e0d793097a7786c4937c97880c18fce6495",
        "scenario_config_hash": "444a42a0397bf9ed9222dcfe5e0ddf0cfe00ca44ea8eba75f06eddf4deb8f615",
        "scenario_hash": "f6cd0985dc6d97eb6c578725717fe6761b6bcd120efa85cf63bbd52a87f1ff82"
      },
      "wall_time_seconds": 0.018802749924361706
    },
    "source": {
      "artifact_id": "jos-intervention-m7-ci-seed-123-0edca19826c7",
      "artifact_type": "m7_intervention",
      "hashes": {
        "artifact_bundle_hash": "0edca19826c72a5c304df4083e2a149d165bb13422f94eb05b922c9ee7907604",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.config_hash": "ee3a43f68086fe08d09344a6d1630e0d793097a7786c4937c97880c18fce6495",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.logical_content_hash": "18781cc48d3a25590674e686a107177971351b4bd23684b9397b51d39b4ebac6",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.m2_logical_content_hash": "28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.m3_logical_content_hash": "f072042f07db46a94fd61781eb9ee99545a6dc169d34b83d6de21ffdf56e3ce3",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.m4_logical_content_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657",
        "embedded.latent_outputs.jos-outbreak-m5-ci-seed-123-18781cc48d3a.parameter_set_hash": "a049826fa23d5d2d27fe57926c48b109ac6840e400cde2ffb910733709cbc92d",
        "latent_logical_content_hash": "18781cc48d3a25590674e686a107177971351b4bd23684b9397b51d39b4ebac6",
        "latent_outcome_hash": "648e3683a09074426f96269c7b567f6aefca67b62868d8ea1eb0d5ec0beb64ad",
        "logical_content_hash": "0edca19826c72a5c304df4083e2a149d165bb13422f94eb05b922c9ee7907604",
        "m2_logical_content_hash": "28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0",
        "m3_logical_content_hash": "f072042f07db46a94fd61781eb9ee99545a6dc169d34b83d6de21ffdf56e3ce3",
        "m4_logical_content_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657",
        "m5_disease_config_hash": "a049826fa23d5d2d27fe57926c48b109ac6840e400cde2ffb910733709cbc92d",
        "run_config_hash": "ee3a43f68086fe08d09344a6d1630e0d793097a7786c4937c97880c18fce6495",
        "scenario_config_hash": "444a42a0397bf9ed9222dcfe5e0ddf0cfe00ca44ea8eba75f06eddf4deb8f615",
        "scenario_hash": "f6cd0985dc6d97eb6c578725717fe6761b6bcd120efa85cf63bbd52a87f1ff82"
      },
      "wall_time_seconds": 0.01357299997471273
    }
  },
  "jos_version": "1.1.0",
  "logical_content_hash": "2c95ad691f6420297b6aa2838a9ed470f83110e15c1c7bced83050660ea8ce36",
  "schema_version": "1.0",
  "source_artifact": "/private/var/folders/9m/jy2pqmz52y1760jssxqt1_lh0000gn/T/pytest-of-stevenmatson/pytest-595/bundle-selftest0/bundle/artifacts/jos-intervention-m7-ci-seed-123-0edca19826c7",
  "status": "passed",
  "steps": [
    {
      "detail": "Copied artifact to /var/folders/9m/jy2pqmz52y1760jssxqt1_lh0000gn/T/jos-bundle-selftest-xvttgovw/jos-intervention-m7-ci-seed-123-0edca19826c7",
      "status": "passed",
      "step": "copy_artifact"
    },
    {
      "detail": "m7_intervention jos-intervention-m7-ci-seed-123-0edca19826c7 verified in 0.018803s at /var/folders/9m/jy2pqmz52y1760jssxqt1_lh0000gn/T/jos-bundle-selftest-xvttgovw/jos-intervention-m7-ci-seed-123-0edca19826c7",
      "status": "passed",
      "step": "verify_copy"
    },
    {
      "detail": "m7_intervention jos-intervention-m7-ci-seed-123-0edca19826c7 verified in 0.013573s at /private/var/folders/9m/jy2pqmz52y1760jssxqt1_lh0000gn/T/pytest-of-stevenmatson/pytest-595/bundle-selftest0/bundle/artifacts/jos-intervention-m7-ci-seed-123-0edca19826c7",
      "status": "passed",
      "step": "verify_original"
    },
    {
      "detail": "artifact_id_agrees=True; artifact_bundle_hash_agrees=True",
      "status": "passed",
      "step": "compare_identities"
    },
    {
      "detail": "Temporary copy removed",
      "status": "passed",
      "step": "cleanup_copy"
    }
  ]
}
```

Design notes:

- Default transcript location is `<bundle>/verification/` when the source parent is named `artifacts`; otherwise `--transcript-dir` is mandatory.
- Resolved transcript destinations inside the artifact directory are refused.
- Source and copied identities include artifact type/id, verifier-exposed hashes, recursively discovered embedded-manifest hashes, and verification wall time.
- Git metadata follows the existing `_git_metadata` pattern copied into the new module.
- No existing verifier, writer, schema, version, documentation, or configuration files were modified.

Open questions: none.