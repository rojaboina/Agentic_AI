from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT_DIR = Path("/Users/roja/Documents/Agentic_AI/Final_Project/sample_patient_data")
HISTORY_YEARS = [2022, 2023, 2024, 2025, 2026]


CMP_RANGES = [
    ("Sodium", "135 - 145 mmol/L", "mmol/L"),
    ("Potassium", "3.5 - 5.0 mmol/L", "mmol/L"),
    ("Chloride", "98 - 108 mmol/L", "mmol/L"),
    ("Carbon Dioxide (CO2)", "21 - 30 mmol/L", "mmol/L"),
    ("Urea Nitrogen (BUN)", "7 - 20 mg/dL", "mg/dL"),
    ("Creatinine", "0.4 - 1.0 mg/dL", "mg/dL"),
    ("Glucose", "70 - 140 mg/dL", "mg/dL"),
    ("Calcium", "8.7 - 10.2 mg/dL", "mg/dL"),
    ("AST (Aspartate Aminotransferase)", "15 - 41 U/L", "U/L"),
    ("ALT (Alanine Aminotransferase)", "10 - 39 U/L", "U/L"),
    ("Bilirubin, Total", "0.4 - 1.5 mg/dL", "mg/dL"),
    ("Alk Phos (Alkaline Phosphatase)", "24 - 110 U/L", "U/L"),
    ("Albumin", "3.5 - 4.8 g/dL", "g/dL"),
    ("Protein, Total", "6.2 - 8.1 g/dL", "g/dL"),
    ("Anion Gap", "3 - 12 mmol/L", "mmol/L"),
    ("BUN/CREA Ratio", "6 - 27", ""),
    ("Glomerular Filtration Rate (eGFR)", "> 60 mL/min/1.73 sq m", "mL/min/1.73 sq m"),
]


RANGE_BOUNDS = {
    "Sodium": (135, 145),
    "Potassium": (3.5, 5.0),
    "Chloride": (98, 108),
    "Carbon Dioxide (CO2)": (21, 30),
    "Urea Nitrogen (BUN)": (7, 20),
    "Creatinine": (0.4, 1.0),
    "Glucose": (70, 140),
    "Calcium": (8.7, 10.2),
    "AST (Aspartate Aminotransferase)": (15, 41),
    "ALT (Alanine Aminotransferase)": (10, 39),
    "Bilirubin, Total": (0.4, 1.5),
    "Alk Phos (Alkaline Phosphatase)": (24, 110),
    "Albumin": (3.5, 4.8),
    "Protein, Total": (6.2, 8.1),
    "Anion Gap": (3, 12),
    "BUN/CREA Ratio": (6, 27),
    "Glomerular Filtration Rate (eGFR)": (60, 120),
    "Cholesterol, Total": (0, 200),
    "LDL Calculated": (0, 100),
    "HDL": (40, 80),
    "Triglyceride": (0, 150),
    "Vitamin D Total, 25OH": (30, 100),
    "Hemoglobin A1C": (0, 5.7),
    "Average Blood Glucose (Calculated From HgBA1c Level)": (70, 117),
    "Thyroid Stimulating Hormone (TSH)": (0.34, 5.66),
    "Thyroxine, Free (FT4)": (0.52, 1.21),
    "Triiodothyronine, Free (FT3)": (2.3, 4.2),
    "Vitamin B12": (180, 914),
    "Iron": (28, 170),
    "Total Iron Binding Capacity (TIBC)": (261, 478),
    "Percent Transferrin Saturation": (15, 55),
}


