from typing import Any

import pandas as pd


class GoogleSheetsReader:
    def __init__(self, sheet_id: str) -> None:
        self._sheet_id = sheet_id
        self._url_format = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={{sheet_name}}"

    def read(self, sheet_name: str, **read_kwargs: dict[str, Any]) -> pd.DataFrame:
        return pd.read_csv(
            self._url_format.format(sheet_name=sheet_name),
            header=0,
            false_values=[""],
            keep_default_na=False,
            **read_kwargs,
        )
