import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO
import re

# Helper function to convert integer to Roman numerals
def to_roman(num):
    roman_numerals = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]
    result = ""
    for value, numeral in roman_numerals:
        while num >= value:
            result += numeral
            num -= value
    return result

# Parse the page range input and return a list of page numbers
def parse_intervals(interval_str, total_pages):
    intervals = []
    for part in interval_str.split(','):
        match = re.match(r'(\d+)-(\d+)', part.strip())
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            if 1 <= start <= total_pages and 1 <= end <= total_pages and start <= end:
                intervals.append(list(range(start, end + 1)))
    return intervals

# Function to add page numbers to a PDF using ReportLab
def add_page_numbers(input_pdf, roman_intervals, arabic_intervals):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    # Maintain the numbering for each interval
    for page_num in range(1, total_pages + 1):
        # Check if the current page is in one of the intervals
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(595.27, 841.89))  # A4 size

        # Determine if this page needs a Roman or Arabic page number
        numbering_text = ""
        if any(page_num in interval for interval in roman_intervals):
            interval_start = min(p[0] for p in roman_intervals if page_num in p)
            numbering_text = to_roman(page_num - interval_start + 1)
        elif any(page_num in interval for interval in arabic_intervals):
            interval_start = min(p[0] for p in arabic_intervals if page_num in p)
            numbering_text = str(page_num - interval_start + 1)

        # If there's a page number, draw it at the bottom center of the page
        if numbering_text:
            can.drawString(297.63, 50, numbering_text)  # Bottom-center position
        can.save()
        packet.seek(0)

        # Check if the overlay PDF contains any pages
        overlay_pdf = PdfReader(packet)
        if overlay_pdf.pages:
            original_page = reader.pages[page_num - 1]
            original_page.merge_page(overlay_pdf.pages[0])
            writer.add_page(original_page)
        else:
            # Just add the original page without overlay if no numbering
            writer.add_page(reader.pages[page_num - 1])

    # Save modified PDF to a buffer
    output_pdf = BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf

# Streamlit app layout
st.title("PDF Page Numbering App with Multiple Intervals")
st.write("Upload a PDF file, then enter intervals for Roman and Arabic numbering.")

# PDF file uploader
pdf_file = st.file_uploader("Choose a PDF file", type="pdf")

if pdf_file is not None:
    # Read the uploaded PDF to determine the number of pages
    reader = PdfReader(pdf_file)
    total_pages = len(reader.pages)

    # Single input for Roman and Arabic intervals
    roman_range_input = st.text_input("Enter pages for Roman numbering (e.g., 1-5,11-15):")
    arabic_range_input = st.text_input("Enter pages for Arabic numbering (e.g., 6-10):")

    # Parse intervals based on inputs
    roman_intervals = parse_intervals(roman_range_input, total_pages)
    arabic_intervals = parse_intervals(arabic_range_input, total_pages)

    # Process the PDF and add page numbers if the button is clicked
    if st.button("Add Page Numbers"):
        # Ensure no overlapping intervals
        all_pages = [page for interval in (roman_intervals + arabic_intervals) for page in interval]
        if len(all_pages) != len(set(all_pages)):
            st.error("Please ensure no overlapping pages between intervals.")
        else:
            output_pdf = add_page_numbers(pdf_file, roman_intervals, arabic_intervals)
            st.download_button("Download PDF with Page Numbers", output_pdf, "numbered_output.pdf", "application/pdf")
