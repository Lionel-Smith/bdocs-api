"""
BDOCS BTVI Certification Module - Vocational certifications.

BTVI (Bahamas Technical and Vocational Institute) provides
industry-recognized vocational certifications. This module
tracks certifications earned through prison programmes or
prior training.

Supported trades:
- AUTOMOTIVE: Auto mechanics, body work
- ELECTRICAL: Electrical installation, wiring
- PLUMBING: Plumbing installation, repair
- CARPENTRY: Wood construction, cabinetry
- WELDING: Metal welding, fabrication
- CULINARY: Food preparation, cooking
- COSMETOLOGY: Hair, beauty services
- HVAC: Heating, ventilation, air conditioning
- MASONRY: Block/brick laying, concrete work

Key features:
- Unique certification numbers (BTVI-YYYY-NNNNN)
- Optional linkage to programme enrollments
- Skill level progression (BASIC → MASTER)
- External verification support
"""
from src.modules.btvi.models import BTVICertification
from src.modules.btvi.controller import btvi_bp, blueprint

__all__ = [
    'BTVICertification',
    'btvi_bp',
    'blueprint'
]
