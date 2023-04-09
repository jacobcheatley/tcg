from dataclasses import dataclass

import pandas as pd


@dataclass
class KeywordDefinition:
    name: str
    display: str
    reminder: str

    @classmethod
    def list_from_dataframe(cls, df: pd.DataFrame):
        return [KeywordDefinition(**row) for row in df.to_dict(orient="records")]
