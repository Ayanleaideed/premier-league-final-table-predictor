from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from fastapi import File, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field, field_validator

try:  # Loading through joblib keeps compatibility with the training notebook.
    import joblib
except ModuleNotFoundError:  # pragma: no cover - joblib should be available in prod.
    joblib = None


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "src" / "Training" / "rf_model_2024_25.joblib"
# Feature columns must match the exact order from training (see src/Training/Training.ipynb)
FEATURE_COLUMNS = [
    "prev_points",
    "prev_position",
    "prev_position_vs_avg",
    "prev_goal_difference",
    "prev_wins",
    "prev_draws",
    "prev_losses",
    "prev_points_per_game",
    "prev_win_pct",
    "prev_goals_per_game",
    "prev_goals_conceded_per_game",
    "prev_home_advantage",
    "prev_home_wins",
    "prev_away_wins",
    "is_promoted",
    "prev_position_category_numeric",
]
REQUIRED_UPLOAD_FIELDS = [
    "team",
    "wins",
    "draws",
    "losses",
    "goalsFor",
    "goalsAgainst",
    "homeWins",
    "awayWins",
]
MATCH_REQUIRED = {"hometeam", "awayteam", "fthg", "ftag"}
COLUMN_ALIASES: Dict[str, List[str]] = {
    "team": ["team", "club", "clubname", "squad", "teamname"],
    "wins": ["wins", "win", "w", "won"],
    "draws": ["draws", "draw", "d", "drawn"],
    "losses": ["losses", "loss", "l", "lost"],
    "goalsFor": [
        "goalsfor",
        "goals_for",
        "gf",
        "forgoals",
        "f",
        "for",
        "scored",
        "goals_scored",
    ],
    "goalsAgainst": [
        "goalsagainst",
        "goals_against",
        "ga",
        "againstgoals",
        "a",
        "against",
        "conceded",
        "goals_conceded",
    ],
    "homeWins": [
        "homewins",
        "home_wins",
        "homew",
        "homewin",
        "home_w",
        "homewon",
    ],
    "awayWins": [
        "awaywins",
        "away_wins",
        "awayw",
        "awaywin",
        "away_w",
        "awaywon",
    ],
    "isPromoted": ["ispromoted", "promoted", "promotion_flag"],
    "matchesPlayed": [
        "matchesplayed",
        "matches_played",
        "mp",
        "gamesplayed",
        "played",
        "pl",
        "games",
    ],
    "points": ["points", "pts", "totalpoints"],
}


class TeamInput(BaseModel):
    team: str
    wins: int
    draws: int
    losses: int
    goals_for: int = Field(..., alias="goalsFor")
    goals_against: int = Field(..., alias="goalsAgainst")
    home_wins: int = Field(..., alias="homeWins")
    away_wins: int = Field(..., alias="awayWins")
    is_promoted: int = Field(0, alias="isPromoted")
    matches_played: int | None = Field(None, alias="matchesPlayed")
    points: int | None = None

    @field_validator("is_promoted", mode="before")
    @classmethod
    def normalize_promoted(cls, value: int | bool | str) -> int:
        truthy = {"true", "1", "yes", "y"}
        falsy = {"false", "0", "no", "n"}
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        val = str(value).strip().lower()
        if val in truthy:
            return 1
        if val in falsy or val == "":
            return 0
        raise ValueError("is_promoted must be boolean-ish (0/1, true/false).")

    @field_validator("matches_played", mode="after")
    @classmethod
    def default_matches(cls, value, info):
        if value:
            return value
        wins = info.data.get("wins", 0)
        draws = info.data.get("draws", 0)
        losses = info.data.get("losses", 0)
        total = wins + draws + losses
        if total == 0:
            raise ValueError("wins + draws + losses must be greater than zero.")
        return total

    model_config = ConfigDict(populate_by_name=True)


class PredictionRequest(BaseModel):
    season: str = "2024-25"
    teams: List[TeamInput]


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app = FastAPI(title="Premier League Predictor", version="1.0.0")
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)


def _load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Re-run the training notebook."
        )
    try:
        if joblib:
            return joblib.load(MODEL_PATH)
    except Exception as exc:  # pragma: no cover - handled below.
        raise RuntimeError(f"Unable to load model via joblib: {exc}") from exc

    # Fallback when joblib is unavailable but pickle is.
    import pickle  # type: ignore

    with MODEL_PATH.open("rb") as handle:
        return pickle.load(handle)


def _position_category(position: int) -> int:
    if position <= 4:
        return 1  # Champions League
    if position <= 6:
        return 2  # Europa/Conference
    if position <= 10:
        return 3  # Upper mid-table
    if position <= 17:
        return 4  # Survival scrap
    return 5  # Relegation


