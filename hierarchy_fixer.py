import os
import json

def get_level(heading):
    """Safely gets the integer level from a heading dictionary."""
    try:
        return int(heading.get('level', 'H0').replace('H', ''))
    except (ValueError, AttributeError):
        return 0

def get_font_size(heading):
    """Safely gets the font size from a heading's style tuple."""
    try:
        # _style is expected to be a tuple: (font_size, font_name)
        return heading.get('_style', (0, ''))[0]
    except (IndexError, TypeError):
        return 0

def refine_heading_hierarchy(headings):
    """
    Refines heading levels to enforce a logical hierarchy based on document
    order and font sizes. This acts as a post-processing step to correct
    potential errors from the initial detection.

    Args:
        headings (list): A list of heading dictionaries. Each dictionary must
                         contain 'level' and a temporary '_style' key.

    Returns:
        list: The list of headings with corrected levels.
    """
    if not headings:
        return []

    # Pass 1: Enforce sequential hierarchy.
    # A heading level cannot jump more than one level down (e.g., H1 to H3).
    # Also, a document shouldn't start with an H2 or H3.
    max_level_seen = 0
    for i, heading in enumerate(headings):
        current_level = get_level(heading)
        
        if i == 0 and current_level > 1:
            current_level = 1 # The first heading must be H1

        if current_level > max_level_seen + 1:
            current_level = max_level_seen + 1
        
        heading['level'] = f"H{current_level}"
        max_level_seen = current_level

    # Pass 2: Correct levels based on font size hierarchy.
    # An H2 should not have a larger font than the preceding H1, etc.
    # This pass corrects such logical inconsistencies.
    last_h1_size = -1
    last_h2_size = -1

    for heading in headings:
        current_level = get_level(heading)
        current_size = get_font_size(heading)

        if current_level == 1:
            last_h1_size = current_size
            last_h2_size = -1  # Reset H2 context after an H1
        
        elif current_level == 2:
            # If this H2 is larger than the last H1, it's likely an H1.
            if last_h1_size != -1 and current_size > last_h1_size:
                heading['level'] = 'H1'
                last_h1_size = current_size
                last_h2_size = -1
            else:
                last_h2_size = current_size

        elif current_level == 3:
            # If this H3 is larger than the last H2, promote it to H2.
            if last_h2_size != -1 and current_size > last_h2_size:
                heading['level'] = 'H2'
                last_h2_size = current_size
            # If it's also larger than the last H1 (and no H2 seen), promote to H1.
            elif last_h1_size != -1 and current_size > last_h1_size:
                heading['level'] = 'H1'
                last_h1_size = current_size
                last_h2_size = -1
    
    # Pass 3: Run the sequential check again, as the font size corrections
    # might have created new jumps (e.g., promoting a heading).
    max_level_seen = 0
    for i, heading in enumerate(headings):
        current_level = get_level(heading)
        
        if i == 0 and current_level > 1:
            current_level = 1

        if current_level > max_level_seen + 1:
            current_level = max_level_seen + 1
        
        heading['level'] = f"H{current_level}"
        max_level_seen = max(max_level_seen, current_level)

    return headings

if __name__ == '__main__':
    # Example usage for testing the fixer logic
    print("Testing hierarchy_fixer...")
    
    # Scenario 1: H2 is larger than H1
    test_headings_1 = [
        {'level': 'H1', 'text': 'Main Section', 'page': 1, '_style': (16, 'Bold')},
        {'level': 'H2', 'text': 'This should be H1', 'page': 1, '_style': (18, 'Bold')}
    ]
    fixed_1 = refine_heading_hierarchy(list(test_headings_1))
    print("\nScenario 1: H2 larger than H1")
    print("Original:", json.dumps(test_headings_1, indent=2))
    print("Fixed:", json.dumps(fixed_1, indent=2))
    assert fixed_1[1]['level'] == 'H1'

    # Scenario 2: Jumps from H1 to H3
    test_headings_2 = [
        {'level': 'H1', 'text': 'Chapter 1', 'page': 2, '_style': (20, 'Bold')},
        {'level': 'H3', 'text': 'This should be H2', 'page': 3, '_style': (14, 'Bold')}
    ]
    fixed_2 = refine_heading_hierarchy(list(test_headings_2))
    print("\nScenario 2: H1 to H3 jump")
    print("Original:", json.dumps(test_headings_2, indent=2))
    print("Fixed:", json.dumps(fixed_2, indent=2))
    assert fixed_2[1]['level'] == 'H2'

    # Scenario 3: Document starts with H2
    test_headings_3 = [
        {'level': 'H2', 'text': 'Abstract', 'page': 1, '_style': (16, 'Bold')},
        {'level': 'H2', 'text': 'Introduction', 'page': 1, '_style': (16, 'Bold')}
    ]
    fixed_3 = refine_heading_hierarchy(list(test_headings_3))
    print("\nScenario 3: Starts with H2")
    print("Original:", json.dumps(test_headings_3, indent=2))
    print("Fixed:", json.dumps(fixed_3, indent=2))
    assert fixed_3[0]['level'] == 'H1'
    
    print("\nAll tests passed.")
