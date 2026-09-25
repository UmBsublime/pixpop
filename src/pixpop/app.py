"""Main application module for pixpop."""

from textual.app import App, ComposeResult
from textual.theme import Theme
from textual.widgets import Footer, Header

from pixpop.config import AppConfig, load_config
from pixpop.workspace import PaintWorkspace


class PixPop(App[None]):
    """A simple paint application with drawing and erasing functionality."""

    CSS_PATH = "styles/main.tcss"

    # Base window title; workspace_io composes project names onto this.
    base_title = "Pixpop"

    def __init__(self, config: AppConfig | None = None) -> None:
        super().__init__()
        self._config = config if config is not None else load_config()

    def compose(self) -> ComposeResult:
        """Create the main application layout with tabs."""
        yield Header(show_clock=True)
        yield PaintWorkspace(config=self._config)
        yield Footer()

    def on_mount(self) -> None:
        self.title = self.base_title
        self.register_theme(
            Theme(
                name="twilight-bog",
                primary="#5d8da2",
                secondary="#89baab",
                accent="#a48db6",
                warning="#727546",
                error="#a66470",
                success="#b8cfb9",
                foreground="#e1e6ea",
                background="#1f1714",
                surface="#343943",
                panel="#4e5a6d",
            )
        )
        self.theme = self._config.theme_name


def main() -> None:
    """Entry point for the pixpop TUI application."""
    app = PixPop()
    app.run()


if __name__ == "__main__":
    main()
