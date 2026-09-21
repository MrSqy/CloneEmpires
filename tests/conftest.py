import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

@pytest.fixture
def dummy_surface():
    import pygame
    pygame.init()
    return pygame.Surface((64, 32))


@pytest.fixture(autouse=True)
def isolated_saves(tmp_path, monkeypatch):
    """Testlerin gerçek oyun kayıtlarına erişmesini önler."""
    from game.save_load import SaveManager
    monkeypatch.setattr(SaveManager, 'SAVE_DIR', tmp_path / 'saves')
