"""
Programme Report Generator - Enrollment stats, completion rates, BTVI certifications.

Report codes: RPT-PRG-001 through RPT-PRG-003
- RPT-PRG-001: Programme Enrollment Summary
- RPT-PRG-002: Completion Rates Analysis
- RPT-PRG-003: BTVI Certification Report

NOTE: STUB implementation using mock data.
TODO: Connect to programmes module repository for real data.
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import random

from src.common.enums import OutputFormat
from src.modules.reports.generators import BaseReportGenerator, ReportOutput


class ProgrammeReportGenerator(BaseReportGenerator):
    """Generator for programme-related reports."""

    # Mock programme types
    PROGRAMME_TYPES = [
        'EDUCATION', 'VOCATIONAL', 'SUBSTANCE_ABUSE',
        'LIFE_SKILLS', 'RELIGIOUS', 'RECREATION'
    ]

    # Mock BTVI certifications
    BTVI_CERTS = [
        'Carpentry Level 1', 'Electrical Installation Level 1',
        'Plumbing Level 1', 'Auto Mechanics Level 1',
        'Computer Basics', 'Small Engine Repair',
        'Culinary Arts Level 1', 'Masonry Level 1'
    ]

    async def generate(
        self,
        params: Dict[str, Any],
        output_format: OutputFormat
    ) -> ReportOutput:
        """Generate programme report."""
        report_code = params.get('report_code', 'RPT-PRG-001')
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        # Default to YTD if no dates specified
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = date(end_date.year, 1, 1)

        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        # Generate mock programme data
        # TODO: Replace with actual repository queries
        data = await self._generate_mock_data(report_code, start_date, end_date)

        # Generate output file
        output_path = self._get_output_path(report_code, output_format)

        if output_format == OutputFormat.JSON:
            file_size = await self._write_json(output_path, data)
        elif output_format == OutputFormat.CSV:
            file_size = await self._write_programme_csv(output_path, data)
        elif output_format == OutputFormat.EXCEL:
            file_size = await self._write_stub_excel(output_path, {
                'Summary': [data['summary']],
                'By Type': data['by_type'],
                'Top Programmes': data['top_programmes'],
                'BTVI Certifications': data['btvi_certifications']
            })
        else:  # PDF
            content = self._format_programme_text(data)
            file_size = await self._write_stub_pdf(
                output_path,
                f"Programme Report - {start_date} to {end_date}",
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
                'total_enrolled': data['summary']['total_enrolled']
            }
        )

    async def _generate_mock_data(
        self,
        report_code: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Generate mock programme data."""
        # TODO: Replace with actual queries to programmes repository

        seed = hash(f"{start_date}{end_date}") % 1000
        random.seed(seed)

        # Programme counts
        total_programmes = random.randint(15, 25)
        active_programmes = int(total_programmes * 0.8)

        # Enrollment
        total_enrolled = random.randint(200, 350)
        completed_ytd = random.randint(80, 150)
        dropped = random.randint(10, 30)
        in_progress = total_enrolled - completed_ytd - dropped

        # Completion rate
        completion_rate = round(completed_ytd / (completed_ytd + dropped) * 100, 1) if (completed_ytd + dropped) > 0 else 0

        # By type distribution
        type_data = []
        remaining_enrolled = total_enrolled
        for i, prog_type in enumerate(self.PROGRAMME_TYPES[:-1]):
            if remaining_enrolled <= 0:
                type_data.append({'type': prog_type, 'programmes': 0, 'enrolled': 0, 'completed': 0})
            else:
                progs = random.randint(2, 5)
                enrolled = min(int(total_enrolled * random.uniform(0.1, 0.25)), remaining_enrolled)
                completed = int(enrolled * random.uniform(0.3, 0.6))
                type_data.append({
                    'type': prog_type,
                    'programmes': progs,
                    'enrolled': enrolled,
                    'completed': completed,
                    'completion_rate': round(completed / enrolled * 100, 1) if enrolled > 0 else 0
                })
                remaining_enrolled -= enrolled

        # Last type gets remainder
        type_data.append({
            'type': self.PROGRAMME_TYPES[-1],
            'programmes': random.randint(1, 3),
            'enrolled': max(0, remaining_enrolled),
            'completed': int(remaining_enrolled * 0.4) if remaining_enrolled > 0 else 0,
            'completion_rate': 40.0 if remaining_enrolled > 0 else 0
        })

        # Top programmes
        top_programmes = [
            {'name': 'GED Preparation', 'type': 'EDUCATION', 'enrolled': random.randint(40, 60), 'completion_rate': random.uniform(55, 75)},
            {'name': 'Carpentry Fundamentals', 'type': 'VOCATIONAL', 'enrolled': random.randint(25, 40), 'completion_rate': random.uniform(60, 80)},
            {'name': 'Substance Abuse Recovery', 'type': 'SUBSTANCE_ABUSE', 'enrolled': random.randint(30, 50), 'completion_rate': random.uniform(45, 65)},
            {'name': 'Computer Literacy', 'type': 'VOCATIONAL', 'enrolled': random.randint(20, 35), 'completion_rate': random.uniform(70, 85)},
            {'name': 'Anger Management', 'type': 'LIFE_SKILLS', 'enrolled': random.randint(25, 40), 'completion_rate': random.uniform(50, 70)}
        ]
        for prog in top_programmes:
            prog['completion_rate'] = round(prog['completion_rate'], 1)

        # BTVI certifications
        btvi_total = random.randint(30, 60)
        btvi_certs = []
        remaining_btvi = btvi_total
        for cert in self.BTVI_CERTS[:6]:
            if remaining_btvi <= 0:
                break
            count = random.randint(3, 12)
            count = min(count, remaining_btvi)
            btvi_certs.append({'certification': cert, 'awarded': count})
            remaining_btvi -= count

        return {
            'report_code': report_code,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'summary': {
                'total_programmes': total_programmes,
                'active_programmes': active_programmes,
                'total_enrolled': total_enrolled,
                'in_progress': in_progress,
                'completed_ytd': completed_ytd,
                'dropped': dropped,
                'completion_rate': completion_rate,
                'btvi_certifications_ytd': btvi_total
            },
            'by_type': type_data,
            'top_programmes': sorted(top_programmes, key=lambda x: x['enrolled'], reverse=True),
            'btvi_certifications': btvi_certs,
            '_stub': True,
            '_message': 'STUB: Mock data for development'
        }

    async def _write_programme_csv(self, path, data: Dict[str, Any]) -> int:
        """Write programme data as CSV."""
        headers = ['Category', 'Item', 'Value', 'Percentage']
        rows = []

        # Summary
        rows.append(['Summary', 'Total Programmes', data['summary']['total_programmes'], '-'])
        rows.append(['Summary', 'Total Enrolled', data['summary']['total_enrolled'], '-'])
        rows.append(['Summary', 'Completed YTD', data['summary']['completed_ytd'], '-'])
        rows.append(['Summary', 'Completion Rate', '-', data['summary']['completion_rate']])
        rows.append(['Summary', 'BTVI Certifications', data['summary']['btvi_certifications_ytd'], '-'])

        # By type
        for item in data['by_type']:
            rows.append(['Type', item['type'], item['enrolled'], item['completion_rate']])

        # Top programmes
        for prog in data['top_programmes']:
            rows.append(['Top Programme', prog['name'], prog['enrolled'], prog['completion_rate']])

        # BTVI
        for cert in data['btvi_certifications']:
            rows.append(['BTVI Cert', cert['certification'], cert['awarded'], '-'])

        return await self._write_csv(path, rows, headers)

    def _format_programme_text(self, data: Dict[str, Any]) -> str:
        """Format programme data as text for PDF."""
        lines = [
            f"Period: {data['start_date']} to {data['end_date']}",
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Programmes: {data['summary']['total_programmes']} ({data['summary']['active_programmes']} active)",
            f"Total Enrolled: {data['summary']['total_enrolled']}",
            f"  - In Progress: {data['summary']['in_progress']}",
            f"  - Completed: {data['summary']['completed_ytd']}",
            f"  - Dropped: {data['summary']['dropped']}",
            f"Completion Rate: {data['summary']['completion_rate']}%",
            f"BTVI Certifications: {data['summary']['btvi_certifications_ytd']}",
            "",
            "BY PROGRAMME TYPE",
            "-" * 40
        ]

        for item in data['by_type']:
            lines.append(f"  {item['type']}: {item['enrolled']} enrolled, {item['completion_rate']}% completion")

        lines.extend(["", "TOP 5 PROGRAMMES BY ENROLLMENT", "-" * 40])
        for i, prog in enumerate(data['top_programmes'], 1):
            lines.append(f"  {i}. {prog['name']} ({prog['type']})")
            lines.append(f"     Enrolled: {prog['enrolled']}, Completion: {prog['completion_rate']}%")

        lines.extend(["", "BTVI CERTIFICATIONS AWARDED", "-" * 40])
        for cert in data['btvi_certifications']:
            lines.append(f"  {cert['certification']}: {cert['awarded']}")

        return "\n".join(lines)


async def get_quick_programme_summary() -> Dict[str, Any]:
    """
    Get quick programme summary without file generation.

    Used by the quick report endpoint for real-time dashboard data.

    TODO: Replace mock data with actual repository queries.
    """
    end_date = date.today()
    start_date = date(end_date.year, 1, 1)

    generator = ProgrammeReportGenerator()
    data = await generator._generate_mock_data('QUICK', start_date, end_date)

    return {
        'total_programmes': data['summary']['total_programmes'],
        'total_enrolled': data['summary']['total_enrolled'],
        'total_completed_ytd': data['summary']['completed_ytd'],
        'completion_rate': data['summary']['completion_rate'],
        'btvi_certifications_ytd': data['summary']['btvi_certifications_ytd'],
        'by_programme_type': {item['type']: item['enrolled'] for item in data['by_type']},
        'top_programmes': data['top_programmes'][:5],
        'generated_at': datetime.utcnow().isoformat(),
        '_stub': True
    }
