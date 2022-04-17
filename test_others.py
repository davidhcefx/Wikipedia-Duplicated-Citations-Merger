#from typing import List, Tuple, Pattern
import builtins
import wikipedia_duplicated_citations_merger as merger
import pytest


# Testing menu

def test_menu_prompt(monkeypatch, capfd):
    """Prompt should be displayed to the user."""
    monkeypatch.setattr(builtins, 'input', lambda _: '1')
    prompt = 'prompt'
    merger.menu(prompt, 2, ['opt1', 'opt2', 'opt3'])
    assert prompt in capfd.readouterr().out.split('\n')

def test_menu_default(monkeypatch):
    """Default option"""
    monkeypatch.setattr(builtins, 'input', lambda _: '')
    ch = merger.menu('prompt', 2, ['opt1', 'opt2', 'opt3'])
    assert ch == 2

def test_menu_normal(monkeypatch):
    """Normal choice"""
    monkeypatch.setattr(builtins, 'input', lambda _: '1')
    ch = merger.menu('prompt', 2, ['opt1', 'opt2', 'opt3'])
    assert ch == 1

def test_menu_invalid(monkeypatch):
    """Invalid choice"""
    monkeypatch.setattr(builtins, 'input', lambda _: '4')
    with pytest.raises(SystemExit):
        _ = merger.menu('prompt', 2, ['opt1', 'opt2', 'opt3'])
