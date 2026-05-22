from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

UCI_ONLINE_RETAIL_II_ZIP = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_XLSX = DEFAULT_RAW_DIR / "online_retail_II.xlsx"


def fetch_online_retail_ii(raw_dir: Path = DEFAULT_RAW_DIR) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / "online_retail_II.zip"

    if DEFAULT_XLSX.exists():
        return DEFAULT_XLSX

    with urllib.request.urlopen(UCI_ONLINE_RETAIL_II_ZIP, timeout=120) as response:
        with zip_path.open("wb") as file:
            shutil.copyfileobj(response, file)

    with zipfile.ZipFile(zip_path) as archive:
        candidates = [name for name in archive.namelist() if name.lower().endswith(".xlsx")]
        if not candidates:
            raise RuntimeError("UCI zip did not contain an .xlsx file")
        member = candidates[0]
        with archive.open(member) as source, DEFAULT_XLSX.open("wb") as target:
            shutil.copyfileobj(source, target)

    return DEFAULT_XLSX


def load_transactions(path: Path, max_rows: int | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing dataset: {path}")

    if path.suffix.lower() in {".csv", ".txt"}:
        frame = pd.read_csv(path, nrows=max_rows)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None, nrows=max_rows)
        frame = pd.concat(sheets.values(), ignore_index=True)
    elif path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
        if max_rows is not None:
            frame = frame.head(max_rows)
    else:
        raise ValueError(f"unsupported input format: {path.suffix}")

    return clean_transactions(frame)


def clean_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.rename(columns={col: _normalise_column(col) for col in frame.columns}).copy()

    required = {"invoice", "stock_code", "quantity", "invoice_date"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    price_col = "unit_price" if "unit_price" in frame.columns else "price"
    if price_col not in frame.columns:
        frame[price_col] = 1.0

    invoice = frame["invoice"].astype(str)
    clean = frame.loc[
        (~invoice.str.upper().str.startswith("C"))
        & (pd.to_numeric(frame["quantity"], errors="coerce") > 0)
        & (pd.to_numeric(frame[price_col], errors="coerce") > 0)
    ].copy()

    clean["stock_code"] = clean["stock_code"].astype(str)
    clean["quantity"] = pd.to_numeric(clean["quantity"], errors="coerce").fillna(0.0)
    clean["unit_price"] = pd.to_numeric(clean[price_col], errors="coerce").fillna(0.0)
    clean["invoice_date"] = pd.to_datetime(clean["invoice_date"])
    clean["date"] = clean["invoice_date"].dt.floor("D")
    clean["revenue"] = clean["quantity"] * clean["unit_price"]

    return clean[["invoice", "stock_code", "date", "quantity", "unit_price", "revenue"]]


def _normalise_column(name: str) -> str:
    lowered = str(name).strip().lower().replace(" ", "_")
    aliases = {
        "invoiceno": "invoice",
        "invoice": "invoice",
        "stockcode": "stock_code",
        "stock_code": "stock_code",
        "description": "description",
        "quantity": "quantity",
        "invoicedate": "invoice_date",
        "invoice_date": "invoice_date",
        "unitprice": "unit_price",
        "unit_price": "unit_price",
        "price": "price",
        "customer_id": "customer_id",
        "customerid": "customer_id",
        "country": "country",
    }
    return aliases.get(lowered, lowered)
