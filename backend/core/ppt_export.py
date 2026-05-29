"""PPTX 导出 — 将幻灯片JSON转为真正的PowerPoint文件"""
import json
import io
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# 配色主题
PRIMARY_COLOR = RGBColor(0x5B, 0x7F, 0xFF)
DARK_COLOR = RGBColor(0x33, 0x33, 0x33)
LIGHT_COLOR = RGBColor(0xF5, 0xF5, 0xF5)
WHITE_COLOR = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT_COLOR = RGBColor(0xFF, 0x6B, 0x6B)


def _add_slide_with_title(prs, title_text, layout_index=1):
    """添加带标题的空白幻灯片"""
    slide_layout = prs.slide_layouts[layout_index]  # Title and Content
    slide = prs.slides.add_slide(slide_layout)
    if slide.shapes.title:
        slide.shapes.title.text = title_text
        for paragraph in slide.shapes.title.text_frame.paragraphs:
            paragraph.font.size = Pt(28)
            paragraph.font.color.rgb = DARK_COLOR
    return slide


def _add_bullets(text_frame, bullets, font_size=16):
    """添加要点列表"""
    for i, bullet in enumerate(bullets):
        if i == 0 and text_frame.paragraphs[0].text:
            p = text_frame.paragraphs[0]
            # Clear placeholder text
            p.clear()
        else:
            p = text_frame.add_paragraph()
        p.text = bullet
        p.font.size = Pt(font_size)
        p.font.color.rgb = DARK_COLOR
        p.space_after = Pt(8)
        p.level = 0


def _add_notes(slide, notes_text):
    """添加演讲者备注"""
    if notes_text:
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = notes_text


def export_pptx(slides_data) -> bytes:
    """将幻灯片JSON数据转为PPTX文件字节流"""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    if isinstance(slides_data, str):
        slides_data = json.loads(slides_data)

    title = slides_data.get("title", "PPT课件")
    slides = slides_data.get("slides", [])

    for slide_data in slides:
        layout = slide_data.get("layout", "title_content")
        page_title = slide_data.get("title", "")
        bullets = slide_data.get("bullets", [])
        table_data = slide_data.get("table")
        diagram_text = slide_data.get("diagram", "")
        key_point = slide_data.get("key_point", "")
        notes = slide_data.get("speaker_notes", "")

        if layout == "title_slide":
            # 封面页 — 使用空白布局
            blank_layout = prs.slide_layouts[6]  # Blank
            slide = prs.slides.add_slide(blank_layout)

            # 顶部色条
            from pptx.util import Inches as In
            shape = slide.shapes.add_shape(
                1, In(0), In(0), prs.slide_width, In(0.15)  # Rectangle
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = PRIMARY_COLOR
            shape.line.fill.background()

            # 标题
            txBox = slide.shapes.add_textbox(In(1.5), In(2.0), In(10), In(2))
            tf = txBox.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(44)
            p.font.bold = True
            p.font.color.rgb = PRIMARY_COLOR
            p.alignment = PP_ALIGN.CENTER

            # 副标题
            if bullets:
                txBox2 = slide.shapes.add_textbox(In(2), In(4.2), In(9), In(1.5))
                tf2 = txBox2.text_frame
                tf2.word_wrap = True
                p2 = tf2.paragraphs[0]
                p2.text = " | ".join(bullets)
                p2.font.size = Pt(20)
                p2.font.color.rgb = DARK_COLOR
                p2.alignment = PP_ALIGN.CENTER

            _add_notes(slide, notes)
            continue

        # 普通内容页
        slide = _add_slide_with_title(prs, page_title)

        # 获取内容区
        if slide.placeholders:
            body_shape = None
            for shape in slide.placeholders:
                if shape.placeholder_format.idx == 1:  # Content placeholder
                    body_shape = shape
                    break

            if body_shape and body_shape.has_text_frame:
                tf = body_shape.text_frame
                tf.clear()

                if layout == "title_content":
                    _add_bullets(tf, bullets)
                    if key_point:
                        p = tf.add_paragraph()
                        p.text = f"★ {key_point}"
                        p.font.size = Pt(14)
                        p.font.color.rgb = PRIMARY_COLOR
                        p.font.bold = True

                elif layout == "two_column":
                    mid = (len(bullets) + 1) // 2
                    left_bullets = bullets[:mid]
                    right_bullets = bullets[mid:]
                    # Use first paragraph for left column header
                    p = tf.paragraphs[0]
                    p.text = "  ".join(left_bullets)
                    p.font.size = Pt(16)
                    p2 = tf.add_paragraph()
                    p2.text = "  ".join(right_bullets)
                    p2.font.size = Pt(16)

                elif layout == "summary":
                    _add_bullets(tf, bullets, font_size=18)
                    tf.paragraphs[0].font.bold = True

                elif layout == "diagram":
                    if diagram_text:
                        p = tf.paragraphs[0]
                        p.text = diagram_text
                        p.font.size = Pt(14)
                        p.font.color.rgb = DARK_COLOR
                    if bullets:
                        for b in bullets:
                            p = tf.add_paragraph()
                            p.text = f"• {b}"
                            p.font.size = Pt(14)

        # 表格
        if layout == "table" and table_data:
            headers = table_data.get("headers", [])
            rows = table_data.get("rows", [])
            if headers and rows:
                num_rows = len(rows) + 1
                num_cols = len(headers)
                table_left = Inches(1)
                table_top = Inches(2.5)
                table_width = Inches(11)
                table_height = Inches(0.5 * num_rows)

                tbl = slide.shapes.add_table(num_rows, num_cols, table_left, table_top, table_width, table_height).table

                # Header row
                for col_idx, header in enumerate(headers):
                    cell = tbl.cell(0, col_idx)
                    cell.text = header
                    for p in cell.text_frame.paragraphs:
                        p.font.size = Pt(14)
                        p.font.bold = True
                        p.font.color.rgb = WHITE_COLOR
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = PRIMARY_COLOR

                # Data rows
                for row_idx, row in enumerate(rows):
                    for col_idx, val in enumerate(row):
                        cell = tbl.cell(row_idx + 1, col_idx)
                        cell.text = str(val)
                        for p in cell.text_frame.paragraphs:
                            p.font.size = Pt(13)

        _add_notes(slide, notes)

    # 保存到字节流
    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output.getvalue()
