import pytest

@pytest.fixture
def dummy_surface():
    import pygame
    pygame.init()
    return pygame.Surface((64, 32))
