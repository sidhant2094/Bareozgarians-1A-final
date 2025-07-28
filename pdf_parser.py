import fitz  # PyMuPDF
import os
from collections import defaultdict
import json

def get_text_blocks(pdf_path):
    """
    Extracts text blocks and intelligently flags blocks that are part of column/table layouts or inside drawn boxes.

    Args:
        pdf_path (str): The file path to the PDF.

    Returns:
        tuple: A tuple containing:
            - list: A list of all text blocks, with each block being a dictionary.
            - dict: A dictionary with the most common 'size' and 'font' name (body style).
            - float: The minimum font size found in the document.
    """
    doc = fitz.open(pdf_path)
    all_blocks = []
    font_styles = defaultdict(int)
    min_font_size = float('inf')

    for page_num, page in enumerate(doc):
        # --- Detect drawn rectangles on the page ---
        drawing_rects = []
        for path in page.get_drawings():
            # We are interested in closed, rectangular paths
            if path['rect'] and not path['fill']: # Non-filled rectangles are likely borders
                 drawing_rects.append(path['rect'])
        # --- End Box Detection ---

        page_blocks = []
        raw_blocks = page.get_text("dict")["blocks"]

        x_positions = defaultdict(list)
        for i, block in enumerate(raw_blocks):
            if block['type'] == 0:
                x0 = round(block['bbox'][0] / 10) * 10
                x_positions[x0].append(i)

        column_block_indices = set()
        for x0 in x_positions:
            if len(x_positions[x0]) > 2:
                for block_index in x_positions[x0]:
                    column_block_indices.add(block_index)

        for i, block in enumerate(raw_blocks):
            if block['type'] == 0:
                is_in_column = i in column_block_indices
                for line in block['lines']:
                    for span in line['spans']:
                        text = span['text'].strip()
                        if not text:
                            continue
                        
                        # --- Check if span is inside a detected box ---
                        span_rect = fitz.Rect(span['bbox'])
                        is_in_box = False
                        for rect in drawing_rects:
                            if rect.contains(span_rect):
                                is_in_box = True
                                break
                        # --- End Check ---

                        size = round(span['size'])
                        font_styles[(size, span['font'])] += len(text)
                        if size < min_font_size:
                            min_font_size = size

                        page_blocks.append({
                            'bbox': span['bbox'],
                            'text': text,
                            'font_size': size,
                            'font_name': span['font'],
                            'page': page_num,
                            'is_column_like': is_in_column,
                            'is_in_box': is_in_box # Add the new flag
                        })
        all_blocks.extend(page_blocks)
    doc.close()

    most_common_style = {'size': 0, 'font': ''}
    if font_styles:
        non_min_styles = {s: c for s, c in font_styles.items() if s[0] > min_font_size}
        if non_min_styles:
            top_style = max(non_min_styles, key=non_min_styles.get)
            most_common_style['size'] = top_style[0]
            most_common_style['font'] = top_style[1]

    return all_blocks, most_common_style, min_font_size
