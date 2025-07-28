# Adobe Hackathon 2025 - PDF Outlining Solution

This project is a solution for Challenge 1a, designed to extract a structured title and outline from PDF documents and output them as JSON files. <br>
**This solution is fully heuristics based, lightweight, and deterministic. Built entirely on good logic and clean design** 

## Approach

The solution follows a clean, modular, and multi-stage pipeline:

<pre>

pdf_parser.py     title_detector.py      heading_detector.py       hierarchy_fixer.py
              →                      →                         →
[Parse text       [Detect centered       [Identify heading           [Fix levels,
 & font info]     title on page 1]      styles & assign H1–H3]       enforce order]

</pre>
Each module is laser-focused on a specific task:

-  **pdf_parser.py**  
  Extracts all text blocks using `PyMuPDF`. Adds metadata: font size, name, position, column/box flags. Also determines the dominant body font style.

-  **title_detector.py**  
  Identifies the document title by selecting large, centered, uncommon text on the first page. Handles multiline titles gracefully.

-  **heading_detector.py**  
  Detects headings by checking for stylistic differences (e.g. bold, larger fonts). Assigns hierarchy levels H1, H2, H3 based on font ranks.

- **hierarchy_fixer.py** – Refines heading tree by enforcing order (e.g., H3 can't follow H1), fixing font-size inconsistencies, and ensuring a valid starting H1.

=> This step-by-step architecture ensures robust handling of even messy or unstructured PDFs.



## Models and Libraries Used

* **Language:** Python 3.9  
* **Core Library:** **PyMuPDF (`fitz`)** – high-performance PDF parser  

* **No models**, no external dependencies, no cloud APIs and no external libararies used.

## How to Build and Run

The solution is containerized with Docker and has no external network dependencies at runtime.

### **->Build the Docker Image**

Use the following command from the root of the project directory:

```bash
docker build --platform linux/amd64 -t mysolution:latest .
```

### **->Run the Container**

**To process PDFs, place them in the `input` directory. The container will automatically process all PDFs and place the corresponding JSON files in the `output` directory.**

Use the following command to run the container, replacing `$(pwd)` with the absolute path to your project directory if you are not using a Unix-like shell.

```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolution:latest
```
