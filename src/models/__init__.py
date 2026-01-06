"""
BDOCS Models Package

This module auto-discovers all *_model.py files and provides
convenient exports for mixins and base classes.
"""
import os
import glob
import importlib

# BDOCS Mixins - for building domain models
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin

# Audit logging
from src.models.audit_log_model import (
    AuditLog,
    AUDIT_TRIGGER_FUNCTION,
    create_audit_trigger_sql,
    drop_audit_trigger_sql,
)

__all__ = [
    # Mixins
    'UUIDMixin',
    'SoftDeleteMixin',
    'AuditMixin',
    # Audit
    'AuditLog',
    'AUDIT_TRIGGER_FUNCTION',
    'create_audit_trigger_sql',
    'drop_audit_trigger_sql',
]

# Dynamically add *_model.py files to application
# This auto-discovers and imports all model files for SQLAlchemy registration
project_name = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
project_name = project_name.split(os.sep, -1)[-1]
for f in glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "**", "*_model.py"), recursive=True):
    spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f)
    mod = f.replace(os.sep, ".").split(project_name, 1)[1][:-3]
    mod = mod.replace(".", "", 1)
    importlib.import_module(mod)
    