# Tax Form Processing Application

Each time I need to fill out my Swiss tax forms and enter my vested
and sold stocks from Microsoft one by one, it's a nightmare :D So I created this
application that takes as input the Fidelity "Custom transaction summary" for
the year and the "Salary certificate" that Microsoft Schweiz provides to us.

It reads the individual transactions and shows the aggregated (sold and vested) quantities by date
in the Swiss date format (dd.mm.yyyy), so I only need to copy and paste.

> A Python application for extracting and processing stock transaction data from
PDF tax documents.

## Overview

This application processes PDF documents containing stock transaction data for
tax reporting purposes. It extracts information from two types of documents:

1. **salary_certificate.pdf** - Contains vested stock awards and ESPP (Employee
   Stock Purchase Plan) data

   You can download this document from the payslip (Employee Portal) website:
   https://interactpayroll.ey.com/ > Go to "My documents" and it's the one with
   your employee number as the file name.

2. **Fidelity NetBenefits transaction summary** - Contains sold shares
   transaction data. Here I'm using only the pages where the table with sold
   shares is located (print only these pages and save as PDF).

   Find this document on the Net Benefits (Fidelity) website. Under "Statements/Records" > Custom transaction summary. Download the summary for the whole year.

   Then print as PDF only the pages that contain the table with "Sold shares".

## Features

- **Vested Stock Extraction**: Parses vested stock data with vest dates and
  share quantities
- **ESPP Data Processing**: Extracts Employee Stock Purchase Plan information
- **Sold Shares Analysis**: Processes sold stock transactions with aggregation
  by date
- **Clean Table Output**: Displays data in formatted tables with consistent date
  formatting (DD.MM.YYYY)
- **Date Aggregation**: Automatically sums shares by the same vest/sell dates
- **Individual Transaction Display**: Option to show all individual transactions
  before aggregation
- **Multiple PDF Support**: Processes multiple PDF documents in a single run

## Sample Output

### Default Output (Aggregated Data Only)

```text
================================================================================
VESTED STOCKS 2024
================================================================================
Vest Date       Quantity       
------------------------------
29.02.2024      12.500         
15.04.2024      24.750         
30.05.2024      3.000          
...  
------------------------------
Total unique dates: 8
Total shares: 6.500

================================================================================
ESPP (Employee Stock Purchase Plan)
================================================================================
Off Period      Purchased Shares    
-----------------------------------
092024          20.0000             
-----------------------------------
Total entries: 1
Total purchased shares: 3.0000
================================================================================

================================================================================
SUMMARY 2024
================================================================================
Total Vested Shares:      99.310         
Total Purchased Shares:   25.047         
Total Sold Shares:        165.347        
----------------------------------------
Total Owned Shares:       124.357        
Net Position (Oversold):  40.990         
================================================================================
```

### With Individual Transactions (--show-individual)

When using the `--show-individual` flag, you'll also see detailed transaction
data before the aggregated summary:

```text
================================================================================
INDIVIDUAL TRANSACTIONS
================================================================================
Date            Quantity       
------------------------------
16.01.2024      2.0000         
16.01.2024      3.0000         
02.02.2024      1.0000              
...
------------------------------
Total individual transactions: 45

============================================================
AGGREGATED QUANTITIES BY DATE:
============================================================
Sell Date                 Quantity       
------------------------------------------------------------
16.01.2024                5.0000         
02.02.2024                7.5000         
27.02.2024                2.5000         
...    
============================================================
Total unique dates: 10
Total individual transactions: 45
Grand total quantity: 15.0000
============================================================

================================================================================
SUMMARY 2024
================================================================================
Total Vested Shares:      99.310         
Total Purchased Shares:   25.047         
Total Sold Shares:        165.347        
----------------------------------------
Total Owned Shares:       124.357        
Net Position (Oversold):  40.990         
================================================================================
```

## Development Setup

This project uses a development container for a consistent development
environment.

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
- `Custom transaction summary - Fidelity NetBenefits_ only sales.pdf` - Sold
  shares document

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
python tax_form/main.py --vested-pdf "path/to/salary_certificate.pdf" --sold-pdf "path/to/sales.pdf"

# Use custom path for vested stocks only
python tax_form/main.py --vested-pdf "custom/path/salary_certificate.pdf"

# Use custom path for sold shares only  
python tax_form/main.py --sold-pdf "custom/path/fidelity_sales.pdf"
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

#### Detailed Transaction Analysis

```bash
# Show individual transactions for sold shares only
python tax_form/main.py --sold-pdf "data/sales.pdf" --no-vested --show-individual

# Show individual transactions for both vested and sold shares
python tax_form/main.py --show-individual

# Combine with custom paths and show individual transactions
python tax_form/main.py --vested-pdf "data/salary_certificate.pdf" --sold-pdf "data/sales.pdf" --show-individual
```

#### Command Line Options

- `--vested-pdf FILEPATH`: Path to PDF containing vested stocks and ESPP data
  (default: `data/salary_certificate.pdf`)
- `--sold-pdf FILEPATH`: Path to PDF containing sold shares data (default:
  `data/Custom transaction summary - Fidelity NetBenefits_ only sales.pdf`)
- `--no-vested`: Skip processing vested stocks and ESPP data
- `--no-sold`: Skip processing sold shares data
- `--show-individual`: Show individual transactions in addition to aggregated
  data
- `-h, --help`: Show help message and exit

### Supported PDF Formats

#### salary_certificate.pdf Structure

The application expects this document to contain:

- **Vested Stocks 2024** section with columns: Award Date, Award ID, Vest Date,
  Award Price, Market Value, Shares, etc.
- **ESPP (Employee Stock Purchase Plan)** section with columns: Off Period,
  Purchased Shares, FMV Price, etc.

#### Fidelity Transaction Summary

The application processes transaction data with pattern matching for:

- Date sold or transferred (format: MMM-DD-YYYY)
- Quantity of shares sold

### Project Structure

```text
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

This project is licensed under the MIT License - see the LICENSE file for
details.
