from lib.types import KeywordDefinition

KEYWORDS = [
    KeywordDefinition(
        "blocker",
        "🛡️ Blocker",
        "<<tap>> Change the target of an enemy attack from an adjacent creature or you to this creature.",
    ),
    KeywordDefinition(
        "tribute",
        "Tribute - {arg0}",
        "To cast this spell you must pay its tribute cost in addition to its normal costs.",
    ),
    KeywordDefinition("harvest", "Harvest - {arg0}", "Get this effect when used as an Ingredient."),
    KeywordDefinition("first", "First {arg0}", "And the reminder uses the second {arg1}"),
    KeywordDefinition("complicated", "Complicated {arg0}", "{cost__names} ~"),
]
