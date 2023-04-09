# Process will be basically
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


class ManaCostEnrichmentPipeline(AbstractPipeline):
    def __init__(self) -> None:
        self.mana_names = {"D": "divine", "A": "arcane", "O": "occult", "P": "primal", "L": "alchemy"}
        self.mana_keys = "".join(self.mana_names.keys())
        self.pattern = re.compile(
            r"\((?P<value>[\d]{1,2})(?P<first>[" + self.mana_keys + "])(?P<second>[" + self.mana_keys + "]?)\)"
        )

    def _convert(self, symbol: str):
        return self.mana_names.get(symbol)

    def __call__(self, data: PipelineData) -> PipelineData:
        groupdict = self.pattern.match(data["card__cost"]).groupdict()
        data["cost__value"] = groupdict["value"]
        data["cost__first"] = self._convert(groupdict["first"])
        data["cost__second"] = self._convert(groupdict["second"])
        data["cost__namelist"] = [data["cost__first"]] + ([data["cost__second"]] if data["cost__second"] else [])
        data["cost__names"] = " ".join(data["cost__namelist"])
        return data


class PrefixPipeline(AbstractPipeline):
    def __init__(self, prefix) -> None:
        self.prefix = prefix

    def __call__(self, data: PipelineData) -> PipelineData:
        return {f"{self.prefix}{k}": v for k, v in data.items()}


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

        new_text = self.pattern.sub(_repl, data["card__text"])
        data["card__text"] = new_text
        return data


class FormatPipeline(AbstractPipeline):
    def __call__(self, data: PipelineData) -> PipelineData:
        data["card__text"] = data["card__text"].format(**data)
        return data


enrich_pipeline = ConcatPipeline([PrefixPipeline("card__"), ManaCostEnrichmentPipeline()])
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
        RegexReplacePipeline("l(", "<ul class=''>"),
        RegexReplacePipeline(")l", "</ul>"),
        RegexReplacePipeline("|", "<br>"),
    ]
)
to_formatted_pipeline = ConcatPipeline([to_html_pipeline, RegexReplacePipeline("~", "{card__name}"), FormatPipeline()])

print(
    to_formatted_pipeline(
        {
            "name": "A custom name",
            "text": "k.blocker(), kr.complicated(some args, ignore these though)",
            "cost": "(2DA)",
            "tags": "Beast Human AnotherTag",
            "power": 3,
        }
    )
)