patients = [
    {
        "folder": "P001_Ava_Patel",
        "profile": {
            "Patient ID": "P001",
            "Name": "Ava Patel",
            "Date of Birth": "1989-04-12",
            "Age": "37",
            "Gender": "Female",
            "Height": "165 cm",
            "Weight": "64 kg",
            "BMI": "23.5",
            "Existing Conditions": "None reported",
            "Medications": "None",
            "Primary Care Provider": "Dr. Elena Brooks",
        },
        "cmp": [139, 4.2, 102, 25, 13, 0.8, 91, 9.4, 22, 18, 0.8, 67, 4.3, 7.1, 10, 16, 88],
        "lipid": [172, 89, 63, 98],
        "a1c": [5.1, 100],
        "thyroid": [2.1, 1.2, 3.2],
        "vitamin_d": [36],
        "b12": [520],
        "iron": [84, 342, 25],
    },
    {
        "folder": "P002_Michael_Johnson",
        "profile": {
            "Patient ID": "P002",
            "Name": "Michael Johnson",
            "Date of Birth": "1978-11-03",
            "Age": "47",
            "Gender": "Male",
            "Height": "178 cm",
            "Weight": "92 kg",
            "BMI": "29.0",
            "Existing Conditions": "Hypertension; family history of cardiovascular disease",
            "Medications": "Lisinopril 10 mg daily",
            "Primary Care Provider": "Dr. Samuel Lee",
        },
        "cmp": [138, 4.8, 101, 24, 19, 1.0, 132, 9.7, 39, 44, 1.1, 94, 4.1, 7.4, 13, 19, 76],
        "lipid": [256, 174, 38, 226],
        "a1c": [6.1, 128],
        "thyroid": [2.8, 1.1, 3.0],
        "vitamin_d": [24],
        "b12": [410],
        "iron": [62, 389, 16],
    },
    {
        "folder": "P003_Sofia_Ramirez",
        "profile": {
            "Patient ID": "P003",
            "Name": "Sofia Ramirez",
            "Date of Birth": "1994-02-24",
            "Age": "32",
            "Gender": "Female",
            "Height": "160 cm",
            "Weight": "70 kg",
            "BMI": "27.3",
            "Existing Conditions": "Hypothyroidism",
            "Medications": "Levothyroxine 50 mcg daily",
            "Primary Care Provider": "Dr. Priya Shah",
        },
        "cmp": [137, 4.1, 100, 23, 10, 0.7, 96, 9.1, 20, 15, 0.6, 61, 4.0, 6.8, 14, 14, 95],
        "lipid": [198, 118, 51, 142],
        "a1c": [5.4, 108],
        "thyroid": [7.4, 0.7, 2.1],
        "vitamin_d": [28],
        "b12": [360],
        "iron": [38, 442, 9],
    },
    {
        "folder": "P004_Daniel_Kim",
        "profile": {
            "Patient ID": "P004",
            "Name": "Daniel Kim",
            "Date of Birth": "2001-08-09",
            "Age": "24",
            "Gender": "Male",
            "Height": "181 cm",
            "Weight": "76 kg",
            "BMI": "23.2",
            "Existing Conditions": "None reported",
            "Medications": "None",
            "Primary Care Provider": "Dr. Hana Morris",
        },
        "cmp": [141, 3.9, 104, 27, 14, 0.9, 86, 9.6, 24, 21, 0.9, 72, 4.5, 7.2, 10, 16, 102],
        "lipid": [184, 104, 44, 130],
        "a1c": [5.0, 96],
        "thyroid": [1.6, 1.1, 3.5],
        "vitamin_d": [18],
        "b12": [190],
        "iron": [71, 351, 20],
    },
    {
        "folder": "P005_Grace_Wilson",
        "profile": {
            "Patient ID": "P005",
            "Name": "Grace Wilson",
            "Date of Birth": "1963-12-19",
            "Age": "62",
            "Gender": "Female",
            "Height": "157 cm",
            "Weight": "81 kg",
            "BMI": "32.9",
            "Existing Conditions": "Type 2 diabetes; hyperlipidemia",
            "Medications": "Metformin 500 mg twice daily; Atorvastatin 20 mg daily",
            "Primary Care Provider": "Dr. Marcus Chen",
        },
        "cmp": [136, 4.9, 99, 22, 21, 1.1, 168, 9.3, 35, 37, 1.0, 105, 3.8, 6.9, 15, 19, 61],
        "lipid": [218, 132, 46, 188],
        "a1c": [7.8, 177],
        "thyroid": [3.8, 0.9, 2.5],
        "vitamin_d": [31],
        "b12": [260],
        "iron": [52, 404, 13],
    },
]


