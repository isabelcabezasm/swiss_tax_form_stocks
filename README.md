# Tax Form Processing Application

A Python application for extracting and processing stock transaction data from PDF tax documents.

## Overview

This application processes PDF documents containing stock transaction data for tax reporting purposes. It extracts information from two types of documents:

1. **salary_certificate.pdf** - Contains vested stock awards and ESPP (Employee Stock Purchase Plan) data
2. **Fidelity NetBenefits transaction summary** - Contains sold shares transaction data

## Features

- **Vested Stock Extraction**: Parses vested stock data with vest dates and share quantities
- **ESPP Data Processing**: Extracts Employee Stock Purchase Plan information
- **Sold Shares Analysis**: Processes sold stock transactions with aggregation by date
- **Clean Table Output**: Displays data in formatted tables with consistent date formatting (DD.MM.YYYY)
- **Date Aggregation**: Automatically sums shares by the same vest/sell dates
- **Multiple PDF Support**: Processes multiple PDF documents in a single run

## Sample Output

```
================================================================================
VESTED STOCKS 2024
================================================================================
Vest Date       Quantity       
------------------------------
29.02.2024      12.500         
15.04.2024      24.750         
30.05.2024      3.000          
31.05.2024      8.250          
30.08.2024      3.000          
31.08.2024      10.000         
15.10.2024      25.000         
30.11.2024      10.000         
------------------------------
Total unique dates: 8
Total shares: 96.500

================================================================================
ESPP (Employee Stock Purchase Plan)
================================================================================
Off Period      Purchased Shares    
-----------------------------------
092024          20.0000             
-----------------------------------
Total entries: 1
Total purchased shares: 20.0000
================================================================================

============================================================
AGGREGATED QUANTITIES BY DATE:
============================================================
Sell Date                 Quantity       
------------------------------------------------------------
16.01.2024                5.0000         
02.02.2024                7.5000         
27.02.2024                2.5000         
08.04.2024                25.0000        
12.06.2024                45.0000         
07.10.2024                20.0000        
25.10.2024                15.0000        
28.10.2024                12.0000        
09.12.2024                8.0000         
11.12.2024                18.0000        
============================================================
Total unique dates: 10
Total individual transactions: 45
Grand total quantity: 158.0000
============================================================
```

## Development Setup

This project uses a development container for a consistent development environment.

### Prerequisites

- Docker Desktop or compatible container runtime
- Visual Studio Code with Dev Containers extension

### Getting Started

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tax_form
   ```

2. Open in VS Code and reopen in container when prompted, or:
   ```bash
   code .
   ```
   Then use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"

3. The dev container will automatically:
   - Install Python dependencies with `uv sync`
   - Install development tools including `pdfplumber` for PDF processing
   - Configure the development environment

## Usage

### Running the Application

Place your PDF files in the `data/` directory (or specify custom paths):
- `salary_certificate.pdf` - Stock awards and ESPP document
- `Custom transaction summary - Fidelity NetBenefits_ only sales.pdf` - Sold shares document

#### Basic Usage

```bash
# Run with default PDF paths
python tax_form/main.py

# Show help and available options
python tax_form/main.py --help
```

#### Custom PDF Paths

```bash
# Specify custom paths for both PDFs
python tax_form/main.py --vested-pdf "path/to/salary_certificate.pdf" --sold-pdf path/to/sales.pdf

# Use custom path for vested stocks only
python tax_form/main.py --vested-pdf "custom/path/salary_certificate.pdf"

# Use custom path for sold shares only  
python tax_form/main.py --sold-pdf custom/path/fidelity_sales.pdf
```

#### Selective Processing

```bash
# Process only vested stocks and ESPP data
python tax_form/main.py --no-sold

# Process only sold shares data
python tax_form/main.py --no-vested

# Process only vested stocks from custom file
python tax_form/main.py --vested-pdf "data/my_salary_certificate.pdf" --no-sold
```

#### Command Line Options

- `--vested-pdf FILEPATH`: Path to PDF containing vested stocks and ESPP data (default: `data/salary_certificate.pdf`)
- `--sold-pdf FILEPATH`: Path to PDF containing sold shares data (default: `data/Custom transaction summary - Fidelity NetBenefits_ only sales.pdf`)
- `--no-vested`: Skip processing vested stocks and ESPP data
- `--no-sold`: Skip processing sold shares data
- `-h, --help`: Show help message and exit

### Supported PDF Formats

#### salary_certificate.pdf Structure
The application expects this document to contain:
- **Vested Stocks 2024** section with columns: Award Date, Award ID, Vest Date, Award Price, Market Value, Shares, etc.
- **ESPP (Employee Stock Purchase Plan)** section with columns: Off Period, Purchased Shares, FMV Price, etc.

#### Fidelity Transaction Summary
The application processes transaction data with pattern matching for:
- Date sold or transferred (format: MMM-DD-YYYY)
- Quantity of shares sold

### Project Structure

```
tax_form/
├── .devcontainer/          # Development container configuration
├── data/                   # PDF files to process
│   ├── salary_certificate.pdf
│   └── Custom transaction summary - Fidelity NetBenefits_ only sales.pdf
├── tax_form/              # Main application package
│   ├── __init__.py
│   ├── __main__.py
│   └── main.py           # Main processing logic
├── pyproject.toml         # Python project configuration
├── uv.lock               # Dependency lock file
└── README.md             # This file
```

## Development Commands

```bash
# Install dependencies
uv sync

# Run the application
python tax_form/main.py

# Run tests (if available)
pytest

# Run linting
ruff check

# Run formatting
ruff format

# Run type checking
mypy .
```

## Dependencies

Key dependencies used in this project:
- **pdfplumber**: PDF text extraction and table parsing
- **pathlib**: File path handling
- **datetime**: Date parsing and formatting
- **re**: Regular expression pattern matching for transaction data
- **logging**: Application logging (set to WARNING level for clean output)

## Code Features

### PDF Processing Functions

- `extract_vested_stocks_from_text()`: Parses vested stock data from text
- `extract_espp_from_text()`: Extracts ESPP purchase information
- `extract_transactions_from_text()`: Processes sold shares using regex patterns
- `extract_vested_data()`: Main extraction function for salary_certificate.pdf
- `extract_table_from_pdf()`: Processes Fidelity transaction summary

### Data Aggregation

- `aggregate_by_date()`: Sums quantities by the same date
- Date parsing and formatting functions for consistent DD.MM.YYYY display
- Chronological sorting of all date-based data

### Display Functions

- `display_vested_results()`: Formats vested stocks and ESPP tables
- `display_results()`: Shows aggregated sold shares data
- Clean table formatting with proper column alignment

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test with sample PDF files
5. Run linting: `ruff check`
6. Commit your changes: `git commit -am 'Add feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.