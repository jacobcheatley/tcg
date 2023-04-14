import itertools
import re
from enum import Flag, auto
from typing import Self


class Color(Flag):
    DIVINE = auto()
    ARCANE = auto()
    OCCULT = auto()
    PRIMAL = auto()
    ALCHEMY = auto()

    @classmethod
    def from_string(cls, string: str) -> Self:
        result = cls(0)
        for char in string:
            result |= cls.shortcuts[char]
        return result

    @property
    def as_ordered_string(self) -> str:
        return self.ordering_string[self]

    @property
    def as_ordered_enum(self) -> tuple[Self]:
        return self.ordering_enums[self]

    @property
    def as_name_list(self) -> list[str]:
        return [self.names[color] for color in self.as_ordered_enum]


Color.shortcuts = {
    "D": Color.DIVINE,
    "A": Color.ARCANE,
    "O": Color.OCCULT,
    "P": Color.PRIMAL,
    "L": Color.ALCHEMY,
}
Color.names = {
    Color.DIVINE: "divine",
    Color.ARCANE: "arcane",
    Color.OCCULT: "occult",
    Color.PRIMAL: "primal",
    Color.ALCHEMY: "alchemy",
}
Color.shortcut_keys = "".join(Color.shortcuts)

# fmt: off
sorted_colors = [
    # Mono
    "D", "A", "O", "P", "L",
    # Dual - Ally
    "DA", "AO", "OP", "PL", "LD",
    # Dual - Enemy
    "DO", "AP", "OL", "PD", "LA",
    # Triple - Arc
    "DAO", "AOP", "OPL", "PLD", "LDA",
    # Triple - Wedge
    # (AKA the only one with ambiguous modular distance and the reason I was too lazy to automate this)
    "DAP", "AOL", "OPD", "PLA", "LDO",
    # Quadruple
    "DAOP", "AOPL", "OPLD", "PLDA", "LDAO",
    # Five
    "DAOPL",
]
# fmt: on

Color.ordering_string = {Color.from_string(string): string for string in sorted_colors}
Color.ordering_enums = {
    Color.from_string(string): tuple((Color.from_string(c) for c in string)) for string in sorted_colors
}


class ManaCostInfo:
    REGEX_PATTERN = re.compile(r"\((?P<value>[\dX]+)(?P<color>[" + Color.shortcut_keys + "]+)\)")

    def __init__(self, value: str, color: Color) -> None:
        self.value = value
        self.color = color

    def __repr__(self) -> str:
        return f"({self.value}{self.color.as_ordered_string})"

    @classmethod
    def from_string(cls, string: str) -> Self:
        match = cls.REGEX_PATTERN.match(string)
        return cls.from_regex_match(match)

    @classmethod
    def from_regex_match(cls, match: re.Match) -> Self:
        groupdict = match.groupdict()
        return cls(groupdict["value"], Color.from_string(groupdict["color"]))


class ManaCostHTMLExtension:
    # TODO: Load from a config or something
    COLOR_VALUES = {
        Color.DIVINE: "#f5de0c",
        Color.ARCANE: "#3232e4",
        Color.OCCULT: "#2e2e2e",
        Color.PRIMAL: "#f56600",
        Color.ALCHEMY: "#9e2e9e",
    }

    def __init__(self, info: ManaCostInfo) -> None:
        self.info = info

    @property
    def color_first(self) -> str:
        return self.COLOR_VALUES[self.info.color.as_ordered_enum[0]]

    @property
    def gradient(self) -> str:
        bleed = 2
        hexcodes = [self.COLOR_VALUES[color] for color in self.info.color.as_ordered_enum]
        doubled_hexcodes = itertools.chain.from_iterable([h, h] for h in hexcodes)
        num_colors = len(hexcodes)
        break_percents = [0]
        for n in range(num_colors - 1):
            part = n + 1
            fraction = part / num_colors
            break_percents.append((100 * fraction) - bleed / 2)
            break_percents.append((100 * fraction) + bleed / 2)
        break_percents.append(100)
        break_colors = [f"{hexcode} {percent}%" for (percent, hexcode) in zip(break_percents, doubled_hexcodes)]
        return f"linear-gradient(to right, {', '.join(break_colors)})"

    @property
    def element(self) -> str:
        return f"<span class='mana' style='background: {self.gradient}'><span class='mana-value'>{self.info.value}</span></span>"

    @property
    def channel_element(self) -> str:
        return f"<span class='mana' style='background: {self.gradient}'><span class='mana-value'>1</span></span>"


# if __name__ == "__main__":
#     print(ColorHTMLExtension(Color.DIVINE | Color.ARCANE | Color.PRIMAL).gradient)
# print(ManaCostInfo.from_string("(2DA)"))
# print(ManaCostInfo.from_string("(21DAO)"))
# print(ManaCostInfo.from_string("(0PDA)"))
# print(ManaCostInfo.from_string("(XDLA)"))


# def sort_multicolor(colors: str) -> str:
#     return color_sets["".join(sorted(colors.upper()))]


# if __name__ == "__main__":
#     print(sort_multicolor("D"))
#     print(sort_multicolor("AD"))
#     print(sort_multicolor("DOP"))
#     print(sort_multicolor("LDPAO"))
#     print(sort_multicolor("OPA"))
