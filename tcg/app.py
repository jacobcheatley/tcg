from flask import Flask, render_template
from sassutils.wsgi import Manifest, SassMiddleware

from tcg.lib.services import CardPipeline, GoogleSheetsReader
from tcg.lib.types import KeywordDefinition


def card_data():
    sheet_reader = GoogleSheetsReader("1qmsOTAWI75Hs6wtkR6oK58nxVS0uEjHigd1mwyo7714")
    keywords_df = sheet_reader.read("keywords")
    keyword_definitions = KeywordDefinition.list_from_dataframe(keywords_df)
    cards = sheet_reader.read("cards")
    card_data = cards.to_dict(orient="records")
    pipeline = CardPipeline(keyword_definitions=keyword_definitions)
    return pipeline.run_multiple(card_data)


app = Flask(__name__)
app.wsgi_app = SassMiddleware(
    app.wsgi_app,
    {"tcg": Manifest(sass_path="static/sass", css_path="static/css", wsgi_path="/static/css", strip_extension=True)},
)


@app.route("/")
def index():
    return render_template("index.html", card_data=card_data())


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
