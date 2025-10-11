"""Basic test to ensure CI pipeline works."""


def test() -> None:
    """The Test."""
    name = "katacombs"
    greeting = f"Hello, {name}!"
    assert len(greeting) > 0
    assert "katacombs" in greeting
