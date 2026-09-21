"""Sürümlü dünya kayıtları, doğrulama ve atomik dosya/yedek yazımı."""
import copy
import json
import math
import os
import re
import tempfile
import time
from collections import deque
from dataclasses import asdict
from pathlib import Path

from game.world import World
from game.economy import EconomyEngine
from game.entities.unit import Unit
from game.entities.worker import Worker
from game.entities.building import Building
from game.entities.resource import ResourceNode
from game.entities.projectile import Projectile
from game.models import UnitStats, BuildingStats
from game.production_queue import ProductionQueue, UNIT_COSTS, UNIT_TRAIN_TIME, MAX_QUEUE_SIZE
from game.building_catalog import CATALOG
from game.unit_stats import BASE_STATS
from game.constants import RESOURCES, INITIAL_STORAGE, STORAGE_PER_LEVEL, MIN_ZOOM, MAX_ZOOM
from game.work_modes import WORK_MODES, MAX_WORKERS

VERSION = 1
UNIT_FIELDS = ('level', 'is_player', 'attack_cooldown', 'manual_override', 'path',
               'target_pos', 'move_goal', 'repath_timer', 'movement_error')
BUILDING_FIELDS = ('building_type', 'cost', 'production_timer', 'production_processed',
                   'is_producing', 'construction_progress', 'is_constructed', 'build_time',
                   'worker_mode', 'pending_worker_mode', 'worker_timer', 'worker_active',
                   'attack_cooldown', 'tower_disabled')
RESOURCE_FIELDS = ('resource_type', 'amount', 'max_amount', 'respawn_time',
                   'regrowth_timer', 'regrowth_phase')
WORKER_FIELDS = ('gather_timer', 'task')
PROJECTILE_FIELDS = ('speed', 'damage', 'is_player')


class SaveError(ValueError):
    """Kullanıcıya gösterilebilen kayıt biçimi/veri hatası."""


class LegacySaveError(SaveError):
    """Bilgi kaybı olmadan aktarılamayan eski kayıt biçimi."""


