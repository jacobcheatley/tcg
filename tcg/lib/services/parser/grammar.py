import pyparsing as pp
from lib.services.parser.replacer import (
    FormatReplacer,
    KeywordReplacer,
    ListReplacer,
    ManaCostReplacer,
)

from tcg.lib.definitions import KEYWORDS

TEXT: pp.ParserElement = pp.Forward()
TEXT_LINE: pp.ParserElement = pp.Forward()

# Basic Constructs
NUMBER = pp.Regex(r"[0-9]+")
WORD = pp.Word(pp.alphanums + ".'\": ")
CARDNAME = pp.Literal("~").set_parse_action(lambda _: "{name}")
# ARROW = pp.Literal("->").set_parse_action(lambda _: "→")
NEWLINE = pp.Literal("|").set_parse_action(lambda _: "<br>")

# Mana
MANA_COLOR = pp.oneOf("D A O P L")
MANA_COST = "(" + NUMBER.set_results_name("value") + pp.OneOrMore(MANA_COLOR).set_results_name("colors") + ")"
MANA_COST_IN_TEXT = MANA_COST.copy().set_parse_action(ManaCostReplacer())
MANA_COST_IN_COST = MANA_COST.copy().set_parse_action(ManaCostReplacer(output_dict=True))

# Keywords
TEXT_LIST = pp.delimited_list(pp.Combine(TEXT_LINE)).set_results_name("args")
KEYWORD_IDENTIFIER = (
    ">k"
    + pp.Optional("r").set_parse_action(lambda s, l, t: bool(t)).set_results_name("reminder")
    + "."
    + pp.Regex(r"[a-z]+").set_results_name("name")
)
KEYWORD = (KEYWORD_IDENTIFIER + "(" + pp.Optional(TEXT_LIST) + ")").set_parse_action(KeywordReplacer(KEYWORDS, TEXT))

# Abilities
ACTIVATED = (pp.Literal("<<") + TEXT_LINE.set_results_name("text") + pp.Literal(">>")).set_parse_action(
    FormatReplacer("<span class='ability-activation-cost'>{text}</span>")
)
TRIGGERED = (pp.Literal("[[") + TEXT_LINE.set_results_name("text") + pp.Literal("]]")).set_parse_action(
    FormatReplacer("<span class='ability-trigger'>{text}</span>")
)

# Lists
BULLET_LIST = (pp.Literal(">l(") + pp.Optional(TEXT_LIST) + ")").set_parse_action(ListReplacer())

ATOM = BULLET_LIST | KEYWORD | MANA_COST_IN_TEXT | ACTIVATED | TRIGGERED | CARDNAME | WORD
TEXT_LINE <<= pp.Combine(pp.OneOrMore(ATOM))
TEXT <<= TEXT_LINE + pp.ZeroOrMore(NEWLINE + TEXT_LINE)
