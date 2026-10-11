from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

POST_PROCESS_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "post_process_script.sh"
RAW_HEADER = "Data;import;export;net_import;net_export\n"
OUTPUT_HEADER = "statistic_id,unit,start,delta\n"


@pytest.fixture
def post_process_env(tmp_path: Path) -> dict[str, str]:
    output_dir = tmp_path / "home assistant"
    output_dir.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    curl = bin_dir / "curl"
    curl.write_text('#!/bin/bash\nprintf \'%s\\n\' "$@" > "$CURL_ARGS_PATH"\n', encoding="utf-8")
    curl.chmod(0o755)

    return {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "CURL_ARGS_PATH": str(tmp_path / "curl_args.txt"),
        "ENEA_CLIENT_POST_PROCESS_HOME_ASSISTANT_CONFIG_DIR": str(output_dir),
        "ENEA_CLIENT_POST_PROCESS_OUTPUT_PATH": "statistics.csv",
        "ENEA_CLIENT_POST_PROCESS_HOME_ASSISTANT_TOKEN": "test-token",
    }


def run_script(inputs: list[Path], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [str(POST_PROCESS_SCRIPT), *map(str, inputs)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def read_output(env: dict[str, str]) -> str:
    output = Path(env["ENEA_CLIENT_POST_PROCESS_HOME_ASSISTANT_CONFIG_DIR"])
    return (output / env["ENEA_CLIENT_POST_PROCESS_OUTPUT_PATH"]).read_bytes().decode("utf-8")


@pytest.mark.parametrize(
    ("rows", "expected_rows"),
    [
        (
            '\x00"=""2025-09-01 00:59"""\x00;"0,507";"0";"0,507";"0"\n',
            (
                "sensor.grid_import_energy,kWh,2025-09-01 00:00,0.507\n"
                "sensor.grid_export_energy,kWh,2025-09-01 00:00,0\n"
            ),
        ),
        (
            '\x00"=""2025-09-01 01:59"""\x00;"0";"12,34";"0";"12,34"',
            (
                "sensor.grid_import_energy,kWh,2025-09-01 01:00,0\n"
                "sensor.grid_export_energy,kWh,2025-09-01 01:00,12.34\n"
            ),
        ),
        (
            (
                'some line with "---" that should be removed\n'
                '"2025-09-01 00:59";"0,507";"0";"0,507";"0"\n'
                '"2025-09-01 01:59";"---";"0";"---";"0"'
            ),
            (
                "sensor.grid_import_energy,kWh,2025-09-01 00:00,0.507\n"
                "sensor.grid_export_energy,kWh,2025-09-01 00:00,0\n"
            ),
        ),
        (
            '\x00"=""2025-09-01 00:59"""\x00;"0,507";"0";"0,507";"0"\r\n',
            (
                "sensor.grid_import_energy,kWh,2025-09-01 00:00,0.507\n"
                "sensor.grid_export_energy,kWh,2025-09-01 00:00,0\r\n"
            ),
        ),
        (
            '"2025-09-01 00:59";"0.507";"0";"0.507";"0"\n',
            (
                "sensor.grid_import_energy,kWh,2025-09-01 00:00,0.507\n"
                "sensor.grid_export_energy,kWh,2025-09-01 00:00,0\n"
            ),
        ),
        (
            '\x00"=""2025-09-01 00:59"""\x00;"0";"0";"=""1,23""";"=""4,56"""\n',
            (
                "sensor.grid_import_energy,kWh,2025-09-01 00:00,1.23\n"
                "sensor.grid_export_energy,kWh,2025-09-01 00:00,4.56\n"
            ),
        ),
        ('"2025-09-01 00:59";"---";"---";"---";"---"\n', ""),
        ("", ""),
    ],
    ids=[
        "raw", "no-final-newline", "placeholder-rows", "crlf", "sanitized", "excel-wrappers", "no-data", "header-only",
    ],
)
def test_post_process_sanitizes_raw_csv(
    tmp_path: Path,
    post_process_env: dict[str, str],
    rows: str,
    expected_rows: str,
) -> None:
    source = tmp_path / "raw input.csv"
    original = (RAW_HEADER + rows).encode("utf-8")
    source.write_bytes(original)

    result = run_script([source], post_process_env)

    assert result.returncode == 0, result.stderr
    assert read_output(post_process_env) == OUTPUT_HEADER + expected_rows
    assert source.read_bytes() == original
    assert Path(post_process_env["CURL_ARGS_PATH"]).exists()


def test_post_process_multiple_inputs_and_import(tmp_path: Path, post_process_env: dict[str, str]) -> None:
    first = tmp_path / "02.2026.csv"
    second = tmp_path / "03.2026.csv"
    first_data = (RAW_HEADER + '\x00"=""2026-02-01 00:59"""\x00;"0,507";"0";"0,507";"0"\n').encode()
    second_data = (RAW_HEADER + '\x00"=""2026-03-29 02:59"""\x00;"0";"0,123";"0";"0,123"').encode()
    first.write_bytes(first_data)
    second.write_bytes(second_data)

    result = run_script([first, second], post_process_env)

    assert result.returncode == 0, result.stderr
    assert read_output(post_process_env) == (
        OUTPUT_HEADER
        + "sensor.grid_import_energy,kWh,2026-02-01 00:00,0.507\n"
        "sensor.grid_export_energy,kWh,2026-02-01 00:00,0\n"
        "sensor.grid_import_energy,kWh,2026-03-29 01:00,0\n"
        "sensor.grid_export_energy,kWh,2026-03-29 01:00,0.123\n"
    )
    assert first.read_bytes() == first_data
    assert second.read_bytes() == second_data

    arguments = Path(post_process_env["CURL_ARGS_PATH"]).read_text(encoding="utf-8").splitlines()
    assert arguments[:9] == [
        "-X", "POST", "-H", "Authorization: Bearer test-token", "-H", "Content-Type: application/json",
        "http://localhost:8123/api/services/import_statistics/import_from_file", "-d", "{",
    ]
    assert json.loads("\n".join(arguments[8:])) == {
        "filename": "statistics.csv",
        "timezone_identifier": "Europe/Warsaw",
        "delimiter": ",",
        "decimal": ".",
        "datetime_format": "%Y-%m-%d %H:%M",
        "unit_from_entity": False,
    }


def test_post_process_does_not_import_on_input_failure(tmp_path: Path, post_process_env: dict[str, str]) -> None:
    result = run_script([tmp_path / "missing.csv"], post_process_env)

    assert result.returncode != 0
    assert not Path(post_process_env["CURL_ARGS_PATH"]).exists()


@pytest.mark.parametrize("relative_script_path", [False, True], ids=["absolute-path", "relative-path"])
def test_post_process_locates_converter_from_another_directory(
    tmp_path: Path,
    post_process_env: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    *,
    relative_script_path: bool,
) -> None:
    deployment_dir = tmp_path / "deployed scripts"
    deployment_dir.mkdir()
    script = deployment_dir / POST_PROCESS_SCRIPT.name
    shutil.copy2(POST_PROCESS_SCRIPT, script)
    converter = "enea_to_home_assistant.awk"
    shutil.copy2(POST_PROCESS_SCRIPT.with_name(converter), deployment_dir / converter)

    source = tmp_path / "raw input.csv"
    original = (RAW_HEADER + '\x00"=""2025-09-01 00:59"""\x00;"0,507";"0";"0,507";"0"\n').encode()
    source.write_bytes(original)
    working_dir = tmp_path / "other directory"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)
    command = os.path.relpath(script, working_dir) if relative_script_path else str(script)

    result = subprocess.run(  # noqa: S603
        [command, str(source)], env=post_process_env, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0, result.stderr
    assert read_output(post_process_env) == (
        OUTPUT_HEADER
        + "sensor.grid_import_energy,kWh,2025-09-01 00:00,0.507\n"
        "sensor.grid_export_energy,kWh,2025-09-01 00:00,0\n"
    )
    assert source.read_bytes() == original
    assert Path(post_process_env["CURL_ARGS_PATH"]).exists()