def _number(value, label, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SaveError(f'{label}: geçersiz sayı.')
    if minimum is not None and value < minimum:
        raise SaveError(f'{label}: değer çok küçük.')
    return value


def _integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise SaveError(f'{label}: geçersiz tam sayı.')
    return value


def _id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{32}', value):
        raise SaveError('Geçersiz kayıt/nesne kimliği.')
    return value


def _text(value, label, limit=80):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise SaveError(f'{label}: geçersiz metin.')
    return value


def _point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise SaveError('Geçersiz konum.')
    return tuple(_number(v, 'Konum') for v in value)


def _resources(value, full=False):
    if not isinstance(value, dict) or set(value) - set(RESOURCES):
        raise SaveError('Geçersiz kaynak türleri.')
    if full and set(value) != set(RESOURCES):
        raise SaveError('Eksik kaynak verisi.')
    return {k: _integer(v, k) for k, v in value.items()}


def _restore_fields(entity, data, names):
    """Yalnız bildirilen alanları doğrular; keyfi nesne niteliği kabul etmez."""
    if not isinstance(data, dict) or set(data) != set(names):
        raise SaveError('Nesne alanları eksik veya bilinmiyor.')
    for name in names:
        value = data[name]
        original = getattr(entity, name)
        if name in ('target_pos', 'move_goal'):
            value = None if value is None else _point(value)
        elif name == 'path':
            if not isinstance(value, list):
                raise SaveError('Geçersiz yol.')
            value = [_point(point) for point in value]
        elif name == 'cost':
            value = _resources(value)
        elif name in ('worker_mode', 'pending_worker_mode'):
            if value is not None and value not in WORK_MODES:
                raise SaveError('Bilinmeyen çalışma modu.')
        elif name == 'task':
            if value not in (None, 'gather', 'build', 'working'):
                raise SaveError('Bilinmeyen köylü görevi.')
        elif type(original) is bool:
            if type(value) is not bool:
                raise SaveError('Geçersiz durum bayrağı.')
        elif isinstance(original, (int, float)):
            _number(value, name, None if name == 'attack_cooldown' else 0)
            if name in ("level", "production_processed", "regrowth_phase"):
                _integer(value, name)
        elif isinstance(original, str):
            if not isinstance(value, str) or len(value) > 200:
                raise SaveError('Geçersiz nesne metni.')
        setattr(entity, name, copy.deepcopy(value))


def _stats(entity, values):
    prototype = UnitStats() if isinstance(entity, Unit) else BuildingStats()
    if not isinstance(values, dict) or set(values) != set(asdict(prototype)):
        raise SaveError('Eksik istatistik.')
    for key, value in values.items():
        _number(value, key, 0)
    if values['hp'] > values['max_hp'] or values['attack_speed'] <= 0:
        raise SaveError('Tutarsız can/saldırı hızı.')
    if isinstance(entity, Unit) and values['move_speed'] <= 0:
        raise SaveError('Geçersiz hareket hızı.')
    if isinstance(entity, Building):
        _integer(values['level'], 'Bina seviyesi', 1)
        _integer(values['max_level'], 'Azami seviye', 1)
    entity.stats = type(prototype)(**values)


def _queue(building, economy, value):
    if not isinstance(value, dict) or set(value) != {'current', 'queued', 'progress', 'max_progress'}:
        raise SaveError('Eksik kuyruk verisi.')
    queued = value['queued']
    if not isinstance(queued, list) or len(queued) + bool(value['current']) > MAX_QUEUE_SIZE:
        raise SaveError('Geçersiz kuyruk uzunluğu.')
    items = queued + ([value['current']] if value['current'] is not None else [])
    for item in items:
        if not isinstance(item, dict) or set(item) != {'unit_type', 'level', 'cost', 'train_time'}:
            raise SaveError('Geçersiz sipariş.')
        if item['unit_type'] not in UNIT_COSTS:
            raise SaveError('Bilinmeyen sipariş türü.')
        _integer(item['level'], 'Sipariş seviyesi', 1)
        _resources(item['cost'])
        if _number(item['train_time'], 'Üretim süresi') != UNIT_TRAIN_TIME[item['unit_type']]:
            raise SaveError('Geçersiz sipariş süresi.')
    progress = _number(value['progress'], 'İlerleme', 0)
    maximum = _number(value['max_progress'], 'Üretim süresi', 0)
    if progress > maximum or (value['current'] and maximum != value['current']['train_time']):
        raise SaveError('Tutarsız üretim ilerlemesi.')
    if value['current'] is None and (progress or maximum):
        raise SaveError('Siparişsiz üretim ilerlemesi.')
    queue = ProductionQueue(building, economy)
    queue.current_production = copy.deepcopy(value['current'])
    queue.queue = deque(copy.deepcopy(queued))
    queue.progress, queue.max_progress = progress, maximum
    return queue


class SaveManager:
    SAVE_DIR = Path(__file__).resolve().parent.parent / 'saves'

    def __init__(self, save_dir=None):
        self.save_dir = Path(save_dir if save_dir is not None else self.SAVE_DIR)
        try:
            self.save_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Ana menü açılabilsin; gerçek yazma denemesi hatayı kullanıcıya iletir.
            pass

    def serialize(self, world, economy, king_name, level, xp=0, *, camera=None, xp_state=None, saved_at=None):
        """Bağımsız JSON verisi üretir; nesne ilişkilerini kimliklerle yazar."""
        ids = {e.entity_id for e in world.entities}
        def ref(entity):
            return entity.entity_id if entity is not None and entity.entity_id in ids else None
        entities = []
        for entity in world.entities:
            row = {'id': entity.entity_id, 'name': entity.name, 'x': entity.x, 'y': entity.y,
                   'alive': entity.is_alive(), 'refs': {}}
            if isinstance(entity, Unit):
                row.update(type='worker' if isinstance(entity, Worker) else 'unit', unit_type=entity.unit_type,
                           stats=asdict(entity.stats), state=entity.state_machine.current)
                names = UNIT_FIELDS + (WORKER_FIELDS if isinstance(entity, Worker) else ())
                row['refs'] = {key: ref(getattr(entity, key)) for key in ('target', 'last_attacker')}
                if isinstance(entity, Worker):
                    row['refs'].update(task_target=ref(entity.task_target), is_inside_building=ref(entity.is_inside_building))
            elif isinstance(entity, Building):
                row.update(type='building', stats=asdict(entity.stats))
                names = BUILDING_FIELDS
                row['workers'] = [ref(w) for w in entity.assigned_workers if ref(w)]
                row['queue'] = entity.production_queue.get_queue_status() if hasattr(entity, 'production_queue') else None
            elif isinstance(entity, ResourceNode):
                row['type'], names = 'resource', RESOURCE_FIELDS
            elif isinstance(entity, Projectile):
                row['type'], names = 'projectile', PROJECTILE_FIELDS
                row['refs'] = {'target': ref(entity.target), 'source': ref(entity.source)}
            else:
                raise SaveError('Bilinmeyen oyun nesnesi.')
            row['fields'] = {name: getattr(entity, name) for name in names}
            entities.append(row)
        max_xp = 100
        if not 1 <= _integer(level, 'Seviye', 1) <= 1000:
            raise SaveError('Desteklenen seviye aralığı dışında.')
        for _ in range(level - 1):
            max_xp = int(max_xp * 1.5)
        stamp = max(world.processed_at, time.time() if saved_at is None else saved_at)
        data = {'version': VERSION, 'world_id': world.world_id, 'world_name': world.name,
                'created_at': world.created_at, 'processed_at': stamp,
                'king_name': king_name, 'townhall_level': level, 'xp': xp,
                'xp_state': xp_state or {'level': level, 'xp': xp, 'max_xp': max_xp,
                                         'xp_multiplier': 1 + (level - 1) * .05},
                'resources': economy.resources, 'storage_level': economy.storage_level,
                'camera': camera or {'x': 0, 'y': 0, 'zoom': 1}, 'entities': entities}
        return copy.deepcopy(data)

    def restore(self, data):
        """Veriyi yeni dünyada doğrular ve kurar; canlı oturuma dokunmaz."""
        try:
            return self._restore(data)
        except SaveError:
            raise
        except (KeyError, TypeError, ValueError, OverflowError, AttributeError) as exc:
            raise SaveError(f'Kayıt verisi eksik veya bozuk: {exc}') from exc

    def _restore(self, data):
        if not isinstance(data, dict):
            raise SaveError('Kayıt bir JSON nesnesi olmalı.')
        if 'version' not in data:
            raise LegacySaveError('Eski sürüm kaydı: dosya korundu, otomatik aktarım desteklenmiyor.')
        if type(data['version']) is not int or data['version'] != VERSION:
            raise SaveError('Desteklenmeyen kayıt sürümü.')
        world, economy = World(), EconomyEngine()
        world.world_id = _id(data['world_id'])
        world.name = _text(data['world_name'], 'Dünya adı', 40)
        world.created_at = _number(data['created_at'], 'Oluşturma zamanı', 0)
        world.processed_at = _number(data['processed_at'], 'İşlenen zaman', world.created_at)
        economy.resources = _resources(data['resources'], full=True)
        economy.storage_level = _integer(data['storage_level'], 'Depo seviyesi')
        economy.storage_limit = INITIAL_STORAGE + economy.storage_level * STORAGE_PER_LEVEL
        if any(n > economy.storage_limit for n in economy.resources.values()):
            raise SaveError('Depo kapasitesi aşılmış.')
        xp = data['xp_state']
        if not isinstance(xp, dict) or set(xp) != {'level', 'xp', 'max_xp', 'xp_multiplier'}:
            raise SaveError('Eksik deneyim durumu.')
        if _integer(xp['level'], 'Seviye', 1) > 1000:
            raise SaveError('Desteklenen seviye aralığı dışında.')
        _integer(xp['max_xp'], 'Seviye eşiği', 1)
        _integer(xp['xp'], 'Deneyim')
        _number(xp['xp_multiplier'], 'Deneyim çarpanı', 1)
        if xp['xp'] >= xp['max_xp'] or xp['level'] != data['townhall_level'] or xp['xp'] != data['xp']:
            raise SaveError('Tutarsız deneyim durumu.')
        _text(data['king_name'], 'Oyuncu adı')
        camera = data['camera']
        if not isinstance(camera, dict) or set(camera) != {'x', 'y', 'zoom'}:
            raise SaveError('Eksik kamera verisi.')
        for key in camera:
            _number(camera[key], key)
        if not MIN_ZOOM <= camera['zoom'] <= MAX_ZOOM:
            raise SaveError('Geçersiz yakınlaştırma.')
        rows = data['entities']
        if not isinstance(rows, list):
            raise SaveError('Nesne listesi eksik.')
        by_id = {}
        for row in rows:
            eid = _id(row['id'])
            if eid in by_id:
                raise SaveError('Tekrarlanan nesne kimliği.')
            x, y = _point((row['x'], row['y']))
            if not (0 <= x < world.width and 0 <= y < world.height):
                raise SaveError('Nesne harita dışında.')
            kind, fields = row['type'], row['fields']
            if kind in ('unit', 'worker'):
                if row['unit_type'] not in BASE_STATS or (kind == 'worker') != (row['unit_type'] == 'worker'):
                    raise SaveError('Geçersiz birim alt türü.')
                level = _integer(fields['level'], 'Birim seviyesi', 1)
                entity = Worker(x, y, level) if kind == 'worker' else Unit(row['unit_type'], x, y, level)
                _restore_fields(entity, fields, UNIT_FIELDS + (WORKER_FIELDS if kind == 'worker' else ()))
                if any(px != int(px) or py != int(py)
                       or not (0 <= px < world.width and 0 <= py < world.height)
                       for px, py in entity.path):
                    raise SaveError('Yol harita içindeki hücre merkezlerinden oluşmalı.')
                if row['state'] not in entity.state_machine.valid_transitions:
                    raise SaveError('Geçersiz birim durumu.')
                entity.state_machine.current = row['state']
                _stats(entity, row['stats'])
                if (not row['alive']) != (row['state'] == 'DEAD') or (row['alive'] and entity.stats.hp <= 0):
                    raise SaveError('Tutarsız birim canlılığı.')
            elif kind == 'building':
                if fields['building_type'] not in set(CATALOG) | {'townhall', 'barracks', 'storage'}:
                    raise SaveError('Bilinmeyen bina.')
                entity = Building(fields['building_type'], x, y)
                _restore_fields(entity, fields, BUILDING_FIELDS)
                _stats(entity, row['stats'])
                if entity.build_time <= 0 or not 0 <= entity.construction_progress <= 100:
                    raise SaveError('Geçersiz inşaat süresi/ilerlemesi.')
                if entity.worker_active and (not entity.worker_mode or entity.worker_timer <= 0):
                    raise SaveError('Tutarsız çalışma süresi.')
                if row['queue'] is not None:
                    entity.production_queue = _queue(entity, economy, row['queue'])
            elif kind == 'resource':
                if fields['resource_type'] not in RESOURCES:
                    raise SaveError('Bilinmeyen doğal kaynak.')
                entity = ResourceNode(fields['resource_type'], x, y, fields['max_amount'])
                _restore_fields(entity, fields, RESOURCE_FIELDS)
                if entity.max_amount <= 0 or entity.amount > entity.max_amount or entity.respawn_time <= 0:
                    raise SaveError('Tutarsız doğal kaynak miktarı/süresi.')
                if entity.regrowth_phase not in (0, 1, 2):
                    raise SaveError('Geçersiz yenilenme aşaması.')
            elif kind == 'projectile':
                entity = Projectile(x, y, None)
                _restore_fields(entity, fields, PROJECTILE_FIELDS)
                if entity.speed <= 0:
                    raise SaveError('Geçersiz mermi hızı.')
            else:
                raise SaveError('Bilinmeyen nesne türü.')
            if type(row['alive']) is not bool:
                raise SaveError('Geçersiz canlılık.')
            entity.entity_id, entity.name = eid, _text(row['name'], 'Nesne adı')
            entity.state.alive = row['alive']
            world.add_entity(entity)
            by_id[eid] = entity
        for row in rows:
            entity = by_id[row['id']]
            expected = ({'target', 'last_attacker', 'task_target', 'is_inside_building'} if isinstance(entity, Worker)
                        else {'target', 'last_attacker'} if isinstance(entity, Unit)
                        else {'target', 'source'} if isinstance(entity, Projectile) else set())
            if not isinstance(row['refs'], dict) or set(row['refs']) != expected:
                raise SaveError('Eksik nesne bağlantısı.')
            for name, eid in row['refs'].items():
                if eid is not None and eid not in by_id:
                    raise SaveError('Bulunamayan hedef bağlantısı.')
                linked = by_id.get(eid)
                if name in ('target', 'last_attacker', 'source') and linked is not None and not isinstance(linked, (Unit, Building)):
                    raise SaveError('Geçersiz savaş hedefi.')
                if name == 'task_target' and linked is not None and not isinstance(linked, (Building, ResourceNode)):
                    raise SaveError('Geçersiz köylü hedefi.')
                if name == 'is_inside_building' and linked is not None and not isinstance(linked, Building):
                    raise SaveError('Geçersiz bina bağlantısı.')
                setattr(entity, name, linked)
            if isinstance(entity, Building):
                workers = row['workers']
                if not isinstance(workers, list) or len(set(workers)) != len(workers) or len(workers) > MAX_WORKERS:
                    raise SaveError('Geçersiz köylü listesi.')
                entity.assigned_workers = [by_id[eid] for eid in workers]
                if any(not isinstance(w, Worker) for w in entity.assigned_workers):
                    raise SaveError('Binaya köylü olmayan nesne atanmış.')
        for entity in world.entities:
            if isinstance(entity, Building):
                if entity.assigned_workers and entity.resource_type() is None:
                    raise SaveError('Bu bina köylü çalıştıramaz.')
                if entity.worker_active and not entity.assigned_workers:
                    raise SaveError('Köylüsüz aktif üretim.')
                for worker in entity.assigned_workers:
                    if worker.is_inside_building is not entity or worker.task_target is not entity or worker.task != 'working':
                        raise SaveError('Tutarsız köylü ataması.')
            if isinstance(entity, Worker) and entity.is_inside_building:
                if entity not in entity.is_inside_building.assigned_workers:
                    raise SaveError('Tek taraflı köylü ataması.')
        return world, economy, copy.deepcopy({'camera': camera, 'xp_state': xp, 'king_name': data['king_name']})

    def deserialize(self, data, world, economy):
        """Eski çağrı API'si: doğrulamadan sonra hedef dünyayı tamamen değiştirir."""
        restored, eco, metadata = self.restore(data)
        world.__dict__.update(restored.__dict__)
        economy.__dict__.update(eco.__dict__)
        for entity in world.entities:
            entity.world = world
            if hasattr(entity, 'production_queue'):
                entity.production_queue.economy = economy
        return metadata

    def _path(self, filename):
        if not isinstance(filename, str) or Path(filename).name != filename or filename in ('.', '..'):
            raise SaveError('Geçersiz kayıt dosyası adı.')
        return self.save_dir / filename

    def _atomic_write(self, path, payload):
        """Dosyayı aynı dizinde hazırlar; tamamlanmadan asıl dosyaya dokunmaz."""
        temporary = None
        try:
            self.save_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.save_dir, prefix='.save-', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def save_to_file(self, filename, data):
        self.restore(data)  # Geçersiz durum sağlam kaydın üstüne yazılamaz.
        payload = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8')
        path = self._path(filename)
        if path.exists():
            try:
                previous = path.read_bytes()
                self.restore(json.loads(previous))
            except (ValueError, UnicodeError):
                pass  # Bozuk ana dosya sağlam yedeği ezmesin.
            else:
                self._atomic_write(path.with_name(path.name + '.bak'), previous)
        self._atomic_write(path, payload)

    def save_world(self, data):
        self.save_to_file(_id(data['world_id']) + '.json', data)

    def load_from_file(self, filename):
        try:
            data = json.loads(self._path(filename).read_text(encoding='utf-8'))
        except (ValueError, UnicodeError) as exc:
            raise SaveError('Kayıt dosyası okunamadı: bozuk JSON.') from exc
        self.restore(data)
        return data

    def list_worlds(self):
        """Bozuk/eski kayıtları da görünür tutar; bir dosya diğerlerini engellemez."""
        records = []
        for path in self.save_dir.glob('*.json'):
            record = {'filename': path.name, 'name': path.stem, 'level': None, 'saved_at': 0,
                      'error': '', 'backup': False}
            try:
                data = self.load_from_file(path.name)
                if path.stem != data['world_id']:
                    raise SaveError('Kayıt adı ile dünya kimliği uyuşmuyor.')
                record.update(name=data['world_name'], level=data['townhall_level'], saved_at=data['processed_at'])
            except (OSError, SaveError) as exc:
                record['error'] = str(exc)
            backup = path.with_name(path.name + '.bak')
            if backup.exists():
                try:
                    data = self.load_from_file(backup.name)
                    record['backup'] = data['world_id'] == path.stem
                except (OSError, SaveError):
                    pass
            records.append(record)
        return sorted(records, key=lambda r: r['saved_at'], reverse=True)
