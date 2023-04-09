from lib.types import KeywordDefinition

KEYWORDS = {
    "blocker": KeywordDefinition(
        "blocker",
        "🛡️ Blocker",
        "<<tap>> -> Change the target of an enemy attack from an adjacent creature or you to this creature.",
    ),
    "tribute": KeywordDefinition(
        "tribute",
        "Tribute - {args[0]}",
        "To cast this spell you must pay its tribute cost in addition to its normal costs.",
    ),
    "harvest": KeywordDefinition("harvest", "Harvest - {args[0]}", "Get this effect when used as an Ingredient."),
    "first": KeywordDefinition("first", "First {args[0]}", "And the reminder uses the second {args[1]}"),
}
