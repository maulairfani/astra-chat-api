from docling.document_converter import DocumentConverter
import PyPDF2
import json

class PDFParser:
  """Class for parsing and converting PDF to JSON with markdown content."""

  def parse(self, input_pdf="data/asii_2023_sustainability_report.pdf", output_json="data/parsed_pdf.json"):
    parsed_data = {}

    for page_number in range(1, 211):
      split_pdf_path = 'data/split_page.pdf'
      self._extract_single_page(input_pdf, split_pdf_path, page_number)

      markdown_content = self._convert_to_markdown(split_pdf_path)
      parsed_data[page_number] = markdown_content

    self._save_to_json(parsed_data, output_json)

  def _convert_to_markdown(self, pdf_path):
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown()

  def _extract_single_page(self, input_pdf, output_pdf, page_number):
    try:
      with open(input_pdf, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        writer = PyPDF2.PdfWriter()

        if 1 <= page_number <= len(reader.pages):
          writer.add_page(reader.pages[page_number - 1])

          with open(output_pdf, 'wb') as output_file:
            writer.write(output_file)
        else:
          print(f"Invalid page number: {page_number}.")
    except FileNotFoundError:
      print(f"File not found: {input_pdf}.")
    except Exception as error:
      print(f"Error extracting page {page_number}: {error}")

  def _save_to_json(self, data, output_json):
    try:
      with open(output_json, 'w') as json_file:
        json.dump(data, json_file, indent=2)
      print(f"JSON saved to: {output_json}")
    except Exception as error:
      print(f"Error saving JSON: {error}")
