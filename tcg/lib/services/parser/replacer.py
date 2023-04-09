from abc import ABC, abstractmethod
from dataclasses import dataclass

import pyparsing as pp
from lib.definitions import KEYWORDS, MANA_CLASSES


class Replacer(ABC):
    @abstractmethod
    def _replace(self, **kwargs) -> pp.ParserElement:
        pass

    def __call__(self, string: str, location: int, tokens: pp.ParseResults) -> pp.ParserElement:
        return self._replace(**tokens.as_dict())


class FormatReplacer(Replacer):
    def __init__(self, format_string: str):
        super().__init__()
        self.format_string = format_string

    def _replace(self, **kwargs) -> str:
        return self.format_string.format(**kwargs)


class ManaCostReplacer(Replacer):
    def __init__(self, output_dict: bool = False):
        super().__init__()
        self.output_dict = output_dict

    def _replace(self, *, value: str, colors: list[str]) -> str:
        color_classes = [MANA_CLASSES[color] for color in colors]
        color_classname_string = " ".join(color_classes)
        element = f"<span class='mana {color_classname_string}'><div class='mana-background {color_classname_string}'></div><span class='mana-value'>{value}</span></span>"
        if self.output_dict:
            return {"value": value, "color_classes": color_classname_string, "element": element}
        else:
            return element


class KeywordReplacer(Replacer):
    def _replace(self, *, name: str, reminder: bool, args: list[str] = None) -> pp.ParserElement:
        print("KEYWORD REPLACE")
        keyword_definition = KEYWORDS[name]
        display_text = f"<span class='keyword-display'>{keyword_definition.display.format(args=args)}</span>"
        reminder_text = (
            f" <span class='keyword-reminder'>({keyword_definition.reminder.format(args=args)})</span>"
            if reminder
            else ""
        )
        return f"{display_text}{reminder_text}"


class ListReplacer(Replacer):
    def _replace(self, *, args: list[str]):
        list_items = "".join((f"<li>{item}</li>" for item in args))
        return f"<ul class='list'>{list_items}</ul>"
