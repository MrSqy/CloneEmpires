"""Izgara (cell-decomposition) yardımcıları.

Kutsal kural: her karakter daima bir hücre merkezinde oturur ve hareket eden
karakter bir adımı başka bir hücrenin merkezinde sonlandırır. Menzil hücre
merkezleri arası öklid mesafenin yuvarlanmış (round) hâliyle ölçülür:

    menzilde mi? = round(euclid) <= range

Örnek: 1 menzilli birim çevresindeki 3x3 kareyi tamamen vurur (köşe 1.41→1),
2 menzilli birim 5x5'in köşelerini vuramaz (2.83→3).
"""

import math
import heapq

# 8 yönlü komşular
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
_SQRT2 = math.sqrt(2)


def cell_of(x, y):
    """Sürekli (x, y) konumunu içinde bulunduğu hücreye yuvarlar."""
    return (int(round(x)), int(round(y)))


def cell_distance(a, b):
    """İki hücre merkezi arası yuvarlanmış öklid mesafe (menzil birimi)."""
    return int(round(math.hypot(a[0] - b[0], a[1] - b[1])))


def in_range(a, b, rng):
    """a ve b hücreleri arasında round(euclid) <= rng ise True."""
    return cell_distance(a, b) <= rng


def find_path(start, goal, blocked, max_nodes=8000):
    """start hücresinden goal hücresine A* yolu (8 yönlü, köşe kesmez).

    blocked: callable(cell) -> bool. Engelli/sınır dışı hücreler için True döner.
    Dönüş: start'tan sonraki hücrelerden goal'e kadar liste; yol yoksa [].
    start ve goal'ün engelsiz olduğu varsayılır (çağıran snap'ler).
    """
    if start == goal:
        return []
    open_heap = [(0.0, start)]
    came = {}
    g = {start: 0.0}
    nodes = 0
    while open_heap and nodes < max_nodes:
        _, cur = heapq.heappop(open_heap)
        if cur == goal:
            path = []
            while cur in came:
                path.append(cur)
                cur = came[cur]
            path.reverse()
            return path
        nodes += 1
        cx, cy = cur
        for dx, dy in _DIRS:
            ncell = (cx + dx, cy + dy)
            if blocked(ncell):
                continue
            if dx != 0 and dy != 0:
                # çapraz adımda köşe kesmeyi engelle
                if blocked((cx + dx, cy)) and blocked((cx, cy + dy)):
                    continue
                step = _SQRT2
            else:
                step = 1.0
            ng = g[cur] + step
            if ncell not in g or ng < g[ncell]:
                g[ncell] = ng
                came[ncell] = cur
                f = ng + math.hypot(ncell[0] - goal[0], ncell[1] - goal[1])
                heapq.heappush(open_heap, (f, ncell))
    return []
