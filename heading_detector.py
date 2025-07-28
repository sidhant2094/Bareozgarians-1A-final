import os
import re
import json
from pdf_parser import get_text_blocks

def is_bold(font_name):
    """Checks if a font name suggests it is bold."""
    return any(indicator in font_name.lower() for indicator in ['bold', 'black', 'heavy', 'oblique'])

def detect_headings(text_blocks, body_style, min_font_size):
    """
    Detects headings using the original logic, ignoring text in columns or boxes, 
    and prepares them for hierarchy refinement.
    """
    MIN_HEADER_LEN = 7
    MAX_HEADER_LEN = 87

    candidates = []
    for i, block in enumerate(text_blocks):
        # Reverted to original flags: 'is_column_like' and 'is_in_box'
        if (block['is_column_like'] or
            block['is_in_box'] or
            block['font_size'] <= min_font_size or
            len(block['text'].split()) > 25):
            continue

        is_larger = block['font_size'] > body_style.get('size', 12)
        is_bolder = is_bold(block['font_name']) and not is_bold(body_style.get('font', ''))
        is_above_column = (i + 1 < len(text_blocks) and 
                           (text_blocks[i+1]['is_column_like'] or text_blocks[i+1]['is_in_box']) and 
                           not (block['is_column_like'] or block['is_in_box']))

        if is_larger or is_bolder or is_above_column:
            candidates.append(block)

    if not candidates:
        return []

    heading_styles = sorted(list(set((h['font_size'], h['font_name']) for h in candidates)), key=lambda x: x[0], reverse=True)
    style_rank = {style: i for i, style in enumerate(heading_styles)}

    classified_headings = []
    last_level = 0
    
    i = 0
    while i < len(candidates):
        block = candidates[i]
        style = (block['font_size'], block['font_name'])
        
        if style not in style_rank:
            i += 1
            continue

        current_rank = style_rank[style]
        
        if not classified_headings:
            level = 1
        else:
            last_heading_style = classified_headings[-1]['_style']
            last_rank = style_rank[last_heading_style]
            if current_rank < last_rank: level = current_rank + 1
            elif current_rank > last_rank: level = last_level + 1
            else: level = last_level
        
        level = min(level, 3)
        last_level = level

        text = block['text']
        if i + 1 < len(candidates):
            next_block = candidates[i+1]
            if (next_block['font_size'], next_block['font_name']) == style:
                vertical_gap = next_block['bbox'][1] - block['bbox'][3]
                if vertical_gap < (block['font_size'] * 1.5):
                    text += " " + next_block['text']
                    i += 1
        
        cleaned_text = text.strip()
        if (cleaned_text and 
            cleaned_text[0].isalnum() and 
            MIN_HEADER_LEN <= len(cleaned_text) <= MAX_HEADER_LEN):
            # Keep the _style key for the hierarchy fixer
            classified_headings.append({"level": f"H{level}", "text": cleaned_text, "page": block['page'], "_style": style})
        elif classified_headings:
            last_level = int(classified_headings[-1]['level'].replace('H',''))

        i += 1
            
    return classified_headings
