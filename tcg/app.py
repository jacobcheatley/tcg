from flask import Flask, render_template
from lib.services import CardConstructor, Parser
from sassutils.wsgi import Manifest, SassMiddleware

app = Flask(__name__)
app.wsgi_app = SassMiddleware(
    app.wsgi_app,
    {"tcg": Manifest(sass_path="static/sass", css_path="static/css", wsgi_path="/static/css", strip_extension=True)},
)

card_data = CardConstructor(Parser()).construct_cards(
    [
        {"name": "A custom name", "text": "~|other text", "cost": "(2DA)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2DO)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2DP)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2DL)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2AO)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2AP)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2AL)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2OP)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2OL)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2PL)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2D)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2A)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2O)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2P)", "tags": "Beast Human AnotherTag"},
        {"name": "A custom name", "text": "~|other text", "cost": "(2L)", "tags": "Beast Human AnotherTag"},
    ]
)


@app.route("/")
def index():
    return render_template("index.html", card_data=card_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
