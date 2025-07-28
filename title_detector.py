import os
import json
from pdf_parser import get_text_blocks

def find_title_blocks(text_blocks, min_font_size):
    """
    Identifies title blocks with refined rules:
    - Must be on the first page and in the top 60% of the page.
    - The entire title block (including multiple lines) must be centered.
    - Cannot be the last text block on the page.
    - Its font style must not be repeated more than twice on the page.
    - Must contain more than one word.
    """
    MAX_TITLE_LEN = 200
    PAGE_ZERO = 0

    # Step 1: Get all text blocks on the first page, sorted top-to-bottom.
    page_zero_blocks = sorted(
        [b for b in text_blocks if b['page'] == PAGE_ZERO and b.get('text', '').strip()],
        key=lambda b: b['bbox'][1]
    )
    if not page_zero_blocks:
        return []

    # --- Define page boundaries for position checks ---
    page_height = max(b['bbox'][3] for b in page_zero_blocks) if page_zero_blocks else 800
    page_width = max(b['bbox'][2] for b in page_zero_blocks) if page_zero_blocks else 600
    page_center_x = page_width / 2.0
    
    # Rule: A title cannot start in the bottom 40% of the page.
    vertical_position_limit = page_height * 0.60
    
    last_block_on_page = page_zero_blocks[-1]

    # Step 2: Filter for potential title candidates based on position and basic properties.
    candidates = [
        b for b in page_zero_blocks
        if b['bbox'][1] < vertical_position_limit and
           b.get('font_size', 0) > min_font_size and
           not b.get('is_column_like') and
           not b.get('is_in_box')
    ]
    if not candidates:
        return []

    # Step 3: Iterate through candidates to find and validate title groups.
    for i, start_block in enumerate(candidates):
        title_style = (start_block['font_size'], start_block['font_name'])
        
        # Rule: If the style is too common, it's likely a heading, not a title.
        style_count = sum(1 for b in candidates if (b['font_size'], b['font_name']) == title_style)
        if style_count > 3: # Allow for slightly more repetition for complex titles
            continue

        # Step 4: Merge subsequent blocks that are part of the same title.
        merged_blocks = [start_block]
        last_merged_block = start_block
        
        for j in range(i + 1, len(candidates)):
            current_block = candidates[j]
            
            is_style_match = (current_block['font_size'], current_block['font_name']) == title_style
            vertical_gap = current_block['bbox'][1] - last_merged_block['bbox'][3]
            is_vertically_close = 0 <= vertical_gap < (last_merged_block['font_size'] * 1.8)

            if is_style_match and is_vertically_close:
                merged_blocks.append(current_block)
                last_merged_block = current_block
            # Break if a non-matching block is found, as the title has ended.
            elif vertical_gap > 0 and not is_vertically_close:
                break
        
        # --- Final Validation on the MERGED block ---
        
        # Rule: The title cannot end with the last block on the page.
        if merged_blocks[-1] == last_block_on_page:
            continue

        # --- New: Check if the entire merged block is centered ---
        merged_bbox_x0 = min(b['bbox'][0] for b in merged_blocks)
        merged_bbox_x1 = max(b['bbox'][2] for b in merged_blocks)
        merged_block_center_x = merged_bbox_x0 + ((merged_bbox_x1 - merged_bbox_x0) / 2.0)
        
        # A merged block is centered if its center is within 15% of the page's center.
        if abs(merged_block_center_x - page_center_x) > (page_width * 0.15):
            continue

        full_title_text = " ".join(b['text'].strip() for b in merged_blocks).strip()

        # Rule: Title must be multi-word and meet other criteria.
        if (full_title_text and 
            full_title_text[0].isalnum() and 
            len(full_title_text.split()) > 1 and
            len(full_title_text) <= MAX_TITLE_LEN):
            return merged_blocks  # A valid title has been found.

    # If no candidates passed all rules, return empty.
    return []
