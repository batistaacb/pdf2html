from codes_we_need import convert_pdf_to_html
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <Document.pdf> [Document.html]")
        sys.exit(1)

    try:
        result = convert_pdf_to_html(
            sys.argv[1],
            sys.argv[2] if len(sys.argv) > 2 else None,
        )
        print(f"HTML created successfully: {result}")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
