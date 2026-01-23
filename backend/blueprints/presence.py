# -*- coding: utf-8 -*-
"""
Module Presence - Suivi des utilisateurs connectes et des processus en cours
"""
from flask import Blueprint, request, jsonify
from flask_login import current_user
import threading
import time
import uuid

presence_bp = Blueprint('presence', __name__)

# Stores en memoire (pour dev). En production, utiliser Redis.
_active_users = {}  # user_id -> { username, page, last_seen }
_processes = {}     # pid -> { id, type, description, owner, started_at, status }

_LOCK = threading.Lock()
_CLEANUP_INTERVAL = 30  # secondes
_USER_TIMEOUT = 90  # secondes


def _cleanup_loop():
    """Thread de nettoyage des utilisateurs inactifs et processus termines"""
    while True:
        now = time.time()
        with _LOCK:
            # Nettoyer les utilisateurs inactifs
            to_del = [uid for uid, v in _active_users.items()
                      if now - v['last_seen'] > _USER_TIMEOUT]
            for uid in to_del:
                _active_users.pop(uid, None)

            # Nettoyer les processus termines depuis plus de 5 minutes
            old_procs = [pid for pid, p in _processes.items()
                         if p['status'] in ('stopped', 'failed')
                         and now - p.get('stopped_at', 0) > 300]
            for pid in old_procs:
                _processes.pop(pid, None)

        time.sleep(_CLEANUP_INTERVAL)


# Demarrer le thread de nettoyage
_cleanup_thread = threading.Thread(target=_cleanup_loop, daemon=True)
_cleanup_thread.start()


# ============================================================================
# FONCTIONS UTILITAIRES (utilisables par d'autres modules)
# ============================================================================

def start_process(type_: str, description: str, owner: str = None) -> str:
    """
    Enregistrer un nouveau processus en cours.

    Args:
        type_: Type de processus (terminal, scan, etc.)
        description: Description du processus
        owner: Proprietaire (username)

    Returns:
        pid: ID unique du processus
    """
    pid = str(uuid.uuid4())
    with _LOCK:
        _processes[pid] = {
            'id': pid,
            'type': type_,
            'description': description,
            'owner': owner or 'system',
            'started_at': int(time.time()),
            'status': 'running'
        }
    return pid


def stop_process(pid: str, status: str = 'stopped', message: str = None) -> bool:
    """
    Marquer un processus comme termine.

    Args:
        pid: ID du processus
        status: Statut final (stopped, failed, completed)
        message: Message optionnel

    Returns:
        True si le processus a ete trouve et mis a jour
    """
    with _LOCK:
        p = _processes.get(pid)
        if not p:
            return False
        p['status'] = status
        p['stopped_at'] = int(time.time())
        if message:
            p['message'] = message
    return True


def get_active_users_count() -> int:
    """Retourner le nombre d'utilisateurs actifs"""
    with _LOCK:
        return len(_active_users)


def get_running_processes_count() -> int:
    """Retourner le nombre de processus en cours"""
    with _LOCK:
        return sum(1 for p in _processes.values() if p['status'] == 'running')


# ============================================================================
# ROUTES API
# ============================================================================

@presence_bp.route('/api/presence/heartbeat', methods=['POST'])
def heartbeat():
    """
    Endpoint heartbeat pour signaler la presence d'un utilisateur.
    Appele regulierement par le frontend.
    """
    data = request.get_json() or {}
    page = data.get('page', 'unknown')

    user = None
    if current_user and hasattr(current_user, 'id') and current_user.is_authenticated:
        user = {
            'id': str(current_user.id),
            'username': getattr(current_user, 'username', 'unknown')
        }
    else:
        # Permettre les heartbeats anonymes (dev)
        user = {
            'id': data.get('user_id', str(uuid.uuid4())),
            'username': data.get('username', 'anonymous')
        }

    with _LOCK:
        _active_users[user['id']] = {
            'username': user['username'],
            'page': page,
            'last_seen': time.time()
        }

    return jsonify({'status': 'ok'}), 200


@presence_bp.route('/api/presence/active', methods=['GET'])
def get_active_users():
    """Obtenir la liste des utilisateurs actifs"""
    with _LOCK:
        now = time.time()
        users = []
        for uid, v in _active_users.items():
            users.append({
                'id': uid,
                'username': v['username'],
                'page': v['page'],
                'last_seen': int(now - v['last_seen'])
            })

    return jsonify({'users': users})


@presence_bp.route('/api/processes', methods=['GET'])
def get_processes():
    """Obtenir la liste des processus"""
    with _LOCK:
        procs = list(_processes.values())

    return jsonify({'processes': procs})


@presence_bp.route('/api/presence/stats', methods=['GET'])
def get_stats():
    """Obtenir les statistiques de presence"""
    return jsonify({
        'active_users': get_active_users_count(),
        'running_processes': get_running_processes_count()
    })
