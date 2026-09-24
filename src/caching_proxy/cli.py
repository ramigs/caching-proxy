import asyncio

import typer

from caching_proxy.db.engine import get_engine
from caching_proxy.db.queries import clear
from caching_proxy.server import run_server

app = typer.Typer()


async def clear_cache() -> None:
    engine = get_engine()
    async with engine.connect() as connection:
        await clear(connection)


@app.command()
def main_command(
    port: int = typer.Option(None, "--port", envvar="PORT"),
    origin: str = typer.Option(None, "--origin", envvar="ORIGIN"),
    clear_cache_flag: bool = typer.Option(False, "--clear-cache"),
):
    if clear_cache_flag:
        asyncio.run(clear_cache())
        typer.echo("Cache cleared.")
        return
    if port and origin:
        run_server(port=port, origin=origin)
    else:
        typer.echo("Provide --port and --origin, or --clear-cache.")


def main():
    app()