HISTORY_OVERRIDES = {
    "P001": {
        2022: {"cmp": [139, 4.1, 103, 24, 12, 0.8, 88, 9.3, 20, 17, 0.7, 63, 4.2, 7.0, 9, 15, 92], "lipid": [168, 86, 61, 92], "a1c": [5.0, 97], "thyroid": [2.0, 1.2, 3.1], "vitamin_d": [34], "b12": [505], "iron": [82, 338, 24]},
        2023: {"cmp": [138, 4.0, 102, 25, 13, 0.8, 90, 9.4, 21, 18, 0.8, 64, 4.3, 7.1, 10, 16, 90], "lipid": [170, 88, 62, 95], "a1c": [5.0, 98], "thyroid": [2.1, 1.2, 3.2], "vitamin_d": [35], "b12": [512], "iron": [83, 340, 24]},
        2024: {"cmp": [140, 4.2, 103, 25, 12, 0.8, 89, 9.5, 22, 18, 0.8, 66, 4.3, 7.0, 10, 15, 89], "lipid": [171, 88, 63, 96], "a1c": [5.1, 99], "thyroid": [2.0, 1.2, 3.3], "vitamin_d": [35], "b12": [518], "iron": [84, 341, 25]},
        2025: {"cmp": [139, 4.2, 102, 25, 13, 0.8, 90, 9.4, 22, 18, 0.8, 66, 4.3, 7.1, 10, 16, 88], "lipid": [172, 89, 63, 97], "a1c": [5.1, 100], "thyroid": [2.1, 1.2, 3.2], "vitamin_d": [36], "b12": [520], "iron": [84, 342, 25]},
    },
    "P002": {
        2022: {"cmp": [139, 4.4, 102, 25, 15, 0.9, 108, 9.5, 28, 31, 0.9, 82, 4.2, 7.2, 10, 17, 88], "lipid": [211, 134, 44, 158], "a1c": [5.6, 114], "thyroid": [2.3, 1.1, 3.1], "vitamin_d": [31], "b12": [455], "iron": [73, 360, 20]},
        2023: {"cmp": [139, 4.5, 102, 24, 16, 0.9, 116, 9.6, 31, 35, 1.0, 86, 4.2, 7.3, 11, 18, 84], "lipid": [224, 146, 42, 176], "a1c": [5.7, 117], "thyroid": [2.4, 1.1, 3.0], "vitamin_d": [29], "b12": [440], "iron": [70, 368, 19]},
        2024: {"cmp": [138, 4.6, 101, 24, 17, 1.0, 121, 9.6, 34, 39, 1.0, 89, 4.1, 7.3, 12, 18, 81], "lipid": [237, 156, 41, 194], "a1c": [5.9, 123], "thyroid": [2.6, 1.1, 3.0], "vitamin_d": [27], "b12": [430], "iron": [67, 377, 18]},
        2025: {"cmp": [138, 4.7, 101, 24, 18, 1.0, 126, 9.7, 36, 41, 1.1, 91, 4.1, 7.4, 13, 18, 78], "lipid": [246, 165, 40, 210], "a1c": [6.0, 126], "thyroid": [2.7, 1.1, 3.0], "vitamin_d": [25], "b12": [420], "iron": [64, 383, 17]},
    },
    "P003": {
        2022: {"cmp": [138, 4.0, 101, 24, 11, 0.7, 90, 9.2, 19, 15, 0.6, 59, 4.1, 6.9, 10, 16, 104], "lipid": [176, 96, 55, 112], "a1c": [5.2, 103], "thyroid": [3.9, 1.0, 3.0], "vitamin_d": [35], "b12": [430], "iron": [58, 370, 16]},
        2023: {"cmp": [138, 4.0, 101, 24, 10, 0.7, 92, 9.2, 19, 15, 0.6, 60, 4.1, 6.9, 11, 15, 101], "lipid": [184, 104, 54, 125], "a1c": [5.3, 105], "thyroid": [4.8, 0.9, 2.8], "vitamin_d": [32], "b12": [405], "iron": [50, 392, 13]},
        2024: {"cmp": [137, 4.1, 100, 23, 10, 0.7, 94, 9.1, 20, 15, 0.6, 60, 4.0, 6.8, 12, 14, 98], "lipid": [190, 110, 53, 134], "a1c": [5.3, 106], "thyroid": [5.8, 0.8, 2.5], "vitamin_d": [30], "b12": [385], "iron": [44, 415, 11]},
        2025: {"cmp": [137, 4.1, 100, 23, 10, 0.7, 95, 9.1, 20, 15, 0.6, 61, 4.0, 6.8, 13, 14, 96], "lipid": [195, 115, 52, 139], "a1c": [5.4, 108], "thyroid": [6.6, 0.8, 2.3], "vitamin_d": [29], "b12": [372], "iron": [40, 432, 10]},
    },
    "P004": {
        2022: {"cmp": [140, 4.0, 103, 26, 14, 0.9, 84, 9.6, 23, 20, 0.8, 70, 4.5, 7.2, 9, 16, 105], "lipid": [174, 95, 47, 112], "a1c": [5.0, 95], "thyroid": [1.5, 1.1, 3.4], "vitamin_d": [32], "b12": [310], "iron": [82, 340, 24]},
        2023: {"cmp": [141, 3.9, 104, 26, 14, 0.9, 85, 9.6, 23, 20, 0.9, 71, 4.5, 7.2, 10, 16, 104], "lipid": [178, 99, 46, 118], "a1c": [5.0, 96], "thyroid": [1.5, 1.1, 3.5], "vitamin_d": [27], "b12": [270], "iron": [78, 344, 23]},
        2024: {"cmp": [141, 3.9, 104, 27, 14, 0.9, 85, 9.6, 24, 21, 0.9, 71, 4.5, 7.2, 10, 16, 103], "lipid": [180, 101, 45, 124], "a1c": [5.0, 96], "thyroid": [1.6, 1.1, 3.5], "vitamin_d": [23], "b12": [230], "iron": [75, 348, 22]},
        2025: {"cmp": [141, 3.9, 104, 27, 14, 0.9, 86, 9.6, 24, 21, 0.9, 72, 4.5, 7.2, 10, 16, 102], "lipid": [182, 103, 44, 128], "a1c": [5.0, 96], "thyroid": [1.6, 1.1, 3.5], "vitamin_d": [20], "b12": [205], "iron": [72, 350, 21]},
    },
    "P005": {
        2022: {"cmp": [138, 4.6, 101, 23, 17, 0.9, 132, 9.4, 28, 30, 0.8, 88, 4.0, 7.0, 12, 19, 78], "lipid": [196, 112, 52, 142], "a1c": [6.7, 146], "thyroid": [3.0, 1.0, 2.9], "vitamin_d": [36], "b12": [330], "iron": [70, 365, 19]},
        2023: {"cmp": [137, 4.7, 100, 23, 18, 1.0, 142, 9.4, 30, 32, 0.9, 94, 3.9, 7.0, 13, 18, 73], "lipid": [204, 120, 50, 156], "a1c": [7.0, 154], "thyroid": [3.2, 1.0, 2.8], "vitamin_d": [34], "b12": [305], "iron": [63, 378, 17]},
        2024: {"cmp": [137, 4.8, 100, 22, 19, 1.0, 151, 9.3, 32, 34, 0.9, 98, 3.9, 6.9, 14, 19, 69], "lipid": [210, 126, 48, 168], "a1c": [7.3, 163], "thyroid": [3.4, 0.9, 2.7], "vitamin_d": [33], "b12": [285], "iron": [58, 390, 15]},
        2025: {"cmp": [136, 4.8, 99, 22, 20, 1.1, 160, 9.3, 34, 36, 1.0, 102, 3.8, 6.9, 15, 18, 65], "lipid": [214, 129, 47, 178], "a1c": [7.5, 169], "thyroid": [3.6, 0.9, 2.6], "vitamin_d": [32], "b12": [270], "iron": [54, 398, 14]},
    },
}