def _prepare_features(payload: PredictionRequest) -> pd.DataFrame:
    df = pd.DataFrame([team.model_dump(by_alias=True) for team in payload.teams])
    rename_map = {
        "goalsFor": "goals_for",
        "goalsAgainst": "goals_against",
        "homeWins": "home_wins",
        "awayWins": "away_wins",
        "isPromoted": "is_promoted",
        "matchesPlayed": "matches_played",
    }
    df = df.rename(columns=rename_map)
    df["team"] = [team.team for team in payload.teams]

    if "matches_played" not in df:
        df["matches_played"] = df["wins"] + df["draws"] + df["losses"]
    if "points" not in df:
        df["points"] = np.nan
    df["points"] = df["points"].fillna(df["wins"] * 3 + df["draws"])
    df["goal_diff"] = df["goals_for"] - df["goals_against"]

    df = df.sort_values(
        by=["points", "goal_diff", "goals_for"], ascending=[False, False, False]
    ).reset_index(drop=True)
    df["prev_position"] = np.arange(1, len(df) + 1)

    df["prev_points"] = df["points"]
    df["prev_goal_difference"] = df["goal_diff"]
    df["prev_points_per_game"] = df["prev_points"] / df["matches_played"]
    df["prev_goals_conceded_per_game"] = df["goals_against"] / df["matches_played"]
    df["prev_goals_per_game"] = df["goals_for"] / df["matches_played"]
    df["prev_position_vs_avg"] = df["prev_position"] - 10.5
    df["prev_home_advantage"] = (df["home_wins"] - df["away_wins"]) / df["matches_played"]
    df["prev_win_pct"] = df["wins"] / df["matches_played"]
    df["prev_position_category_numeric"] = df["prev_position"].apply(
        _position_category
    )
    df["prev_home_wins"] = df["home_wins"]
    df["prev_away_wins"] = df["away_wins"]
    df["prev_wins"] = df["wins"]
    df["prev_losses"] = df["losses"]
    df["prev_draws"] = df["draws"]
    df["is_promoted"] = df["is_promoted"]

    missing_cols = [col for col in FEATURE_COLUMNS if col not in df]
    if missing_cols:
        raise HTTPException(
            status_code=422,
            detail=f"Missing engineered features: {', '.join(missing_cols)}",
        )
    return df


def _normalize_label(label: str) -> str:
    return "".join(ch for ch in label.lower() if ch.isalnum())


def _match_rows_to_table(df: pd.DataFrame) -> pd.DataFrame | None:
    norm_map = {_normalize_label(col): col for col in df.columns}
    if not MATCH_REQUIRED.issubset(norm_map):
        return None
    home_col = norm_map["hometeam"]
    away_col = norm_map["awayteam"]
    fthg_col = norm_map["fthg"]
    ftag_col = norm_map["ftag"]
    ftr_col = norm_map.get("ftr")

    home_goals = pd.to_numeric(df[fthg_col], errors="coerce").fillna(0).astype(float)
    away_goals = pd.to_numeric(df[ftag_col], errors="coerce").fillna(0).astype(float)
    if ftr_col:
        result = df[ftr_col].astype(str).str.upper().str.strip()
    else:
        result = np.where(
            home_goals > away_goals,
            "H",
            np.where(home_goals < away_goals, "A", "D"),
        )

    home_frame = pd.DataFrame(
        {
            "team": df[home_col].astype(str).str.strip(),
            "wins": (result == "H").astype(int),
            "draws": (result == "D").astype(int),
            "losses": (result == "A").astype(int),
            "goalsFor": home_goals,
            "goalsAgainst": away_goals,
            "homeWins": (result == "H").astype(int),
            "awayWins": 0,
            "matchesPlayed": 1,
        }
    )
    away_frame = pd.DataFrame(
        {
            "team": df[away_col].astype(str).str.strip(),
            "wins": (result == "A").astype(int),
            "draws": (result == "D").astype(int),
            "losses": (result == "H").astype(int),
            "goalsFor": away_goals,
            "goalsAgainst": home_goals,
            "homeWins": 0,
            "awayWins": (result == "A").astype(int),
            "matchesPlayed": 1,
        }
    )

    combined = pd.concat([home_frame, away_frame], ignore_index=True)
    grouped = (
        combined.groupby("team", as_index=False)
        .sum(numeric_only=True)
        .sort_values("team")
    )
    grouped["points"] = grouped["wins"] * 3 + grouped["draws"]
    grouped["isPromoted"] = 0
    return grouped


