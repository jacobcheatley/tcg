from lib.services.parser import Parser


class CardConstructor:
    def __init__(self, parser: Parser) -> None:
        self.parser = parser

    def _prefix_dict(self, prefix: str, d: dict):
        return {f"{prefix}{key}": value for key, value in d.items()}

    def _row_to_dict(self, row: dict) -> dict:
        cost = self._prefix_dict("cost_", self.parser.parse_cost(row["cost"])[0])
        text = self.parser.parse_text(row["text"]).format(**row)
        channel_cost_element = f"<span class='mana {cost['cost_color_classes']}'><div class='mana-background {cost['cost_color_classes']}'></div><span class='mana-value'>1</span></span>"
        return {**row, **cost, "text": text, "channel_cost_element": channel_cost_element}

    def construct_cards(self, cards: list[dict]):
        return [self._row_to_dict(card) for card in cards]


if __name__ == "__main__":
    parser = Parser()
    card_constructor = CardConstructor(parser)

    print(
        card_constructor._row_to_dict(
            {"name": "A custom name", "text": "~|other text", "cost": "(2AD)", "tags": "Beast Human AnotherTag"}
        )
    )
