import typer

# from my_app.server import run_server
# from my_app.cache import Cache

app = typer.Typer()


@app.command()
def main_command(
    port: int = typer.Option(None, "--port"),
    origin: str = typer.Option(None, "--origin"),
    clear_cache: bool = typer.Option(False, "--clear-cache"),
):
    if clear_cache:
        # Cache().clear()
        typer.echo("Cache cleared.")
        return
    if port and origin:
        typer.echo("port and origin.")
        # run_server(port=port, origin=origin)
    else:
        typer.echo("Provide --port and --origin, or --clear-cache.")


def main():
    app()
