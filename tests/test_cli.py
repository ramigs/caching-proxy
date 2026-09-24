from unittest.mock import AsyncMock, Mock

from typer.testing import CliRunner

from caching_proxy.cli import app

runner = CliRunner()


def test_port_and_origin_starts_the_server(monkeypatch):
    mock_run_server = Mock()
    monkeypatch.setattr("caching_proxy.cli.run_server", mock_run_server)

    result = runner.invoke(app, ["--port", "3000", "--origin", "https://dummyjson.com"])

    assert result.exit_code == 0
    mock_run_server.assert_called_once_with(port=3000, origin="https://dummyjson.com")


def test_port_and_origin_are_read_from_environment(monkeypatch):
    mock_run_server = Mock()
    monkeypatch.setattr("caching_proxy.cli.run_server", mock_run_server)

    result = runner.invoke(
        app, [], env={"PORT": "3000", "ORIGIN": "https://dummyjson.com"}
    )

    assert result.exit_code == 0
    mock_run_server.assert_called_once_with(port=3000, origin="https://dummyjson.com")


def test_clear_cache_flag_clears_the_cache(monkeypatch):
    mock_clear_cache = AsyncMock()
    monkeypatch.setattr("caching_proxy.cli.clear_cache", mock_clear_cache)

    result = runner.invoke(app, ["--clear-cache"])

    assert result.exit_code == 0
    mock_clear_cache.assert_called_once()
    assert "Cache cleared." in result.stdout


def test_missing_arguments_prints_usage_message():
    result = runner.invoke(app, [], env={"PORT": None, "ORIGIN": None})

    assert result.exit_code == 0
    assert "Provide --port and --origin, or --clear-cache." in result.stdout
