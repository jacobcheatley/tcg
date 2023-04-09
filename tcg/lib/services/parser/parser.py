from lib.services.parser.grammar import MANA_COST_IN_COST, TEXT


class Parser:
    def __init__(self) -> None:
        self._text_grammar = TEXT
        self._cost_grammar = MANA_COST_IN_COST

    def parse_text(self, text: str) -> str:
        parsed = self._text_grammar.parse_string(text)
        # print(parsed)
        # print("===>")
        return "".join(parsed)

    def parse_cost(self, cost: str) -> dict:
        return self._cost_grammar.parse_string(cost)
