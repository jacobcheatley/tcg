from dataclasses import dataclass


@dataclass
class KeywordDefinition:
    name: str
    display: str
    reminder: str
