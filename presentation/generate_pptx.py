#!/usr/bin/env python3
"""
Automated PowerPoint (.pptx) Generator for Dr. K Ponnappa's Evaluation Presentation.

Requirements:
    pip install python-pptx

Usage:
    python3 generate_pptx.py
Generates:
    presentation/ROS2_Machine_Temperature_Monitor_Presentation.pptx
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

    # Color Palette
    DARK_BLUE = RGBColor(15, 23, 42)
    SLATE = RGBColor(30, 41, 59)
    PRIMARY_BLUE = RGBColor(30, 58, 138)
    ACCENT_ORANGE = RGBColor(249, 115, 22)
    WHITE = RGBColor(255, 255, 255)
    LIGHT_GRAY = RGBColor(241, 245, 249)
    TEXT_MUTED = RGBColor(148, 163, 184)
    TEXT_DARK = RGBColor(15, 23, 42)

    blank_layout = prs.slide_layouts[6]

    # ---------------- SLIDE 1: TITLE SLIDE ----------------
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = DARK_BLUE
    bg1.line.color.rgb = DARK_BLUE

    # Title box
    tb1 = slide1.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(2.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "ROS 2 HUMBLE • INDUSTRIAL CYBER-PHYSICAL DIGITAL TWIN"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_ORANGE

    p1 = tf1.add_paragraph()
    p1.text = "MACHINE TEMPERATURE MONITORING & ALARM SYSTEM"
    p1.font.size = Pt(32)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    p2 = tf1.add_paragraph()
    p2.text = "Precision CNC Spindle Thermal Runaway Protection • 4-Cylinder Engine Assembly Operations"
    p2.font.size = Pt(16)
    p2.font.color.rgb = TEXT_MUTED

    # Team members list
    tb_team = slide1.shapes.add_textbox(Inches(0.8), Inches(3.4), Inches(7.5), Inches(3.5))
    tf_team = tb_team.text_frame
    tf_team.word_wrap = True

    p_th = tf_team.paragraphs[0]
    p_th.text = "TEAM MEMBERS (Engine Assembly & Robotics Team):"
    p_th.font.size = Pt(13)
    p_th.font.bold = True
    p_th.font.color.rgb = ACCENT_ORANGE

    members = [
        ("Abhinav Giri", "Roll No: 01"),
        ("Akash Deep", "Roll No: 02"),
        ("Aryanandha", "Roll No: 03"),
        ("Dhanjeet Mishra", "Roll No: 04"),
        ("Harshit Singh", "Roll No: 05"),
        ("Lokendra", "Roll No: 06"),
        ("Paramjeet Kumawat", "Roll No: 07"),
        ("Ritesh Vivek Kumar", "Roll No: 08"),
        ("Sunny", "Roll No: 09")
    ]

    for name, roll in members:
        p = tf_team.add_paragraph()
        p.text = f"• {name.ljust(22)} {roll}"
        p.font.size = Pt(12)
        p.font.color.rgb = WHITE

    # Supervisor Box
    sup_shape = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.8), Inches(3.5), Inches(3.8), Inches(2.2))
    sup_shape.fill.solid()
    sup_shape.fill.fore_color.rgb = SLATE
    sup_shape.line.color.rgb = PRIMARY_BLUE

    tf_sup = sup_shape.text_frame
    tf_sup.word_wrap = True
    p_sl = tf_sup.paragraphs[0]
    p_sl.text = "PRESENTED TO FACULTY SUPERVISOR:"
    p_sl.font.size = Pt(11)
    p_sl.font.bold = True
    p_sl.font.color.rgb = ACCENT_ORANGE

    p_sn = tf_sup.add_paragraph()
    p_sn.text = "Dr. K Ponnappa"
    p_sn.font.size = Pt(22)
    p_sn.font.bold = True
    p_sn.font.color.rgb = WHITE

    p_sd = tf_sup.add_paragraph()
    p_sd.text = "Department of Mechanical / Robotics Engineering"
    p_sd.font.size = Pt(11)
    p_sd.font.color.rgb = TEXT_MUTED

    # Save presentation
    output_path = os.path.join(os.path.dirname(__file__), "ROS2_Machine_Temperature_Monitor_Presentation.pptx")
    prs.save(output_path)
    print(f"PowerPoint Presentation generated successfully at: {output_path}")

if __name__ == '__main__':
    create_presentation()
