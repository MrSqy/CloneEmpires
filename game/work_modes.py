"""Kaynak binalarında köylü çalışma modları (Social Empires tarzı zamanlı üretim).

Köylü(ler) bir kaynak binasına atanır, bir mod seçilir, mücevher maliyeti
peşin ödenir ve süre dolunca kaynak + bir miktar mücevher kazanılır.
"""
import math

# mode_key -> (etiket, dakika, taban kaynak kazancı)
WORK_MODES = {
    "fast":     dict(label="Hızlı",   minutes=2,  base=10),
    "normal":   dict(label="Normal",  minutes=5,  base=30),
    "long":     dict(label="Uzun",    minutes=10, base=75),
    "marathon": dict(label="Maraton", minutes=30, base=250),
}

MODE_ORDER = ["fast", "normal", "long", "marathon"]

# Atanan köylü sayısına göre kazanç çarpanı
WORKER_MULTIPLIER = {1: 1.0, 2: 1.25, 3: 1.5, 4: 2.0}
MAX_WORKERS = 4


def gem_cost(mode_key: str) -> int:
    """Modu başlatmak için gereken mücevher: dakika × 10."""
    mode = WORK_MODES[mode_key]
    return mode["minutes"] * 10


def duration_seconds(mode_key: str) -> float:
    return WORK_MODES[mode_key]["minutes"] * 60.0


def worker_multiplier(worker_count: int) -> float:
    n = max(1, min(worker_count, MAX_WORKERS))
    return WORKER_MULTIPLIER[n]


def resource_gain(mode_key: str, worker_count: int) -> int:
    base = WORK_MODES[mode_key]["base"]
    return math.ceil(base * worker_multiplier(worker_count))


def gem_reward(resource_amount: int) -> int:
    """Kazanılan kaynağın 5'e bölünmüş tavanı kadar mücevher."""
    return math.ceil(resource_amount / 5)
