"""
Analyze the Comparative Income Statement PDF using PyPDF2
"""
import PyPDF2
import os

pdf_path = r'sample_files\04_Rittenhouse Station_Comparative Income Statement_September 2025.pdf'

print("=" * 100)
print("COMPARATIVE INCOME STATEMENT ANALYSIS")
print("=" * 100)
print()

if not os.path.exists(pdf_path):
    print(f"ERROR: File not found: {pdf_path}")
    exit(1)

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    
    print(f"Total pages: {len(pdf_reader.pages)}")
    print()
    
    for page_num in range(len(pdf_reader.pages)):
        print(f"\n{'='*100}")
        print(f"PAGE {page_num + 1}")
        print(f"{'='*100}\n")
        
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        
        if text:
            print(text)
        else:
            print("(No text extracted)")

print("\n" + "="*100)
print("END OF DOCUMENT")
print("="*100)
