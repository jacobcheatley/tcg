# Process will be basically
import functools
import re
from abc import ABC, abstractmethod
from typing import Any

from tcg.lib.definitions import KEYWORDS
from tcg.lib.types import KeywordDefinition

PipelineData = dict[str, str]


class AbstractPipeline(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def __call__(self, data: PipelineData) -> PipelineData:
        return data


class ConcatPipeline(AbstractPipeline):
    def __init__(self, pipelines: list[AbstractPipeline]) -> None:
        self.pipelines = pipelines

    def __call__(self, data: PipelineData) -> str:
        result = data
        for pipeline in self.pipelines:
            result = pipeline(result)
        return result


class RegexReplacePipeline(AbstractPipeline):
    def __init__(self, pattern: re.Pattern | str, repl, fields: list[str] = None) -> None:
        self.pattern = pattern if isinstance(pattern, re.Pattern) else re.compile(re.escape(pattern))
        self.repl = repl
        self.fields = fields if fields is not None else ["card__text"]

    def __call__(self, data: PipelineData) -> PipelineData:
        for field in self.fields:
            data[field] = self.pattern.sub(self.repl, data[field])
        return data


MANA_NAMES = {"D": "divine", "A": "arcane", "O": "occult", "P": "primal", "L": "alchemy"}
MANA_KEYS = "".join(MANA_NAMES)
MANA_PATTERN = re.compile(r"\((?P<value>[\d]{1,2})(?P<first>[" + MANA_KEYS + "])(?P<second>[" + MANA_KEYS + "]?)\)")


def mana_information(match: re.Match) -> dict[str, Any]:
    groupdict = match.groupdict()
    result = {
        "value": groupdict["value"],
        "first": MANA_NAMES.get(groupdict["first"]),
        "second": MANA_NAMES.get(groupdict["second"]),
    }
    result["namelist"] = [result["first"]] + ([result["second"]] if result["second"] else [])
    result["names"] = " ".join(result["namelist"])
    return result


class ManaCostEnrichmentPipeline(AbstractPipeline):
    def __call__(self, data: PipelineData) -> PipelineData:
        match = MANA_PATTERN.match(data["card__cost"])
        info = mana_information(match)
        return data | {**PipelineHelpers.prefix("cost__", info)}


class ManaCostReplacePipeline(AbstractPipeline):
    def __call__(self, data: PipelineData) -> PipelineData:
        def _repl(match: re.Match):
            info = mana_information(match)
            return f"<span class='mana {info['names']}'>{info['value']}</span>"

        data["card__text"] = MANA_PATTERN.sub(_repl, data["card__text"])
        data["card__cost"] = MANA_PATTERN.sub(_repl, data["card__cost"])
        return data


class PipelineHelpers:
    @staticmethod
    def prefix(prefix: str, data: PipelineData) -> PipelineData:
        return {f"{prefix}{k}": v for k, v in data.items()}


class KeywordReplacePipeline(AbstractPipeline):
    def __init__(self, keyword_definitions: list[KeywordDefinition]) -> None:
        self.pattern = re.compile(r"k(?P<reminder>r?)\.(?P<name>[a-z]+)\((?P<args>[^\)]*)\)")
        self.keyword_definitions: dict[str, KeywordDefinition] = {
            definition.name: definition for definition in keyword_definitions
        }

    def __call__(self, data: PipelineData) -> PipelineData:
        def _repl(match: re.Match) -> str:
            groupdict = match.groupdict()
            name = groupdict["name"]
            if name not in self.keyword_definitions:
                return f"k(UNKNOWN_KEYWORD_{name})k"
            else:
                show_reminder = bool(groupdict["reminder"])
                args = {f"arg{i}": v for i, v in enumerate(groupdict["args"].split(", "))}
                definition = self.keyword_definitions[name]
                format_string = f"k({definition.display})k" + (f" r({definition.reminder})r" if show_reminder else "")
                format_context = {**data, **args}
                return format_string.format_map(format_context)

        data["card__text"] = self.pattern.sub(_repl, data["card__text"])
        return data


class FormatPipeline(AbstractPipeline):
    def __call__(self, data: PipelineData) -> PipelineData:
        data["card__text"] = data["card__text"].format(**data)
        return data


enrich_pipeline = ConcatPipeline([lambda card: PipelineHelpers.prefix("card__", card), ManaCostEnrichmentPipeline()])
to_pseudo_pipeline = ConcatPipeline([enrich_pipeline, KeywordReplacePipeline(KEYWORDS)])
to_html_pipeline = ConcatPipeline(
    [
        to_pseudo_pipeline,
        RegexReplacePipeline("<<", "<span class='ability-activation-cost'>"),
        RegexReplacePipeline(">>", "</span>"),
        RegexReplacePipeline("[[", "<span class='ability-trigger'>"),
        RegexReplacePipeline("]]", "</span>"),
        RegexReplacePipeline("r(", "<span class='reminder-text'>("),
        RegexReplacePipeline(")r", ")</span>"),
        RegexReplacePipeline("k(", "<span class='keyword-name'>"),
        RegexReplacePipeline(")k", ")</span>"),
        RegexReplacePipeline(
            re.compile("l\((?P<args>.*)\)l"),
            lambda match: f"""<ul class='list'>{''.join([f"<li>{line.strip()}</li>" for line in match.groupdict()['args'].split(',')])}</ul>""",
        ),
        RegexReplacePipeline("", ""),
        RegexReplacePipeline("|", "<br>"),
        ManaCostReplacePipeline(),
    ]
)
to_formatted_pipeline = ConcatPipeline([to_html_pipeline, RegexReplacePipeline("~", "{card__name}"), FormatPipeline()])

print(
    to_formatted_pipeline(
        {
            "name": "A custom name",
            "text": "k.blocker(), kr.complicated((2DA))|<<pay (2DA)>> Choose one: l(one, two, three)l",
            "cost": "(2DA)",
            "tags": "Beast Human AnotherTag",
            "power": 3,
        }
    )["card__text"].replace("<br>", "\n")
)
