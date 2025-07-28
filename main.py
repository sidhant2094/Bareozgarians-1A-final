import os
import json
import time

# Import the updated functions from our other Python files
from pdf_parser import get_text_blocks
from title_detector import find_title_blocks
from heading_detector import detect_headings
from hierarchy_fixer import refine_heading_hierarchy # NEW IMPORT

def process_pdf(pdf_path):
    """
    Processes a single PDF file to extract its title and outline using refined logic.

    Args:
        pdf_path (str): The full path to the PDF file.

    Returns:
        dict: A dictionary containing the title and a list of headings (the outline).
              Returns None if the PDF cannot be processed.
    """
    try:
        print(f"Processing: {os.path.basename(pdf_path)}")
        
        # Step 1: Parse the PDF to get all blocks, body style, and minimum font size.
        all_blocks, body_style, min_font_size = get_text_blocks(pdf_path)

        # Step 2: Detect the blocks that constitute the title.
        title_blocks = find_title_blocks(all_blocks, min_font_size)

        title_text = ""
        blocks_for_headings = all_blocks

        if title_blocks:
            title_text = " ".join(b['text'] for b in title_blocks)
            title_block_ids = set(id(b) for b in title_blocks)
            blocks_for_headings = [b for b in all_blocks if id(b) not in title_block_ids]

        # Step 3: Detect headings. Note: these will include a temporary '_style' key.
        headings = detect_headings(blocks_for_headings, body_style, min_font_size)

        # NEW Step 4: Refine the heading hierarchy using the new fixer logic.
        refined_headings = refine_heading_hierarchy(headings)

        # NEW Step 5: Clean up the temporary '_style' key before final output.
        for heading in refined_headings:
            if '_style' in heading:
                del heading['_style']

        # Step 6: Assemble the final JSON structure.
        output_data = {
            "title": title_text,
            "outline": refined_headings # Use the refined list
        }
        
        return output_data

    except Exception as e:
        print(f"Error processing {os.path.basename(pdf_path)}: {e}")
        return None

def main():
    """
    Main function to run the document outlining process.
    It looks for PDFs in the 'input' directory and saves the
    JSON results in the 'output' directory.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, 'input')
    output_dir = os.path.join(script_dir, 'output')

    # Create directories if they don't exist
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    try:
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    except FileNotFoundError:
        print(f"Error: The input directory was not found at '{input_dir}'")
        return

    if not pdf_files:
        print(f"No PDF files found in '{input_dir}' directory.")
        print("Please add some PDF files to the 'input' folder to run the script.")
        return

    print(f"Found {len(pdf_files)} PDF(s) to process.")
    start_time = time.time()

    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        result = process_pdf(pdf_path)

        if result:
            base_name = os.path.splitext(pdf_file)[0]
            output_filename = f"{base_name}.json"
            output_path = os.path.join(output_dir, output_filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            print(f"Successfully created output: {output_path}")

    end_time = time.time()
    print(f"\nProcessing complete. Total time: {end_time - start_time:.2f} seconds.")


if __name__ == '__main__':
    main()
