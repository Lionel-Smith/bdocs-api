"""
BDOCS Housing & Classification Module

Manages housing unit assignments and security classification
for inmates at Fox Hill Correctional Facility.

Fox Hill Units:
- Maximum Security: MAX-A, MAX-B, MAX-C
- Medium Security: MED-A, MED-B, MED-C
- Minimum Security: MIN-A, MIN-B
- Female: FEM-1
- Remand: REM-1
- Juvenile: JUV-1
"""
from src.modules.housing.models import HousingUnit, Classification, HousingAssignment
from src.modules.housing.controller import blueprint

__all__ = ['HousingUnit', 'Classification', 'HousingAssignment', 'blueprint']