def style_map() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=17, leading=21),
        "panel": ParagraphStyle("Panel", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, spaceBefore=8),
        "test": ParagraphStyle("Test", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=10.5, leading=13),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.2, leading=12),
        "small": ParagraphStyle("Small", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#667085")),
        "link": ParagraphStyle("Link", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=12, textColor=colors.HexColor("#F59E0B")),
    }


def build_patient_info_pdf(folder: Path, profile: dict[str, str]) -> None:
    styles = style_map()
    doc = SimpleDocTemplate(str(folder / "patient_information.pdf"), pagesize=LETTER, leftMargin=0.6 * inch, rightMargin=0.6 * inch)
    data = [["Field", "Value"]] + [[key, value] for key, value in profile.items()]
    table = Table(data, colWidths=[2.2 * inch, 4.3 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D5DD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    doc.build([Paragraph("Patient Information", styles["title"]), Spacer(1, 12), table])


class MetricCard(Flowable):
    def __init__(self, name: str, normal_range: str, value: str, unit: str, low: float | None = None, high: float | None = None):
        super().__init__()
        self.name = name
        self.normal_range = normal_range
        self.value = value
        self.unit = unit
        self.low = low
        self.high = high
        self.width = 6.4 * inch
        self.height = 1.35 * inch

    def draw(self) -> None:
        canvas = self.canv
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D0D5DD"))
        canvas.setFillColor(colors.white)
        canvas.roundRect(0, 0, self.width, self.height, 6, stroke=1, fill=1)

        canvas.setFillColor(colors.HexColor("#333333"))
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(0.15 * inch, self.height - 0.28 * inch, self.name)

        canvas.setFillColor(colors.HexColor("#005EB8"))
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(self.width - 0.15 * inch, self.height - 0.30 * inch, "View trends")

        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.setFont("Helvetica", 8.5)
        canvas.drawString(0.15 * inch, self.height - 0.62 * inch, f"Normal range: {self.normal_range}")

        value_text = f"{self.value} {self.unit}".strip()
        bar_x = 1.45 * inch
        bar_y = 0.26 * inch
        bar_w = 3.55 * inch
        bar_h = 0.12 * inch
        canvas.setFillColor(colors.HexColor("#F2CF2F"))
        canvas.rect(bar_x, bar_y, bar_w, bar_h, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#16A34A"))
        canvas.rect(bar_x + bar_w * 0.25, bar_y, bar_w * 0.50, bar_h, stroke=0, fill=1)
        canvas.setStrokeColor(colors.HexColor("#9A8700"))
        canvas.rect(bar_x, bar_y, bar_w, bar_h, stroke=1, fill=0)

        marker_x = bar_x + bar_w * 0.5
        if self.low is not None and self.high is not None:
            span = self.high - self.low
            if span > 0:
                display_value = float(str(self.value).replace(">", "").replace("<", ""))
                min_axis = self.low - span * 0.5
                max_axis = self.high + span * 0.5
                marker_x = bar_x + max(0, min(1, (display_value - min_axis) / (max_axis - min_axis))) * bar_w

        canvas.setFillColor(colors.HexColor("#16A34A"))
        canvas.roundRect(marker_x - 0.16 * inch, bar_y + 0.28 * inch, 0.32 * inch, 0.24 * inch, 8, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(marker_x, bar_y + 0.35 * inch, self.value)

        canvas.setFillColor(colors.HexColor("#333333"))
        canvas.line(marker_x - 0.08 * inch, bar_y + 0.23 * inch, marker_x + 0.08 * inch, bar_y + 0.23 * inch)
        canvas.line(marker_x - 0.08 * inch, bar_y + 0.23 * inch, marker_x, bar_y + 0.12 * inch)
        canvas.line(marker_x + 0.08 * inch, bar_y + 0.23 * inch, marker_x, bar_y + 0.12 * inch)

        if self.low is not None:
            canvas.setFillColor(colors.HexColor("#667085"))
            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(bar_x + bar_w * 0.25, bar_y - 0.18 * inch, format_bound(self.low))
        if self.high is not None:
            canvas.drawCentredString(bar_x + bar_w * 0.75, bar_y - 0.18 * inch, format_bound(self.high))

        canvas.setFillColor(colors.HexColor("#333333"))
        canvas.setFont("Helvetica", 8.5)
        canvas.drawRightString(self.width - 0.15 * inch, 0.12 * inch, value_text)
        canvas.restoreState()


def format_bound(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value).rstrip("0").rstrip(".")



def trend_link(metric_name: str) -> str:
    return "<u>View trends</u>"


def portal_metric(styles: dict[str, ParagraphStyle], name: str, normal_range: str, value: str = "", unit: str = "") -> list:
    low, high = RANGE_BOUNDS.get(name, (None, None))
    visual_range = normal_range
    if not visual_range and low is not None and high is not None:
        visual_range = f"{format_bound(low)} - {format_bound(high)} {unit}".strip()
    blocks = [
        Paragraph(name, styles["test"]),
        Paragraph(trend_link(name), styles["link"]),
    ]
    if visual_range:
        blocks.append(Paragraph(f"Normal range: {visual_range}", styles["body"]))
    if value:
        blocks.append(Spacer(1, 6))
        blocks.append(MetricCard(name, visual_range, value, unit, low, high))
    blocks.append(Spacer(1, 18))
    return blocks


def add_cmp(story: list, styles: dict[str, ParagraphStyle], values: list) -> None:
    story.append(Paragraph("COMPREHENSIVE METABOLIC PANEL (CMP)", styles["panel"]))
    story.append(Paragraph("Results", styles["body"]))
    story.append(Spacer(1, 10))
    for (name, normal_range, unit), value in zip(CMP_RANGES, values):
        story.extend(portal_metric(styles, name, normal_range, str(value), unit))
        if name == "Glucose":
            story.append(
                Paragraph(
                    "Interpretive Data:<br/>"
                    "Above is the NONFASTING reference range.<br/><br/>"
                    "Below are the FASTING reference ranges:<br/>"
                    "NORMAL: 70-99 mg/dL<br/>"
                    "PREDIABETES: 100-125 mg/dL<br/>"
                    "DIABETES: > 125 mg/dL",
                    styles["body"],
                )
            )
            story.append(Spacer(1, 14))
        if name == "Glomerular Filtration Rate (eGFR)":
            story.append(
                Paragraph(
                    "CKD-EPI (2021) does not include patient's race in the calculation of eGFR. "
                    "Monitoring changes of plasma creatinine and eGFR over time is useful for monitoring kidney function. "
                    "This change was made on 3/1/2022.<br/><br/>"
                    "Interpretive Ranges for eGFR(CKD-EPI 2021):<br/><br/>"
                    "eGFR: > 60 mL/min/1.73 sq m - Normal<br/>"
                    "eGFR: 30 - 59 mL/min/1.73 sq m - Moderately Decreased<br/>"
                    "eGFR: 15 - 29 mL/min/1.73 sq m - Severely Decreased<br/>"
                    "eGFR: < 15 mL/min/1.73 sq m - Kidney Failure<br/><br/>"
                    "Note: These eGFR calculations do not apply in acute situations when eGFR is changing rapidly or in patients on dialysis.",
                    styles["body"],
                )
            )
            story.append(Spacer(1, 14))


def add_lipid_panel(story: list, styles: dict[str, ParagraphStyle], values: list) -> None:
    total, ldl, hdl, triglyceride = values
    story.append(PageBreak())
    story.append(Paragraph("Lipid panel:", styles["panel"]))
    story.append(Paragraph("Results", styles["body"]))
    story.append(Spacer(1, 10))
    story.extend(portal_metric(styles, "Cholesterol, Total", "below 200 mg/dL", str(total), "mg/dL"))
    story.append(
        Paragraph(
            "Comment: The significance of total cholesterol depends on the values of individual components including HDL, LDL, non-HDL, and triglycerides. "
            "A fasting or non-fasting lipid panel, including total, HDL, and LDL cholesterol, and triglycerides, is recommended to screen and monitor lipid-related risk.<br/>"
            "Desirable: &lt;200 mg/dL<br/>Borderline High: 200-239 mg/dL<br/>High: &gt;=240 mg/dL<br/>Ref: NCEP guidelines",
            styles["body"],
        )
    )
    story.append(Spacer(1, 14))
    story.extend(portal_metric(styles, "LDL Calculated", "below 100 mg/dL", str(ldl), "mg/dL"))
    story.append(
        Paragraph(
            "&lt;70 mg/dL Desired target for prior heart disease, stroke, and those at high-risk. Even lower levels may be recommended to decrease the risk of heart attack and stroke.<br/>"
            "70-159 mg/dL Comprehensive cardiovascular risk assessment is recommended. Statin therapy may be advised based on risk factors.<br/>"
            "Desirable: &lt;100 mg/dL<br/>Above desirable: 100-129 mg/dL<br/>Borderline high: 130-159 mg/dL<br/>"
            "160-189 mg/dL Moderately elevated LDL level. Statin therapy is recommended if other risk factors are present.<br/>"
            "&gt;=190 mg/dL Severely elevated LDL level. High long-term risk of heart disease and stroke. High-intensity statin therapy is recommended for most people. Consider specialist referral.<br/>"
            "*A healthy diet and exercise are recommended for all to reduce heart disease risk. Statin choice should be based on patient preference after patient-provider discussions.<br/>"
            "Ref: 2018 ACC/AHA and the NCEP guidelines",
            styles["body"],
        )
    )
    story.append(Spacer(1, 14))
    story.extend(portal_metric(styles, "HDL", "", str(hdl), "mg/dL"))
    story.append(Paragraph("People with low HDL levels are at increased risk of heart disease:<br/>&lt;50 mg/dL for Women<br/>&lt;40 mg/dL for Men", styles["body"]))
    story.append(Spacer(1, 14))
    story.extend(portal_metric(styles, "Triglyceride", "below 150 mg/dL", str(triglyceride), "mg/dL"))
    story.append(
        Paragraph(
            "&lt;150 mg/dL Normal<br/>"
            "150-499 mg/dL High Triglycerides. Risk of heart disease may be increased. Address reversible causes (eg sugar in foods and beverages, alcohol, and diabetes control). Medication may be appropriate based on other clinical factors.<br/>"
            "&gt;=500 mg/dL Very High Triglycerides. Risk of heart disease and pancreatitis increased. Address reversible causes as above. Medication to lower triglycerides usually advised.<br/>"
            "*Ranges provided for adults, pediatric guidelines vary.",
            styles["body"],
        )
    )


def add_vitamin_d(story: list, styles: dict[str, ParagraphStyle], values: list) -> None:
    story.append(PageBreak())
    story.append(Paragraph("VITAMIN D 25 HYDROXY", styles["panel"]))
    story.append(Paragraph("Results", styles["body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Bone and Mineral Metabolism: Vitamin D<br/><br/>25 OH Vitamin D Status<br/>&lt;10 ng/mL Deficiency<br/>10-30 ng/mL Insufficiency<br/>30-100 ng/mL Sufficiency<br/>&gt;100 ng/mL Toxicity", styles["body"]))
    story.append(Spacer(1, 14))
    story.extend(portal_metric(styles, "Vitamin D Total, 25OH", "30 - 100 ng/ml", str(values[0]), "ng/mL"))


def add_a1c(story: list, styles: dict[str, ParagraphStyle], values: list) -> None:
    story.append(PageBreak())
    story.append(Paragraph("HEMOGLOBIN A1C", styles["panel"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Results", styles["body"]))
    story.append(
        Paragraph(
            "Between 5.7% and 6.4% is suggestive of Pre-Diabetes or controlled Diabetes.<br/>"
            "Greater than or equal to 6.5% is suggestive of Diabetes, and if more than one value, diagnostic.<br/><br/>"
            "Accuracy may be reduced by anemia, hemoglobinopathy, recent transfusion, sickle cell, artificial heart valve, dialysis, TIPS, severe hyperglycemia, etc.",
            styles["body"],
        )
    )
    story.append(Spacer(1, 14))
    story.extend(portal_metric(styles, "Hemoglobin A1C", "below 5.7 %", str(values[0]), "%"))
    story.extend(portal_metric(styles, "Average Blood Glucose (Calculated From HgBA1c Level)", "", str(values[1]), "mg/dL"))


def add_thyroid(story: list, styles: dict[str, ParagraphStyle], values: list) -> None:
    story.append(PageBreak())
    story.append(Paragraph("Thyroid Hormone Tests", styles["panel"]))
    story.append(Paragraph("Collected on Jun 17, 2024 9:38 AM", styles["body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Results", styles["body"]))
    story.append(Spacer(1, 10))
    story.extend(portal_metric(styles, "Thyroid Stimulating Hormone (TSH)", "0.34 - 5.66 uIU/mL", str(values[0]), "uIU/mL"))
    story.extend(portal_metric(styles, "Thyroxine, Free (FT4)", "0.52 - 1.21 ng/dL", str(values[1]), "ng/dL"))


def add_b12(story: list, styles: dict[str, ParagraphStyle], values: list) -> None:
    story.append(PageBreak())
    story.append(Paragraph("VITAMIN B12", styles["panel"]))
    story.append(Paragraph("Collected on Jun 17, 2024 9:38 AM", styles["body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Results", styles["body"]))
    story.append(Spacer(1, 10))
    story.extend(portal_metric(styles, "Vitamin B12", "180 - 914 pg/mL", str(values[0]), "pg/mL"))


def add_iron(story: list, styles: dict[str, ParagraphStyle], values: list) -> None:
    story.append(PageBreak())
    story.append(Paragraph("IRON AND TOTAL IRON BINDING CAPACITY (TIBC)", styles["panel"]))
    story.append(Paragraph("Collected on Jun 17, 2024 9:38 AM", styles["body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Results", styles["body"]))
    story.append(Spacer(1, 10))
    story.extend(portal_metric(styles, "Iron", "28 - 170 mcg/dL", str(values[0]), "mcg/dL"))
    story.extend(portal_metric(styles, "Total Iron Binding Capacity (TIBC)", "261 - 478 mcg/dL", str(values[1]), "mcg/dL"))
    story.extend(portal_metric(styles, "Percent Transferrin Saturation", "15 - 55 %", str(values[2]), "%"))


def build_lab_results_pdf(folder: Path, patient: dict, year: int, filename: str) -> None:
    styles = style_map()
    profile = patient["profile"]
    doc = SimpleDocTemplate(
        str(folder / filename),
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    story = [
        Paragraph("Test Results", styles["title"]),
        Paragraph(f"Patient: {profile['Name']} | DOB: {profile['Date of Birth']} | Patient ID: {profile['Patient ID']}", styles["small"]),
        Paragraph(f"Collected: {year}-06-20 | Source: Patient portal sample export", styles["small"]),
        Spacer(1, 14),
    ]
    add_cmp(story, styles, patient["cmp"])
    add_lipid_panel(story, styles, patient["lipid"])
    add_vitamin_d(story, styles, patient["vitamin_d"])
    add_a1c(story, styles, patient["a1c"])
    add_thyroid(story, styles, patient["thyroid"])
    add_b12(story, styles, patient["b12"])
    add_iron(story, styles, patient["iron"])
    story.append(PageBreak())
    story.append(Paragraph("Additional information", styles["panel"]))
    story.append(Paragraph("Synthetic sample data for software testing only. Not a real medical record.", styles["small"]))
    doc.build(story)


def patient_for_year(patient: dict, year: int) -> dict:
    if year == 2026:
        return patient

    patient_id = patient["profile"]["Patient ID"]
    overrides = HISTORY_OVERRIDES[patient_id][year]
    yearly = dict(patient)
    yearly.update(overrides)
    return yearly


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for patient in patients:
        folder = OUTPUT_DIR / patient["folder"]
        folder.mkdir(parents=True, exist_ok=True)
        build_patient_info_pdf(folder, patient["profile"])
        for year in HISTORY_YEARS:
            yearly_patient = patient_for_year(patient, year)
            build_lab_results_pdf(folder, yearly_patient, year, f"lab_results_{year}.pdf")


if __name__ == "__main__":
    main()
