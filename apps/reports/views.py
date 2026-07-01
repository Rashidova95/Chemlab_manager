from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from django.utils.timezone import localtime
from drf_spectacular.utils import extend_schema
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.samples.models import Sample
from apps.samples.serializers import SampleDetailSerializer


@extend_schema(tags=['Reports'])
class SamplePDFReportView(generics.RetrieveAPIView):
    """
    FR-10: Namuna bo'yicha PDF hisobot.
    GET /api/v1/reports/samples/{id}/pdf/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SampleDetailSerializer
    queryset = Sample.objects.prefetch_related(
        'experiments__performed_by',
        'experiments__approved_by',
    ).select_related('received_by__profile')

    def get(self, request, *args, **kwargs):
        sample = self.get_object()
        experiments = sample.experiments.filter(status='approved')

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=2 * cm, leftMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2.5 * cm,
        )

        styles = getSampleStyleSheet()
        elements = []

        # ── Ranglar ──────────────────────────────
        BLUE = colors.HexColor('#1F5C9E')
        LIGHT_BLUE = colors.HexColor('#EBF5FB')
        GRAY = colors.HexColor('#F4F6F8')
        BORDER = colors.HexColor('#CCCCCC')
        MUTED = colors.HexColor('#6B7280')
        TEXT = colors.HexColor('#1F2937')

        # ── Uslublar ─────────────────────────────
        title_style = ParagraphStyle('T', parent=styles['Title'],
                                     fontSize=18, textColor=BLUE, spaceAfter=4, alignment=1)
        sub_style = ParagraphStyle('S', parent=styles['Normal'],
                                   fontSize=9, textColor=MUTED, spaceAfter=12, alignment=1)
        heading = ParagraphStyle('H', parent=styles['Heading2'],
                                 fontSize=12, textColor=BLUE, spaceBefore=10, spaceAfter=6)
        normal = ParagraphStyle('N', parent=styles['Normal'],
                                fontSize=9, textColor=TEXT, leading=14)
        small = ParagraphStyle('SM', parent=styles['Normal'],
                               fontSize=8, textColor=MUTED)

        # ── SARLAVHA ─────────────────────────────
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("ChemLab UZ", title_style))
        elements.append(Paragraph("Kimyo Laboratoriyasi Boshqaruv Tizimi", sub_style))
        elements.append(HRFlowable(width="100%", thickness=2, color=BLUE))
        elements.append(Spacer(1, 0.4 * cm))

        # ── LABORATORIYA VA HISOBOT MA'LUMOTI ────
        lab_name = ""
        try:
            if sample.received_by:
                lab_name = sample.received_by.profile.lab_name
        except Exception:
            pass

        if lab_name:
            elements.append(Paragraph(f"Laboratoriya: {lab_name}", heading))

        report_num = f"RPT-{sample.sample_id}-{timezone.now().strftime('%Y%m%d')}"
        report_date = localtime(timezone.now()).strftime('%d.%m.%Y %H:%M')
        elements.append(Paragraph(f"Hisobot raqami: {report_num}", small))
        elements.append(Paragraph(f"Yaratilgan: {report_date}", small))
        elements.append(Spacer(1, 0.4 * cm))

        # ── NAMUNA MA'LUMOTI ─────────────────────
        elements.append(Paragraph("Namuna ma'lumoti", heading))

        received_by_name = "—"
        if sample.received_by:
            received_by_name = (
                    sample.received_by.get_full_name() or
                    sample.received_by.email
            )

        sample_data = [
            ['Namuna ID', sample.sample_id],
            ['Nomi', sample.name],
            ['Manba turi', sample.get_source_type_display()],
            ['Holat', sample.get_status_display()],
            ['Miqdor', f"{sample.quantity} {sample.unit}"],
            ['Qabul qilgan', received_by_name],
            ['Qabul sanasi', localtime(sample.received_at).strftime('%d.%m.%Y %H:%M')],
        ]
        if sample.notes:
            sample_data.append(['Izoh', sample.notes])

        st = Table(sample_data, colWidths=[5 * cm, 12 * cm])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(st)
        elements.append(Spacer(1, 0.6 * cm))

        # ── TAJRIBALAR ────────────────────────────
        exp_count = experiments.count()
        elements.append(Paragraph(
            f"Tasdiqlangan tajribalar ({exp_count} ta)", heading
        ))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        elements.append(Spacer(1, 0.3 * cm))

        if not exp_count:
            elements.append(Paragraph(
                "Tasdiqlangan tajribalar mavjud emas.", normal
            ))
        else:
            for i, exp in enumerate(experiments, 1):
                exp_style = ParagraphStyle('ET', parent=styles['Heading3'],
                                           fontSize=11, textColor=BLUE, spaceBefore=8, spaceAfter=4)
                elements.append(Paragraph(f"{i}. {exp.title}", exp_style))

                performed = exp.performed_by.get_full_name() if exp.performed_by else "—"
                approved_by = exp.approved_by.get_full_name() if exp.approved_by else "—"
                approved_date = (
                    localtime(exp.approved_at).strftime('%d.%m.%Y %H:%M')
                    if exp.approved_at else "—"
                )

                exp_data = [
                    ['Metod', exp.method],
                    ['Maqsad', exp.objective],
                    ['Kuzatuvlar', exp.observations or "—"],
                    ['Bajargan', performed],
                    ['Tasdiqlagan', approved_by],
                    ['Tasdiqlagan sana', approved_date],
                ]
                et = Table(exp_data, colWidths=[5 * cm, 12 * cm])
                et.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), GRAY),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
                    ('PADDING', (0, 0), (-1, -1), 5),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1),
                     [colors.white, colors.HexColor('#FAFAFA')]),
                ]))
                elements.append(et)

                # Natijalar jadvali
                if exp.results:
                    elements.append(Spacer(1, 0.2 * cm))
                    elements.append(Paragraph("Tahlil natijalari:", normal))
                    res_data = [['Parametr', 'Qiymat', 'Birlik']]
                    for key, val in exp.results.items():
                        if isinstance(val, dict):
                            res_data.append([
                                key,
                                str(val.get('qiymat', '')),
                                str(val.get('birlik', ''))
                            ])
                        else:
                            res_data.append([key, str(val), ''])

                    rt = Table(res_data, colWidths=[5 * cm, 6 * cm, 6 * cm])
                    rt.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
                        ('PADDING', (0, 0), (-1, -1), 5),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                         [colors.white, LIGHT_BLUE]),
                    ]))
                    elements.append(rt)

                elements.append(Spacer(1, 0.5 * cm))

        # ── IMZO JOYI ─────────────────────────────
        elements.append(Spacer(1, 1 * cm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        elements.append(Spacer(1, 0.5 * cm))

        sign_data = [
            ['Mas\'ul shaxs:', '', 'Laboratoriya mudiri:'],
            ['', '', ''],
            ['________________', '', '________________'],
            ['(Imzo)', '', '(Imzo)'],
            ['Sana: ___/___/______', '', 'Sana: ___/___/______'],
        ]
        sign_t = Table(sign_data, colWidths=[7 * cm, 3 * cm, 7 * cm])
        sign_t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 3), (0, 3), MUTED),
            ('TEXTCOLOR', (2, 3), (2, 3), MUTED),
        ]))
        elements.append(sign_t)

        # ── FOOTER ───────────────────────────────
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(HRFlowable(width="100%", thickness=1, color=BLUE))
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph(
            f"ChemLab UZ — LIMS tizimi orqali avtomatik yaratilgan | "
            f"Hisobot: {report_num} | {timezone.now().strftime('%d.%m.%Y')}",
            small
        ))

        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{sample.sample_id}_report.pdf"'
        )
        return response
