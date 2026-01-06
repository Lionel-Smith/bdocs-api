"""
Report Generators - Strategy pattern implementations for different report types.

Each generator handles a specific category of reports and produces output
in the requested format (PDF, Excel, CSV, JSON).

Base interface:
- generate(params, output_format) -> ReportOutput

NOTE: These are STUB implementations using mock data.
TODO: Connect to actual module repositories when integrating.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from src.common.enums import OutputFormat


@dataclass
class ReportOutput:
    """Result of report generation."""
    file_path: str
    file_size_bytes: int
    format: OutputFormat
    generated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class BaseReportGenerator(ABC):
    """Abstract base class for report generators."""

    def __init__(self, output_dir: str = "/tmp/bdocs_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def generate(
        self,
        params: Dict[str, Any],
        output_format: OutputFormat
    ) -> ReportOutput:
        """Generate the report with given parameters."""
        pass

    def _get_output_path(
        self,
        report_code: str,
        output_format: OutputFormat
    ) -> Path:
        """Generate output file path."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extension = output_format.value.lower()
        filename = f"{report_code}_{timestamp}.{extension}"
        return self.output_dir / filename

    async def _write_json(self, path: Path, data: Dict[str, Any]) -> int:
        """Write data as JSON file."""
        import json
        content = json.dumps(data, indent=2, default=str)
        path.write_text(content)
        return path.stat().st_size

    async def _write_csv(self, path: Path, data: list, headers: list) -> int:
        """Write data as CSV file."""
        import csv
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)
        return path.stat().st_size

    async def _write_stub_pdf(self, path: Path, title: str, content: str) -> int:
        """Write stub PDF (text file with .pdf extension for development)."""
        # NOTE: In production, use reportlab or weasyprint for actual PDF
        stub_content = f"""
========================================
{title}
========================================
Generated: {datetime.utcnow().isoformat()}

{content}

========================================
STUB: This is a development placeholder.
Real PDF generation requires reportlab/weasyprint.
========================================
"""
        path.write_text(stub_content)
        return path.stat().st_size

    async def _write_stub_excel(self, path: Path, sheets: Dict[str, list]) -> int:
        """Write stub Excel (JSON file with .xlsx extension for development)."""
        # NOTE: In production, use openpyxl for actual Excel
        import json
        stub_content = {
            "_stub": True,
            "_message": "This is a development placeholder. Real Excel requires openpyxl.",
            "generated": datetime.utcnow().isoformat(),
            "sheets": sheets
        }
        path.write_text(json.dumps(stub_content, indent=2, default=str))
        return path.stat().st_size


# Import generators for easy access
from src.modules.reports.generators.population_report import PopulationReportGenerator
from src.modules.reports.generators.incident_report import IncidentReportGenerator
from src.modules.reports.generators.programme_report import ProgrammeReportGenerator
from src.modules.reports.generators.aca_report import ACAReportGenerator

__all__ = [
    'BaseReportGenerator',
    'ReportOutput',
    'PopulationReportGenerator',
    'IncidentReportGenerator',
    'ProgrammeReportGenerator',
    'ACAReportGenerator',
]
