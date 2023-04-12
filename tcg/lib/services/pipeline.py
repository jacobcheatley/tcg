# Process will be basically
import re
from abc import ABC, abstractmethod
from typing import Any

from tcg.lib.types import KeywordDefinition

PipelineData = dict[str, str]


class AbstractPipeline(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def __call__(self, data: PipelineData) -> PipelineData:
        return data

    def run_multiple(self, datas: list[PipelineData]) -> list[PipelineData]:
        return [self(data) for data in datas]


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
        print(data)
        match = MANA_PATTERN.match(data["card__cost"])
        info = mana_information(match)
        return data | {**PipelineHelpers.prefix("cost__", info)}


class ManaCostReplacePipeline(AbstractPipeline):
    def __call__(self, data: PipelineData) -> PipelineData:
        def _mana_element(names: str, value: str):
            return f"<span class='mana {names}'><span class='mana-value'>{value}</span></span>"

        def _repl(match: re.Match):
            info = mana_information(match)
            return _mana_element(info["names"], info["value"])

        data["card__text"] = MANA_PATTERN.sub(_repl, data["card__text"])
        card_cost_match = MANA_PATTERN.match(data["card__cost"])
        card_cost_info = mana_information(card_cost_match)
        data["card__cost"] = _mana_element(card_cost_info["names"], card_cost_info["value"])
        data["card__channel_cost"] = _mana_element(card_cost_info["names"], "1")
        return data


class PipelineHelpers:
    @staticmethod
    def prefix(prefix: str, data: PipelineData) -> PipelineData:
        return {f"{prefix}{k}": v for k, v in data.items()}


class KeywordReplacePipeline(AbstractPipeline):
    def __init__(self, keyword_definitions: list[KeywordDefinition]) -> None:
        self.pattern = re.compile(r"\(k(?P<reminder>r?)\.(?P<name>[^\s\/]+)\s?(?P<args>[^\/]*)\/\)")
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


class AutoReminderPipeline(AbstractPipeline):
    def __call__(self, data: PipelineData) -> PipelineData:
        if data["cost__second"] is not None:
            data["card__text"] = f"r(This channels tapped.)r|{data['card__text']}"
        return data


class TypelineEnrichmentPipeline(AbstractPipeline):
    def __call__(self, data: PipelineData) -> PipelineData:
        card_type = data["card__type"]
        card_quick = "quick" if data["card__quick"] else ""
        card_leader = "leader" if data["card__leader"] else ""
        card_typelist: list[str] = [x for x in [card_quick, card_leader, card_type] if x]
        data["card__typelist"] = card_typelist
        data["card__typenames"] = " ".join(card_typelist)
        data["card__typeline"] = " ".join([typeline_name.capitalize() for typeline_name in card_typelist])
        return data


class CardPipeline(AbstractPipeline):
    def __init__(self, *, keyword_definitions: list[KeywordDefinition]) -> None:
        self.enrich_pipeline = ConcatPipeline(
            [
                lambda card: PipelineHelpers.prefix("card__", card),
                ManaCostEnrichmentPipeline(),
                TypelineEnrichmentPipeline(),
            ]
        )
        self.to_pseudo_pipeline = ConcatPipeline([KeywordReplacePipeline(keyword_definitions), AutoReminderPipeline()])
        self.to_html_pipeline = ConcatPipeline(
            [
                RegexReplacePipeline("<<", "<span class='ability-activation-cost'>"),
                RegexReplacePipeline(">>", "</span>"),
                RegexReplacePipeline("[[", "<span class='ability-trigger'>"),
                RegexReplacePipeline("]]", "</span>"),
                RegexReplacePipeline("r(", "<span class='keyword-reminder'>("),
                RegexReplacePipeline(")r", ")</span>"),
                RegexReplacePipeline("k(", "<span class='keyword-display'>"),
                RegexReplacePipeline(")k", "</span>"),
                RegexReplacePipeline(
                    re.compile("l\((?P<args>.*)\)l"),
                    lambda match: f"""<ul class='list'>{''.join([f"<li>{line.strip()}</li>" for line in match.groupdict()['args'].split(',')])}</ul>""",
                ),
                RegexReplacePipeline("", ""),
                RegexReplacePipeline("|", "<br>"),
                ManaCostReplacePipeline(),
            ]
        )
        self.to_formatted_pipeline = ConcatPipeline([RegexReplacePipeline("~", "{card__name}"), FormatPipeline()])

        self.pipeline = ConcatPipeline(
            [self.enrich_pipeline, self.to_pseudo_pipeline, self.to_html_pipeline, self.to_formatted_pipeline]
        )

    def __call__(self, data: PipelineData) -> PipelineData:
        return self.pipeline(data)
