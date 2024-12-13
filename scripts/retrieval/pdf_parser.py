from docling.document_converter import DocumentConverter
import PyPDF2
import json

class PDFParser:
  def parse(self, input_pdf="data/asii_2023_sustainability_report.pdf", output_json="data/parsed_pdf.json"):
    pdf_data = {}

    for i in range(1, 211):
      # Split PDF untuk setiap halaman
      target_pdf = 'data/split.pdf'
      self._split_pdf(input_pdf, target_pdf, i)

      # Konversi PDF yang sudah dibagi ke format markdown
      markdown = self._convert_pdf_to_markdown(target_pdf)

      # Simpan markdown ke dalam dictionary dengan key nomor halaman
      pdf_data[i] = markdown

    # Simpan hasil konversi ke file JSON
    try:
      with open(output_json, 'w') as json_file:
        json.dump(pdf_data, json_file, indent=4)

      print(f"Hasil konversi PDF disimpan dalam '{output_json}'.")

    except Exception as e:
      print(f"Terjadi kesalahan saat menyimpan file JSON: {e}")

  def _convert_pdf_to_markdown(self, pdf_path):
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown()

  def _split_pdf(self, input_pdf, output_pdf, page_num):
    try:
      # Buka file PDF input
      with open(input_pdf, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()

        total_pages = len(reader.pages)

        # Validasi halaman yang diminta
        if page_num < 1 or page_num > total_pages:
          print(f"Halaman {page_num} tidak valid.")
          return None

        # Ambil halaman yang diminta
        writer.add_page(reader.pages[page_num - 1])

        # Simpan file PDF yang terpisah
        with open(output_pdf, 'wb') as output_file:
          writer.write(output_file)

        return output_pdf

    except FileNotFoundError:
      print(f"File '{input_pdf}' tidak ditemukan.")
    except Exception as e:
      print(f"Terjadi kesalahan: {e}")

