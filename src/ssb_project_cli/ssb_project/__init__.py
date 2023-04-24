"""ssb-project package."""
from questionary import Style


prompt_autocomplete_style = Style(
    [
        ("answer", "fg:#000000 bold"),  # submitted answer text behind the question
        ("selected", "fg:#FFFFFF"),  # style for a selected item
    ]
)
