# -*- coding: utf-8 -*-
"""
Configuration du système de logging structuré
"""
import logging
import logging.handlers
import os
from datetime import datetime


# Créer le répertoire des logs s'il n'existe pas
LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)


def setup_logging(app_name='oteria', log_level=logging.INFO):
    """
    Configure le système de logging de l'application

    Args:
        app_name: Nom de l'application pour les fichiers de log
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logger configuré
    """
    # Créer le logger principal
    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)

    # Éviter la duplication si déjà configuré
    if logger.handlers:
        return logger

    # Format des logs
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Format simple pour la console
    console_format = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # Handler pour la console (niveau INFO et plus)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Handler pour fichier général (tous les logs)
    general_log_file = os.path.join(LOGS_DIR, f'{app_name}.log')
    file_handler = logging.handlers.RotatingFileHandler(
        general_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    # Handler pour les erreurs uniquement
    error_log_file = os.path.join(LOGS_DIR, f'{app_name}_errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    logger.addHandler(error_handler)

    # Handler pour les scans (activité métier)
    scans_log_file = os.path.join(LOGS_DIR, f'{app_name}_scans.log')
    scans_handler = logging.handlers.RotatingFileHandler(
        scans_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    scans_handler.setLevel(logging.INFO)
    scans_handler.setFormatter(log_format)

    # Filtre personnalisé pour les scans
    class ScanFilter(logging.Filter):
        def filter(self, record):
            return 'SCAN' in record.getMessage() or record.name.endswith('_scan')

    scans_handler.addFilter(ScanFilter())
    logger.addHandler(scans_handler)

    logger.info(f'Logging system initialized for {app_name}')
    logger.debug(f'Log directory: {LOGS_DIR}')

    return logger


def get_logger(name):
    """
    Récupère un logger pour un module spécifique

    Args:
        name: Nom du module

    Returns:
        Logger configuré
    """
    return logging.getLogger(f'oteria.{name}')


def log_scan_activity(logger, scan_type, investigation_id, target, status, **kwargs):
    """
    Log une activité de scan de manière structurée

    Args:
        logger: Logger à utiliser
        scan_type: Type de scan (recon, network, ad, vuln)
        investigation_id: ID de l'investigation
        target: Cible du scan
        status: Statut (started, completed, failed)
        **kwargs: Données additionnelles
    """
    extra_info = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
    message = f'SCAN [{scan_type}] inv={investigation_id} target={target} status={status}'

    if extra_info:
        message += f' | {extra_info}'

    if status == 'failed':
        logger.error(message)
    elif status == 'completed':
        logger.info(message)
    else:
        logger.debug(message)


def log_security_event(logger, event_type, user_id, details, severity='info'):
    """
    Log un événement de sécurité

    Args:
        logger: Logger à utiliser
        event_type: Type d'événement (login, logout, auth_failure, permission_denied, etc.)
        user_id: ID de l'utilisateur concerné
        details: Détails de l'événement
        severity: Sévérité (info, warning, error, critical)
    """
    message = f'SECURITY [{event_type}] user={user_id} - {details}'

    if severity == 'critical':
        logger.critical(message)
    elif severity == 'error':
        logger.error(message)
    elif severity == 'warning':
        logger.warning(message)
    else:
        logger.info(message)


# Logger principal de l'application
app_logger = setup_logging('oteria', logging.DEBUG)
