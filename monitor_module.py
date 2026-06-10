"""
DAU Dashboard - Sistem Monitorinq Modulu
CPU, RAM, GPU, VRAM, Disk real-time izləmə
psutil ilə real göstəricilər
WebSocket ilə canlı yenilənmə
Raw SQLite database.py funksiyaları ilə işləyir
"""

import os
import json
import time
import importlib
from datetime import datetime, timedelta

import database as db


class MonitorModule:
    """Sistem Monitorinq - Real-time resurs izləmə"""

    def __init__(self):
        self.psutil = None
        self._try_import_psutil()
        self._last_save_time = 0

    def _try_import_psutil(self):
        """psutil kitabxanasını import etməyə çalışır"""
        try:
            self.psutil = importlib.import_module('psutil')
        except Exception:
            self.psutil = None

    # ============================================
    # CPU MƏLUMATLARI
    # ============================================

    def get_cpu_info(self):
        """CPU məlumatlarını qaytarır"""
        if not self.psutil:
            return {'error': 'psutil quraşdırılmayıb. pip install psutil ilə quraşdırın.'}

        try:
            cpu_percent = self.psutil.cpu_percent(interval=0.5)
            cpu_percent_per_cpu = self.psutil.cpu_percent(interval=0.3, percpu=True)
            cpu_count_logical = self.psutil.cpu_count(logical=True)
            cpu_count_physical = self.psutil.cpu_count(logical=False)
            cpu_freq = self.psutil.cpu_freq()

            cpu_times = self.psutil.cpu_times()
            total_time = cpu_times.user + cpu_times.system + cpu_times.idle
            user_pct = round((cpu_times.user / total_time) * 100, 1) if total_time > 0 else 0
            system_pct = round((cpu_times.system / total_time) * 100, 1) if total_time > 0 else 0
            idle_pct = round((cpu_times.idle / total_time) * 100, 1) if total_time > 0 else 0

            load_avg = self.psutil.getloadavg() if hasattr(self.psutil, 'getloadavg') else (0, 0, 0)

            return {
                'percent': cpu_percent,
                'percent_per_cpu': cpu_percent_per_cpu,
                'count_logical': cpu_count_logical,
                'count_physical': cpu_count_physical,
                'freq_current': round(cpu_freq.current, 0) if cpu_freq else 0,
                'freq_min': round(cpu_freq.min, 0) if cpu_freq and cpu_freq.min else 0,
                'freq_max': round(cpu_freq.max, 0) if cpu_freq and cpu_freq.max else 0,
                'user_percent': user_pct,
                'system_percent': system_pct,
                'idle_percent': idle_pct,
                'load_avg_1m': round(load_avg[0], 2),
                'load_avg_5m': round(load_avg[1], 2),
                'load_avg_15m': round(load_avg[2], 2),
            }
        except Exception as e:
            return {'error': f'CPU məlumat xətası: {str(e)}'}

    # ============================================
    # RAM MƏLUMATLARI
    # ============================================

    def get_ram_info(self):
        """RAM məlumatlarını qaytarır"""
        if not self.psutil:
            return {'error': 'psutil quraşdırılmayıb'}

        try:
            mem = self.psutil.virtual_memory()
            swap = self.psutil.swap_memory()

            return {
                'total': mem.total,
                'total_gb': round(mem.total / (1024 ** 3), 2),
                'used': mem.used,
                'used_gb': round(mem.used / (1024 ** 3), 2),
                'available': mem.available,
                'available_gb': round(mem.available / (1024 ** 3), 2),
                'percent': mem.percent,
                'cached': mem.cached if hasattr(mem, 'cached') else 0,
                'cached_gb': round(mem.cached / (1024 ** 3), 2) if hasattr(mem, 'cached') and mem.cached else 0,
                'buffers': mem.buffers if hasattr(mem, 'buffers') else 0,
                'buffers_gb': round(mem.buffers / (1024 ** 3), 2) if hasattr(mem, 'buffers') and mem.buffers else 0,
                'swap': {
                    'total': swap.total,
                    'total_gb': round(swap.total / (1024 ** 3), 2),
                    'used': swap.used,
                    'used_gb': round(swap.used / (1024 ** 3), 2),
                    'percent': swap.percent,
                    'free': swap.free,
                    'free_gb': round(swap.free / (1024 ** 3), 2),
                },
            }
        except Exception as e:
            return {'error': f'RAM məlumat xətası: {str(e)}'}

    # ============================================
    # GPU / VRAM MƏLUMATLARI
    # ============================================

    def get_gpu_info(self):
        """GPU məlumatlarını qaytarır (NVIDIA GPU üçün)"""
        try:
            GPUtil = importlib.import_module('GPUtil')
        except Exception:
            GPUtil = None

        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    result = []
                    for gpu in gpus:
                        result.append({
                            'id': gpu.id,
                            'name': gpu.name,
                            'load_percent': round(gpu.load * 100, 1),
                            'memory_total': gpu.memoryTotal,
                            'memory_total_mb': round(gpu.memoryTotal, 0),
                            'memory_used': gpu.memoryUsed,
                            'memory_used_mb': round(gpu.memoryUsed, 0),
                            'memory_free': gpu.memoryFree,
                            'memory_free_mb': round(gpu.memoryFree, 0),
                            'memory_percent': round((gpu.memoryUsed / gpu.memoryTotal) * 100, 1) if gpu.memoryTotal > 0 else 0,
                            'temperature': gpu.temperature,
                            'uuid': gpu.uuid,
                        })
                    return {'gpus': result, 'count': len(result), 'available': True}
            except Exception:
                pass

        # nvidia-smi ilə yoxla
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,utilization.gpu,memory.total,memory.used,memory.free,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                gpus = []
                for line in result.stdout.strip().split('\n'):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 7:
                        try:
                            gpus.append({
                                'id': int(parts[0]),
                                'name': parts[1],
                                'load_percent': float(parts[2]),
                                'memory_total_mb': float(parts[3]),
                                'memory_used_mb': float(parts[4]),
                                'memory_free_mb': float(parts[5]),
                                'memory_total': float(parts[3]),
                                'memory_used': float(parts[4]),
                                'memory_free': float(parts[5]),
                                'memory_percent': round((float(parts[4]) / float(parts[3])) * 100, 1) if float(parts[3]) > 0 else 0,
                                'temperature': float(parts[6]),
                                'uuid': None,
                            })
                        except (ValueError, IndexError):
                            continue

                if gpus:
                    return {'gpus': gpus, 'count': len(gpus), 'available': True}
        except (FileNotFoundError, Exception):
            pass

        return {
            'gpus': [],
            'count': 0,
            'available': False,
            'message': 'GPU tapılmadı və ya nvidia-smi quraşdırılmayıb',
        }

    # ============================================
    # DİSK MƏLUMATLARI
    # ============================================

    def get_disk_info(self):
        """Disk məlumatlarını qaytarır"""
        if not self.psutil:
            return {'error': 'psutil quraşdırılmayıb'}

        try:
            partitions = []
            for partition in self.psutil.disk_partitions():
                try:
                    usage = self.psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'opts': partition.opts,
                        'total': usage.total,
                        'total_gb': round(usage.total / (1024 ** 3), 2),
                        'used': usage.used,
                        'used_gb': round(usage.used / (1024 ** 3), 2),
                        'free': usage.free,
                        'free_gb': round(usage.free / (1024 ** 3), 2),
                        'percent': usage.percent,
                    })
                except (PermissionError, OSError):
                    continue

            disk_io = self.psutil.disk_io_counters()
            io_data = None
            if disk_io:
                io_data = {
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count,
                    'read_bytes': disk_io.read_bytes,
                    'read_bytes_mb': round(disk_io.read_bytes / (1024 ** 2), 2),
                    'write_bytes': disk_io.write_bytes,
                    'write_bytes_mb': round(disk_io.write_bytes / (1024 ** 2), 2),
                }

            return {
                'partitions': partitions,
                'partition_count': len(partitions),
                'io': io_data,
            }
        except Exception as e:
            return {'error': f'Disk məlumat xətası: {str(e)}'}

    # ============================================
    # ŞƏBƏKƏ MƏLUMATLARI
    # ============================================

    def get_network_info(self):
        """Şəbəkə məlumatlarını qaytarır"""
        if not self.psutil:
            return {'error': 'psutil quraşdırılmayıb'}

        try:
            net_io = self.psutil.net_io_counters()
            connections = self.psutil.net_connections(kind='inet')

            active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])

            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_sent_mb': round(net_io.bytes_sent / (1024 ** 2), 2),
                'bytes_recv': net_io.bytes_recv,
                'bytes_recv_mb': round(net_io.bytes_recv / (1024 ** 2), 2),
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'total_connections': len(connections),
                'active_connections': active_connections,
            }
        except Exception as e:
            return {'error': f'Şəbəkə məlumat xətası: {str(e)}'}

    # ============================================
    # PROSESLƏR
    # ============================================

    def get_top_processes(self, sort_by='cpu', limit=10):
        """Ən çox resurs istifadə edən prosesləri qaytarır"""
        if not self.psutil:
            return {'error': 'psutil quraşdırılmayıb'}

        try:
            processes = []
            for proc in self.psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = proc.info
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'cpu_percent': round(info['cpu_percent'] or 0, 1),
                        'memory_percent': round(info['memory_percent'] or 0, 1),
                        'status': info['status'],
                    })
                except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                    continue

            if sort_by == 'cpu':
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            elif sort_by == 'memory':
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            else:
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

            return {
                'processes': processes[:limit],
                'sort_by': sort_by,
                'total_count': len(processes),
            }
        except Exception as e:
            return {'error': f'Proses məlumat xətası: {str(e)}'}

    # ============================================
    # APP.PY ÜÇÜN UYĞUNLAŞDIRMA METODLARI
    # ============================================

    def get_system_info(self):
        """app.py monitor/status üçün - get_system_overview alias"""
        return self.get_system_overview()

    def get_processes(self):
        """app.py monitor/processes üçün - get_top_processes alias"""
        result = self.get_top_processes()
        if isinstance(result, dict) and 'processes' in result:
            return result['processes']
        return result

    # ============================================
    # TAM SİSTEM MƏLUMATI
    # ============================================

    def get_system_overview(self):
        """Bütün sistem məlumatlarını birlikdə qaytarır"""
        cpu = self.get_cpu_info()
        ram = self.get_ram_info()
        gpu = self.get_gpu_info()
        disk = self.get_disk_info()
        network = self.get_network_info()

        if self.psutil:
            try:
                boot_time = self.psutil.boot_time()
                uptime_seconds = int(time.time() - boot_time)
                uptime_hours = uptime_seconds // 3600
                uptime_minutes = (uptime_seconds % 3600) // 60
                uptime_str = f"{uptime_hours} saat {uptime_minutes} dəqiqə"
            except Exception:
                uptime_str = "Naməlum"
        else:
            uptime_str = "Naməlum"

        return {
            'timestamp': datetime.now().isoformat(),
            'uptime': uptime_str,
            'cpu': cpu if 'error' not in cpu else {'error': cpu['error']},
            'ram': ram if 'error' not in ram else {'error': ram['error']},
            'gpu': gpu,
            'disk': disk if 'error' not in disk else {'error': disk['error']},
            'network': network if 'error' not in network else {'error': network['error']},
        }

    # ============================================
    # CANLI MONİTORİNG DATASI
    # ============================================

    def get_live_data(self):
        """WebSocket üçün yüngül canlı data"""
        if not self.psutil:
            return {'error': 'psutil quraşdırılmayıb'}

        try:
            cpu = self.psutil.cpu_percent(interval=0.3)
            mem = self.psutil.virtual_memory()
            disk = self.psutil.disk_usage('/')
            net_io = self.psutil.net_io_counters()

            data = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu,
                'ram_percent': mem.percent,
                'ram_used_gb': round(mem.used / (1024 ** 3), 2),
                'ram_total_gb': round(mem.total / (1024 ** 3), 2),
                'disk_percent': disk.percent,
                'disk_used_gb': round(disk.used / (1024 ** 3), 2),
                'disk_total_gb': round(disk.total / (1024 ** 3), 2),
                'net_bytes_sent': net_io.bytes_sent,
                'net_bytes_recv': net_io.bytes_recv,
            }

            # GPU əlavə et (varsa)
            gpu_info = self.get_gpu_info()
            if gpu_info.get('available') and gpu_info.get('gpus'):
                primary_gpu = gpu_info['gpus'][0]
                data['gpu_percent'] = primary_gpu['load_percent']
                data['vram_percent'] = primary_gpu['memory_percent']
                data['vram_used_mb'] = primary_gpu['memory_used_mb']
                data['vram_total_mb'] = primary_gpu['memory_total_mb']
                data['gpu_temp'] = primary_gpu['temperature']
                data['gpu_name'] = primary_gpu['name']

            # Database-ə saxla (hər 60 saniyədən bir)
            self._save_metric(data)

            return data
        except Exception as e:
            return {'error': f'Canlı data xətası: {str(e)}'}

    # ============================================
    # TARİXÇƏ
    # ============================================

    def get_metric_history(self, metric_type='cpu', hours=1):
        """Keçmiş metrikları qaytarır"""
        try:
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM system_metrics WHERE metric_type = ? AND created_at >= ? ORDER BY created_at DESC LIMIT 500',
                (metric_type, cutoff))
            rows = cursor.fetchall()
            conn.close()

            result = []
            for r in rows:
                d = dict(r)
                try:
                    d['metadata'] = json.loads(d.get('metric_metadata', '{}'))
                except (json.JSONDecodeError, TypeError):
                    d['metadata'] = {}
                result.append(d)

            return {
                'metric_type': metric_type,
                'hours': hours,
                'data': list(reversed(result)),
                'count': len(result),
            }
        except Exception as e:
            return {'error': str(e), 'data': [], 'count': 0}

    # ============================================
    # STATİSTİKA
    # ============================================

    def get_stats(self):
        """Monitorinq statistikasını qaytarır"""
        try:
            stats = db.metric_stats()
            latest = db.metric_get_latest()

            result = {
                'total_metrics': stats.get('total_metrics', 0),
                'type_distribution': stats.get('type_distribution', []),
                'latest_metric': None,
            }

            if latest:
                result['latest_metric'] = {
                    'type': latest.get('metric_type'),
                    'value': latest.get('value'),
                    'created_at': latest.get('created_at'),
                }

            return result
        except Exception as e:
            return {'error': str(e), 'total_metrics': 0}

    # ============================================
    # DATABASE KÖMƏKÇİLƏRİ
    # ============================================

    def _save_metric(self, data):
        """Metrikları database-ə saxlayır (hər 60 saniyədən bir)"""
        now = time.time()
        if now - self._last_save_time < 60:
            return

        try:
            now_iso = datetime.now().isoformat()

            # CPU
            db.metric_save('cpu', str(data.get('cpu_percent', 0)),
                           {'percent': data.get('cpu_percent', 0)})

            # RAM
            db.metric_save('ram', str(data.get('ram_percent', 0)),
                           {
                               'percent': data.get('ram_percent', 0),
                               'used_gb': data.get('ram_used_gb', 0),
                               'total_gb': data.get('ram_total_gb', 0),
                           })

            # GPU (varsa)
            if 'gpu_percent' in data:
                db.metric_save('gpu', str(data.get('gpu_percent', 0)),
                               {
                                   'load_percent': data.get('gpu_percent', 0),
                                   'vram_percent': data.get('vram_percent', 0),
                                   'vram_used_mb': data.get('vram_used_mb', 0),
                                   'vram_total_mb': data.get('vram_total_mb', 0),
                                   'temperature': data.get('gpu_temp', 0),
                                   'name': data.get('gpu_name', ''),
                               })

            # Disk
            db.metric_save('disk', str(data.get('disk_percent', 0)),
                           {
                               'percent': data.get('disk_percent', 0),
                               'used_gb': data.get('disk_used_gb', 0),
                               'total_gb': data.get('disk_total_gb', 0),
                           })

            self._last_save_time = now
        except Exception as e:
            print(f'[Monitor] Metric save xəta: {e}')

    # ============================================
    # KÖHNƏ METRİKALARI TƏMİZLƏ
    # ============================================

    def cleanup_old_metrics(self, days=7):
        """Köhnə metrikları silir"""
        try:
            deleted = db.metric_cleanup(days)
            return {
                'success': True,
                'deleted_count': deleted,
                'message': f'{deleted} köhnə metrik silindi ({days} gündən köhnə)',
            }
        except Exception as e:
            return {'error': str(e)}