def _standardize_upload_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    match_table = _match_rows_to_table(df)
    if match_table is not None:
        df = match_table

    original_cols = {_normalize_label(col): col for col in df.columns}
    rename_dict: Dict[str, str] = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            normalized = _normalize_label(alias)
            if normalized in original_cols:
                rename_dict[original_cols[normalized]] = target
                break
    df = df.rename(columns=rename_dict)
    df.columns = [col.strip() for col in df.columns]
    present = set(df.columns)
    missing = [field for field in REQUIRED_UPLOAD_FIELDS if field not in present]

    derivable = []
    if "wins" in present:
        for field in ("homeWins", "awayWins"):
            if field in missing:
                derivable.append(field)
                missing.remove(field)

    if missing:
        raise HTTPException(
            status_code=422,
            detail=(
                "Uploaded file missing columns: "
                f"{', '.join(missing)}. Detected columns: {list(df.columns)}"
            ),
        )

    df["team"] = df["team"].astype(str).str.strip()
    if "isPromoted" not in df:
        df["isPromoted"] = 0
    df["isPromoted"] = pd.to_numeric(df["isPromoted"], errors="coerce").fillna(0)
    if "matchesPlayed" not in df or df["matchesPlayed"].isna().all():
        df["matchesPlayed"] = (
            df.get("matchesPlayed")
            if "matchesPlayed" in df
            else df["wins"] + df["draws"] + df["losses"]
        )
    df["matchesPlayed"] = pd.to_numeric(df["matchesPlayed"], errors="coerce").fillna(
        df["wins"] + df["draws"] + df["losses"]
    )
    if "points" not in df or df["points"].isna().all():
        df["points"] = df["wins"] * 3 + df["draws"]

    numeric_fields = [
        "wins",
        "draws",
        "losses",
        "goalsFor",
        "goalsAgainst",
        "homeWins",
        "awayWins",
        "matchesPlayed",
        "points",
    ]
    for field in numeric_fields:
        if field in df:
            df[field] = pd.to_numeric(df[field], errors="coerce").fillna(0)

    if "homeWins" not in df or "awayWins" not in df:
        wins = df["wins"].fillna(0)
        home_estimate = np.ceil(wins * 0.55)
        if "homeWins" not in df or df["homeWins"].isna().all():
            df["homeWins"] = home_estimate
        if "awayWins" not in df or df["awayWins"].isna().all():
            df["awayWins"] = wins - df["homeWins"]
    column_order = [
        "team",
        "wins",
        "draws",
        "losses",
        "goalsFor",
        "goalsAgainst",
        "homeWins",
        "awayWins",
        "isPromoted",
        "matchesPlayed",
        "points",
    ]
    for col in column_order:
        if col not in df:
            df[col] = np.nan
    df = df[column_order]
    df = df.dropna(subset=["team"])
    return df


def _predict_from_payload(payload: PredictionRequest):
    try:
        df = _prepare_features(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        model = _load_model()
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail="Install scikit-learn + joblib to load the model.",
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    features = df[FEATURE_COLUMNS]
    predicted_points = model.predict(features)
    df["predicted_points"] = predicted_points

    df = df.sort_values(
        by="predicted_points", ascending=False, ignore_index=True
    ).reset_index(drop=True)
    df["predicted_position"] = df.index + 1
    df["season"] = payload.season

    response = [
        {
            "predicted_points": round(float(row.predicted_points), 2),
            "team": row.team,
            "season": row.season,
            "prev_points": row.prev_points,
            "predicted_position": int(row.predicted_position),
            "is_promoted": int(row.is_promoted),
        }
        for row in df.itertuples()
    ]
    return {"predictions": response, "feature_columns": FEATURE_COLUMNS}


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    sample_payload = {
        "season": "2024-25",
        "teams": [
            {
                "team": "Manchester City",
                "wins": 28,
                "draws": 5,
                "losses": 5,
                "goalsFor": 96,
                "goalsAgainst": 36,
                "homeWins": 15,
                "awayWins": 13,
                "isPromoted": 0,
            },
            {
                "team": "Arsenal",
                "wins": 26,
                "draws": 6,
                "losses": 6,
                "goalsFor": 88,
                "goalsAgainst": 32,
                "homeWins": 14,
                "awayWins": 12,
                "isPromoted": 0,
            },
            {
                "team": "Ipswich",
                "wins": 11,
                "draws": 9,
                "losses": 18,
                "goalsFor": 44,
                "goalsAgainst": 69,
                "homeWins": 7,
                "awayWins": 4,
                "isPromoted": 1,
            },
        ],
    }
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sample_payload": json.dumps(sample_payload, indent=2),
            "feature_columns": FEATURE_COLUMNS,
            "model_path": MODEL_PATH,
        },
    )


@app.post("/predict")
def predict(payload: PredictionRequest):
    return _predict_from_payload(payload)


@app.post("/predict/upload")
async def predict_upload(
    season: str = Form("2024-25"), file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required.")
    suffix = Path(file.filename).suffix.lower()
    data = await file.read()
    buffer = io.BytesIO(data)
    try:
        if suffix in {".csv", ".txt"}:
            df = pd.read_csv(buffer)
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(buffer)
        else:
            raise HTTPException(
                status_code=415,
                detail="Unsupported file type. Upload CSV, XLS, or XLSX.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Unable to parse upload: {exc}"
        ) from exc

    standardized = _standardize_upload_dataframe(df)
    records = standardized.to_dict(orient="records")
    teams = [TeamInput(**record) for record in records]
    payload = PredictionRequest(season=season, teams=teams)
    return _predict_from_payload(payload)


@app.get("/health")
def health():
    exists = MODEL_PATH.exists()
    return {"status": "ok" if exists else "missing-model", "model_path": str(MODEL_PATH)}



if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
