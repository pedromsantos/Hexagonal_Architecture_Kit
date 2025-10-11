"""Basic test to ensure CI pipeline works."""


def test_true_equals_true() -> None:
    """Test that true equals true."""
    result = True
    assert result


def test_basic_math() -> None:
    """Test basic math operations."""
    result = 2 + 2
    expected = 4
    assert result == expected


def test_string_operations() -> None:
    """Test string operations."""
    name = "katacombs"
    greeting = f"Hello, {name}!"
    assert len(greeting) > 0
    assert "katacombs" in greeting
