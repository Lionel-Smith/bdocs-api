"""
Population Report Generator - Daily counts, demographics, housing distribution.

Report codes: RPT-POP-001 through RPT-POP-004
- RPT-POP-001: Daily Population Summary
- RPT-POP-002: Population by Security Level
- RPT-POP-003: Population by Housing Unit
- RPT-POP-004: Demographic Analysis

NOTE: STUB implementation using mock data.
TODO: Connect to population module repository for real data.
"""
from datetime import datetime, date
from typing import Dict, Any
import random

from src.common.enums import OutputFormat
from src.modules.reports.generators import BaseReportGenerator, ReportOutput


class PopulationReportGenerator(BaseReportGenerator):
    """Generator for population-related reports."""

    async def generate(
        self,
        params: Dict[str, Any],
        output_format: OutputFormat
    ) -> ReportOutput:
        """Generate population report."""
        report_code = params.get('report_code', 'RPT-POP-001')
        as_of_date = params.get('as_of_date', date.today())

        # Generate mock population data
        # TODO: Replace with actual repository queries
        data = await self._generate_mock_data(report_code, as_of_date)

        # Generate output file
        output_path = self._get_output_path(report_code, output_format)

        if output_format == OutputFormat.JSON:
            file_size = await self._write_json(output_path, data)
        elif output_format == OutputFormat.CSV:
            file_size = await self._write_population_csv(output_path, data)
        elif output_format == OutputFormat.EXCEL:
            file_size = await self._write_stub_excel(output_path, {
                'Summary': [data['summary']],
                'By Status': data['by_status'],
                'By Security': data['by_security_level'],
                'By Housing': data['by_housing_unit']
            })
        else:  # PDF
            content = self._format_population_text(data)
            file_size = await self._write_stub_pdf(
                output_path,
                f"Population Report - {as_of_date}",
                content
            )

        return ReportOutput(
            file_path=str(output_path),
            file_size_bytes=file_size,
            format=output_format,
            generated_at=datetime.utcnow(),
            metadata={
                'report_code': report_code,
                'as_of_date': str(as_of_date),
                'total_population': data['summary']['total_population']
            }
        )

    async def _generate_mock_data(
        self,
        report_code: str,
        as_of_date: date
    ) -> Dict[str, Any]:
        """Generate mock population data."""
        # TODO: Replace with actual queries to population repository

        # Use date hash for consistent mock data
        seed = hash(str(as_of_date)) % 1000
        random.seed(seed)

        total = random.randint(850, 950)

        # Status breakdown
        active = int(total * 0.85)
        remand = int(total * 0.12)
        transit = total - active - remand

        # Security levels
        maximum = int(total * 0.25)
        medium = int(total * 0.45)
        minimum = int(total * 0.20)
        protective = total - maximum - medium - minimum

        # Housing units (BDCS has multiple units)
        units = {
            'Maximum Security Block A': int(maximum * 0.6),
            'Maximum Security Block B': maximum - int(maximum * 0.6),
            'Medium Security Unit 1': int(medium * 0.35),
            'Medium Security Unit 2': int(medium * 0.35),
            'Medium Security Unit 3': medium - int(medium * 0.7),
            'Minimum Security Dormitory': minimum,
            'Protective Custody': protective,
            'Medical Unit': random.randint(5, 15),
            'Intake Processing': random.randint(3, 10)
        }

        # Demographics
        male = int(total * 0.94)
        female = total - male

        return {
            'report_code': report_code,
            'as_of_date': str(as_of_date),
            'facility': 'Bahamas Department of Correctional Services',
            'summary': {
                'total_population': total,
                'capacity': 1000,
                'occupancy_rate': round(total / 1000 * 100, 1),
                'average_age': round(random.uniform(28, 35), 1),
                'average_sentence_months': round(random.uniform(24, 60), 1)
            },
            'by_status': [
                {'status': 'ACTIVE', 'count': active, 'percentage': round(active/total*100, 1)},
                {'status': 'REMAND', 'count': remand, 'percentage': round(remand/total*100, 1)},
                {'status': 'TRANSIT', 'count': transit, 'percentage': round(transit/total*100, 1)}
            ],
            'by_security_level': [
                {'level': 'MAXIMUM', 'count': maximum, 'percentage': round(maximum/total*100, 1)},
                {'level': 'MEDIUM', 'count': medium, 'percentage': round(medium/total*100, 1)},
                {'level': 'MINIMUM', 'count': minimum, 'percentage': round(minimum/total*100, 1)},
                {'level': 'PROTECTIVE', 'count': protective, 'percentage': round(protective/total*100, 1)}
            ],
            'by_housing_unit': [
                {'unit': k, 'count': v, 'percentage': round(v/total*100, 1)}
                for k, v in units.items()
            ],
            'by_gender': [
                {'gender': 'MALE', 'count': male, 'percentage': round(male/total*100, 1)},
                {'gender': 'FEMALE', 'count': female, 'percentage': round(female/total*100, 1)}
            ],
            '_stub': True,
            '_message': 'STUB: Mock data for development'
        }

    async def _write_population_csv(self, path, data: Dict[str, Any]) -> int:
        """Write population data as CSV."""
        headers = ['Category', 'Item', 'Count', 'Percentage']
        rows = []

        # Summary
        rows.append(['Summary', 'Total Population', data['summary']['total_population'], '100.0'])
        rows.append(['Summary', 'Capacity', data['summary']['capacity'], '-'])
        rows.append(['Summary', 'Occupancy Rate', '-', data['summary']['occupancy_rate']])

        # By status
        for item in data['by_status']:
            rows.append(['Status', item['status'], item['count'], item['percentage']])

        # By security
        for item in data['by_security_level']:
            rows.append(['Security Level', item['level'], item['count'], item['percentage']])

        # By housing
        for item in data['by_housing_unit']:
            rows.append(['Housing Unit', item['unit'], item['count'], item['percentage']])

        return await self._write_csv(path, rows, headers)

    def _format_population_text(self, data: Dict[str, Any]) -> str:
        """Format population data as text for PDF."""
        lines = [
            f"Facility: {data['facility']}",
            f"As of Date: {data['as_of_date']}",
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Population: {data['summary']['total_population']}",
            f"Capacity: {data['summary']['capacity']}",
            f"Occupancy Rate: {data['summary']['occupancy_rate']}%",
            f"Average Age: {data['summary']['average_age']} years",
            f"Average Sentence: {data['summary']['average_sentence_months']} months",
            "",
            "BY STATUS",
            "-" * 40
        ]

        for item in data['by_status']:
            lines.append(f"  {item['status']}: {item['count']} ({item['percentage']}%)")

        lines.extend(["", "BY SECURITY LEVEL", "-" * 40])
        for item in data['by_security_level']:
            lines.append(f"  {item['level']}: {item['count']} ({item['percentage']}%)")

        lines.extend(["", "BY HOUSING UNIT", "-" * 40])
        for item in data['by_housing_unit']:
            lines.append(f"  {item['unit']}: {item['count']} ({item['percentage']}%)")

        return "\n".join(lines)


async def get_quick_population_summary(as_of_date: date = None) -> Dict[str, Any]:
    """
    Get quick population summary without file generation.

    Used by the quick report endpoint for real-time dashboard data.

    TODO: Replace mock data with actual repository queries.
    """
    if not as_of_date:
        as_of_date = date.today()

    generator = PopulationReportGenerator()
    data = await generator._generate_mock_data('QUICK', as_of_date)

    return {
        'as_of_date': str(as_of_date),
        'total_population': data['summary']['total_population'],
        'by_status': {item['status']: item['count'] for item in data['by_status']},
        'by_security_level': {item['level']: item['count'] for item in data['by_security_level']},
        'by_housing_unit': {item['unit']: item['count'] for item in data['by_housing_unit']},
        'by_gender': {item['gender']: item['count'] for item in data['by_gender']},
        'average_age': data['summary']['average_age'],
        'average_sentence_months': data['summary']['average_sentence_months'],
        'generated_at': datetime.utcnow().isoformat(),
        '_stub': True
    }
