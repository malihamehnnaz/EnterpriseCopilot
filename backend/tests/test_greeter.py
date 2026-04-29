import pytest
from backend.app.agents.greeter import greet

def test_greet():
    """
    Test the greet function.
    """
    name = "Test User"
    expected_greeting = f"Hello, {name}! Welcome to the Enterprise Copilot."
    assert greet(name) == expected_greeting

def test_greet_with_empty_name():
    """
    Test the greet function with an empty name.
    """
    name = ""
    expected_greeting = f"Hello, {name}! Welcome to the Enterprise Copilot."
    assert greet(name) == expected_greeting
