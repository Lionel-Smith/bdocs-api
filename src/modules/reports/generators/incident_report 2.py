"""
Incident Report Generator - Date range analysis, by type, by severity.

Report codes: RPT-INC-001 through RPT-INC-003
- RPT-INC-001: Incident Summary (date range)
- RPT-INC-002: Incidents by Type Analysis
- RPT-INC-003: Incidents by Severity Analysis

NOTE: STUB implementation using mock data.
TODO: Connect to incidents module repository for real data.
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import random

from src.common.enums import OutputFormat
from src.modules.reports.generators import BaseReportGenerator, ReportOutput


class IncidentReportGenerator(BaseReportGenerator):
    """Generator for incident-related reports."""

    # Mock incident types matching the incidents module
    INCIDENT_TYPES = [
        'ASSAULT', 'CONTRABAND', 'ESCAPE_ATTEMPT', 'MEDICAL_EMERGENCY',
        'PROPERTY_DAMAGE', 'DISTURBANCE', 'POLICY_VIOLATION', 'OTHER'
    ]

    SEVERITY_LEVELS = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

    async def generate(
        self,
        params: Dict[str, Any],
        output_format: OutputFormat
    ) -> ReportOutput:
        """Generate incident report."""
        report_code = params.get('report_code', 'RPT-INC-001')
        start_date = params.get('start_date', date.today() - timedelta(days=30))
        end_date = params.get('end_date', date.today())

        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        # Generate mock incident data
        # TODO: Replace with actual repository queries
        data = await self._generate_mock_data(report_code, start_date, end_date)

        # Generate output file
        output_path = self._get_output_path(report_code, output_format)

        if output_format == OutputFormat.JSON:
            file_size = await self._write_json(output_path, data)
        elif output_format == OutputFormat.CSV:
            file_size = await self._write_incident_csv(output_path, data)
        elif output_format == OutputFormat.EXCEL:
            file_size = await self._write_stub_excel(output_path, {
                'Summary': [data['summary']],
                'By Type': data['by_type'],
                'By Severity': data['by_severity'],
                'Daily Trend': data['daily_trend']
            })
        else:  # PDF
            content = self._format_incident_text(data)
            file_size = await self._write_stub_pdf(
                output_path,
                f"Incident Report - {start_date} to {end_date}",
                content
            )

        return ReportOutput(
            file_path=str(output_path),
            file_size_bytes=file_size,
            format=output_format,
            generated_at=datetime.utcnow(),
            metadata={
                'report_code': report_code,
                'start_date': str(start_date),
                'end_date': str(end_date),
                'total_incidents': data['summary']['total_incidents']
            }
        )

    async def _generate_mock_data(
        self,
        report_code: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Generate mock incident data."""
        # TODO: Replace with actual queries to incidents repository

        days = (end_date - start_date).days + 1
        seed = hash(f"{start_date}{end_date}") % 1000
        random.seed(seed)

        # Generate daily incidents
        daily_trend = []
        total = 0
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            # More incidents on weekends (mock pattern)
            base = 3 if current_date.weekday() >= 5 else 2
            count = random.randint(base - 1, base + 3)
            total += count
            daily_trend.append({
                'date': str(current_date),
                'count': count
            })

        # By type distribution
        type_counts = {}
        remaining = total
        for i, inc_type in enumerate(self.INCIDENT_TYPES[:-1]):
            if remaining <= 0:
                type_counts[inc_type] = 0
            else:
                # Weight certain types higher
                weight = 0.25 if inc_type in ['ASSAULT', 'CONTRABAND'] else 0.1
                count = min(int(total * weight) + random.randint(-2, 2), remaining)
                count = max(0, count)
                type_counts[inc_type] = count
                remaining -= count
        type_counts['OTHER'] = max(0, remaining)

        # By severity
        severity_counts = {
            'CRITICAL': int(total * 0.05),
            'HIGH': int(total * 0.20),
            'MEDIUM': int(total * 0.45),
            'LOW': total - int(total * 0.05) - int(total * 0.20) - int(total * 0.45)
        }

        # By status
        status_counts = {
            'OPEN': int(total * 0.15),
            'UNDER_INVESTIGATION': int(total * 0.25),
            'CLOSED': int(total * 0.55),
            'REFERRED': total - int(total * 0.15) - int(total * 0.25) - int(total * 0.55)
        }

        most_common = max(type_counts, key=type_counts.get)
        daily_avg = round(total / days, 1) if days > 0 else 0

        return {
            'report_code': report_code,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'days_covered': days,
            'summary': {
                'total_incidents': total,
                'daily_average': daily_avg,
                'most_common_type': most_common,
                'critical_count': severity_counts['CRITICAL'],
                'high_severity_count': severity_counts['CRITICAL'] + severity_counts['HIGH'],
                'open_incidents': status_counts['OPEN'] + status_counts['UNDER_INVESTIGATION']
            },
            'by_type': [
                {'type': k, 'count': v, 'percentage': round(v/total*100, 1) if total > 0 else 0}
                for k, v in type_counts.items()
            ],
            'by_severity': [
                {'severity': k, 'count': v, 'percentage': round(v/total*100, 1) if total > 0 else 0}
                for k, v in severity_counts.items()
            ],
            'by_status': [
                {'status': k, 'count': v, 'percentage': round(v/total*100, 1) if total > 0 else 0}
                for k, v in status_counts.items()
            ],
            'daily_trend': daily_trend,
            '_stub': True,
            '_message': 'STUB: Mock data for development'
        }

    async def _write_incident_csv(self, path, data: Dict[str, Any]) -> int:
        """Write incident data as CSV."""
        headers = ['Category', 'Item', 'Count', 'Percentage']
        rows = []

        # Summary
        rows.append(['Summary', 'Total Incidents', data['summary']['total_incidents'], '100.0'])
        rows.append(['Summary', 'Daily Average', data['summary']['daily_average'], '-'])
        rows.append(['Summary', 'Most Common Type', data['summary']['most_common_type'], '-'])

        # By type
        for item in data['by_type']:
            rows.append(['Type', item['type'], item['count'], item['percentage']])

        # By severity
        for item in data['by_severity']:
            rows.append(['Severity', item['severity'], item['count'], item['percentage']])

        # By status
        for item in data['by_status']:
            rows.append(['Status', item['status'], item['count'], item['percentage']])

        return await self._write_csv(path, rows, headers)

    def _format_incident_text(self, data: Dict[str, Any]) -> str:
        """Format incident data as text for PDF."""
        lines = [
            f"Period: {data['start_date']} to {data['end_date']}",
            f"Days Covered: {data['days_covered']}",
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Incidents: {data['summary']['total_incidents']}",
            f"Daily Average: {data['summary']['daily_average']}",
            f"Most Common Type: {data['summary']['most_common_type']}",
            f"Critical Incidents: {data['summary']['critical_count']}",
            f"High Severity: {data['summary']['high_severity_count']}",
            f"Currently Open: {data['summary']['open_incidents']}",
            "",
            "BY TYPE",
            "-" * 40
        ]

        for item in sorted(data['by_type'], key=lambda x: x['count'], reverse=True):
            lines.append(f"  {item['type']}: {item['count']} ({item['percentage']}%)")

        lines.extend(["", "BY SEVERITY", "-" * 40])
        for item in data['by_severity']:
            lines.append(f"  {item['severity']}: {item['count']} ({item['percentage']}%)")

        lines.extend(["", "BY STATUS", "-" * 40])
        for item in data['by_status']:
            lines.append(f"  {item['status']}: {item['count']} ({item['percentage']}%)")

        return "\n".join(lines)


async def get_quick_incident_summary(
    start_date: date = None,
    end_date: date = None
) -> Dict[str, Any]:
    """
    Get quick incident summary without file generation.

    Used by the quick report endpoint for real-time dashboard data.

    TODO: Replace mock data with actual repository queries.
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    generator = IncidentReportGenerator()
    data = await generator._generate_mock_data('QUICK', start_date, end_date)

    return {
        'start_date': str(start_date),
        'end_date': str(end_date),
        'total_incidents': data['summary']['total_incidents'],
        'by_type': {item['type']: item['count'] for item in data['by_type']},
        'by_severity': {item['severity']: item['count'] for item in data['by_severity']},
        'by_status': {item['status']: item['count'] for item in data['by_status']},
        'daily_average': data['summary']['daily_average'],
        'most_common_type': data['summary']['most_common_type'],
        'highest_severity_count': data['summary']['high_severity_count'],
        'generated_at': datetime.utcnow().isoformat(),
        '_stub': True
    }
