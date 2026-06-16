"""DuckDB result storage."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from mini_tokamak.schemas import CandidateResult


def connect(db_path: str | Path) -> duckdb.DuckDBPyConnection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    init_db(conn)
    return conn


def init_db(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id VARCHAR PRIMARY KEY,
            created_at TIMESTAMP DEFAULT current_timestamp,
            config_path VARCHAR,
            mode VARCHAR,
            n_requested INTEGER,
            output_dir VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS candidate_results (
            run_id VARCHAR,
            candidate_id VARCHAR,
            objective_score DOUBLE,
            feasibility_score DOUBLE,
            dominant_failure_reason VARCHAR,
            machine_type VARCHAR,
            fuel_mode VARCHAR,
            R DOUBLE,
            a DOUBLE,
            aspect_ratio DOUBLE,
            kappa DOUBLE,
            Bt DOUBLE,
            Ip DOUBLE,
            heating_power DOUBLE,
            estimated_volume DOUBLE,
            estimated_plasma_volume DOUBLE,
            result_json JSON
        )
        """
    )


def insert_run(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    config_path: str,
    mode: str,
    n_requested: int,
    output_dir: str,
) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO runs VALUES (?, current_timestamp, ?, ?, ?, ?)",
        [run_id, config_path, mode, n_requested, output_dir],
    )


def insert_candidate_result(conn: duckdb.DuckDBPyConnection, result: CandidateResult) -> None:
    c = result.candidate
    conn.execute(
        """
        INSERT INTO candidate_results VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        [
            result.run_id,
            c.candidate_id,
            result.objective_score,
            result.constraints.feasibility_score,
            result.constraints.dominant_failure_reason,
            c.machine_type,
            c.fuel_mode,
            c.R,
            c.a,
            c.aspect_ratio,
            c.kappa,
            c.Bt,
            c.Ip,
            c.heating_power,
            c.estimated_volume,
            c.estimated_plasma_volume,
            json.dumps(result.model_dump(mode="json")),
        ],
    )


def replace_candidate_result(conn: duckdb.DuckDBPyConnection, result: CandidateResult) -> None:
    conn.execute(
        "DELETE FROM candidate_results WHERE run_id = ? AND candidate_id = ?",
        [result.run_id, result.candidate.candidate_id],
    )
    insert_candidate_result(conn, result)


def list_runs(db_path: str | Path) -> list[dict[str, object]]:
    if not Path(db_path).exists():
        return []
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT run_id, created_at, config_path, mode, n_requested, output_dir FROM runs ORDER BY created_at DESC"
        ).fetchall()
    return [
        {
            "run_id": row[0],
            "created_at": str(row[1]),
            "config_path": row[2],
            "mode": row[3],
            "n_requested": row[4],
            "output_dir": row[5],
        }
        for row in rows
    ]


def best_results(db_path: str | Path, limit: int = 10) -> list[dict[str, object]]:
    if not Path(db_path).exists():
        return []
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT run_id, candidate_id, objective_score, feasibility_score,
                   dominant_failure_reason, machine_type, fuel_mode, R, a, Bt, Ip
            FROM candidate_results
            ORDER BY objective_score DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()
    keys = [
        "run_id",
        "candidate_id",
        "objective_score",
        "feasibility_score",
        "dominant_failure_reason",
        "machine_type",
        "fuel_mode",
        "R",
        "a",
        "Bt",
        "Ip",
    ]
    return [dict(zip(keys, row, strict=False)) for row in rows]
