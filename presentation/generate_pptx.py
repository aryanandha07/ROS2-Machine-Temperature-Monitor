#!/usr/bin/env python3
"""
Automated PowerPoint (.pptx) Generator for Prof. Sunil Aggarwal's Evaluation.

Institution: IIITDM Jabalpur
Department: B.Tech Smart Manufacturing
Team:
  - Aryanandha (24BSM013)
  - Spoorthy (24BSM002)
  - Devanshu Verma (24BSM019)

Requirements:
    pip install python-pptx

Usage:
    python3 generate_pptx.py
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    DARK_BLUE = RGBColor(15, 23, 42)
    SLATE = RGBColor(30, 41, 59)
    PRIMARY_BLUE = RGBColor(30, 58, 138)
    ACCENT_ORANGE = RGBColor(249, 115, 22)
    WHITE = RGBColor(255, 255, 255)
    TEXT_MUTED = RGBColor(148, 163, 184)

    blank_layout = prs.slide_layouts[6]

    # ---------------- SLIDE 1: TITLE SLIDE ----------------
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = DARK_BLUE
    bg1.line.color.rgb = DARK_BLUE

    # Title box
    tb1 = slide1.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(2.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "ROS 2 HUMBLE • SMART MANUFACTURING CYBER-PHYSICAL SYSTEM"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_ORANGE

    p1 = tf1.add_paragraph()
    p1.text = "ROS 2 BASED MACHINE TEMPERATURE MONITORING AND ALARM SYSTEM"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    p2 = tf1.add_paragraph()
    p2.text = "A Python-Based Industrial Temperature Monitoring & Autonomous Fault Detection Prototype"
    p2.font.size = Pt(15)
    p2.font.color.rgb = TEXT_MUTED

    # Team Members Box
    tb_team = slide1.shapes.add_textbox(Inches(0.8), Inches(3.3), Inches(6.8), Inches(3.5))
    tf_team = tb_team.text_frame
    tf_team.word_wrap = True

    p_th = tf_team.paragraphs[0]
    p_th.text = "PRESENTED BY:"
    p_th.font.size = Pt(13)
    p_th.font.bold = True
    p_th.font.color.rgb = ACCENT_ORANGE

    members = [
        ("Aryanandha", "24BSM013", "Role A: Sensor Simulation, Physics & Fault Injection"),
        ("Spoorthy", "24BSM002", "Role B: EMA Filtering, Hysteresis Logic & Safe Reset"),
        ("Devanshu Verma", "24BSM019", "Role C: Launch Orchestration, Evidence Logger & Dashboard")
    ]

    for name, roll, role in members:
        p = tf_team.add_paragraph()
        p.text = f"• {name} ({roll})"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = WHITE

        p_sub = tf_team.add_paragraph()
        p_sub.text = f"   {role}"
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_MUTED

    # Supervisor Box
    sup_shape = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(3.4), Inches(4.5), Inches(2.4))
    sup_shape.fill.solid()
    sup_shape.fill.fore_color.rgb = SLATE
    sup_shape.line.color.rgb = PRIMARY_BLUE

    tf_sup = sup_shape.text_frame
    tf_sup.word_wrap = True
    p_sl = tf_sup.paragraphs[0]
    p_sl.text = "PRESENTED TO:"
    p_sl.font.size = Pt(11)
    p_sl.font.bold = True
    p_sl.font.color.rgb = ACCENT_ORANGE

    p_sn = tf_sup.add_paragraph()
    p_sn.text = "Prof. Sunil Aggarwal"
    p_sn.font.size = Pt(22)
    p_sn.font.bold = True
    p_sn.font.color.rgb = WHITE

    p_sd = tf_sup.add_paragraph()
    p_sd.text = "· B.Tech Smart Manufacturing ·\nIIITDM Jabalpur"
    p_sd.font.size = Pt(13)
    p_sd.font.color.rgb = RGBColor(147, 197, 253)

    output_path = os.path.join(os.path.dirname(__file__), "ROS2_Machine_Temperature_Monitor_IIITDM.pptx")
    prs.save(output_path)
    print(f"PowerPoint Presentation generated at: {output_path}")

if __name__ == '__main__':
    create_presentation()
