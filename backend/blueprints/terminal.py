# -*- coding: utf-8 -*-
"""
Module Terminal - Execution de code Python via interface web
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import tempfile
import subprocess
import os
import sys

terminal_bp = Blueprint('terminal', __name__)


@terminal_bp.route('/api/terminal/execute', methods=['POST'])
@login_required
def execute():
    """
    Execute du code Python fourni dans le corps JSON: {"code": "..."}
    Retourne stdout, stderr, returncode et si timeout.
    NOTE: Execution non sandboxee - a limiter/isoler en production.
    """
    from .presence import start_process, stop_process

    data = request.get_json() or {}
    code = data.get('code', '')
    timeout = int(data.get('timeout', 10))

    # Limiter le timeout max
    if timeout > 30:
        timeout = 30

    username = getattr(current_user, 'username', 'anonymous')
    pid = start_process('terminal', 'Execution de code Python', owner=username)

    # Fichier temporaire pour le code
    fd, path = tempfile.mkstemp(suffix='.py', prefix='term_')
    os.close(fd)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)

        # Executer Python en processus separe avec timeout
        try:
            proc = subprocess.run(
                [sys.executable, '-u', path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tempfile.gettempdir()
            )
            stop_process(pid, status='stopped')

            return jsonify({
                'stdout': proc.stdout,
                'stderr': proc.stderr,
                'returncode': proc.returncode,
                'timeout': False
            })

        except subprocess.TimeoutExpired as e:
            stop_process(pid, status='failed', message=f'Timeout after {timeout}s')

            return jsonify({
                'stdout': e.stdout or '',
                'stderr': (e.stderr or '') + f'\nExecution timed out after {timeout}s',
                'returncode': -1,
                'timeout': True
            }), 408

    except Exception as e:
        stop_process(pid, status='failed', message=str(e))
        return jsonify({
            'error': str(e),
            'stdout': '',
            'stderr': str(e),
            'returncode': -1,
            'timeout': False
        }), 500

    finally:
        try:
            os.remove(path)
        except Exception:
            pass


@terminal_bp.route('/api/terminal/history', methods=['GET'])
@login_required
def get_history():
    """Recuperer l'historique des executions (placeholder)"""
    # Pour une vraie implementation, stocker en DB
    return jsonify({'history': []})
