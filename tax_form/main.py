"""Main module for the tax form processing application."""

import argparse
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

import pdfplumber

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def extract_vested_data(pdf_path: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Extract both vested stocks and ESPP data from salary_certificate PDF.

    Args:
        pdf_path: Path to the salary_certificate PDF file

    Returns:
        Dictionary containing 'vested_stocks' and 'espp_data' lists
    """

    with pdfplumber.open(pdf_path) as pdf:
        all_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"

        # Extract vested stocks data
        vested_stocks = extract_vested_stocks_from_text(all_text)

        # Extract ESPP data
        espp_data = extract_espp_from_text(all_text)

        return {"vested_stocks": vested_stocks, "espp_data": espp_data}


def extract_transactions_from_text(text: str) -> List[Dict[str, str]]:
    """
    Extract transaction data from text using regex patterns.

    Args:
        text: Raw text containing transaction data

    Returns:
        List of transaction dictionaries
    """
    transactions = []

    # Pattern to match transaction lines like:
    # Jan-16-2024 Jun-01-2020 3.0000 $549.75 $1,175.99 + $626.24 USD DO
    pattern = r"(\w{3}-\d{2}-\d{4})\s+(\w{3}-\d{2}-\d{4})\s+([\d.]+)\s+\$[\d,.]+"

    lines = text.split("\n")
    for line in lines:
        # Look for date patterns at the start of lines
        match = re.search(pattern, line)
        if match:
            date_sold = match.group(1)
            quantity = match.group(3)

            transactions.append(
                {"Date sold or transferred": date_sold, "Quantity": quantity}
            )

    return transactions


def extract_table_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract table data from PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of dictionaries representing table rows
    """
    all_transactions = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"PDF has {len(pdf.pages)} pages")

            for page_num, page in enumerate(pdf.pages, 1):
                logger.info(f"Processing page {page_num}")

                # Extract all text from the page
                page_text = page.extract_text()

                if page_text:
                    # Look for transaction data in the text
                    transactions = extract_transactions_from_text(page_text)
                    if transactions:
                        logger.info(
                            f"Found {len(transactions)} transactions on page {page_num}"
                        )

                        # Add all transactions (including duplicates)
                        all_transactions.extend(transactions)

                        # Log first few transactions for debugging
                        for i, trans in enumerate(transactions[:3]):
                            logger.info(f"Transaction {i + 1}: {trans}")
                    else:
                        logger.info(f"No transactions found on page {page_num}")

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise

    return all_transactions


def aggregate_by_date(data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregate quantities by date, summing up quantities for the same date.

    Args:
        data: List of transaction dictionaries

    Returns:
        Dictionary with dates as keys and total quantities as values
    """
    date_quantities = {}

    for transaction in data:
        date_sold = transaction.get("Date sold or transferred", "")
        quantity_str = transaction.get("Quantity", "0")

        # Convert quantity to float
        try:
            quantity = float(quantity_str)
        except (ValueError, TypeError):
            logger.warning(f"Invalid quantity value: {quantity_str}")
            continue

        # Add to the total for this date
        if date_sold in date_quantities:
            date_quantities[date_sold] += quantity
        else:
            date_quantities[date_sold] = quantity

    return date_quantities


def display_results(data: List[Dict[str, Any]], show_individual: bool = False) -> None:
    """Display the aggregated results by date and optionally individual transactions."""
    if not data:
        print("No data to display")
        return

    # Show individual transactions if requested
    if show_individual:
        print("=" * 80)
        print("INDIVIDUAL TRANSACTIONS")
        print("=" * 80)
        print(f"{'Date':<15} {'Quantity':<15}")
        print("-" * 30)

        for i, transaction in enumerate(data, 1):
            date_sold = transaction.get("Date sold or transferred", "")
            quantity = transaction.get("Quantity", "0")

            # Format date for display
            from datetime import datetime

            try:
                dt = datetime.strptime(date_sold, "%b-%d-%Y")
                formatted_date = dt.strftime("%d.%m.%Y")
            except ValueError:
                formatted_date = date_sold

            print(f"{formatted_date:<15} {quantity:<15}")

        print("-" * 30)
        print(f"Total individual transactions: {len(data)}")
        print("\n")

    # Show aggregated data by date
    aggregated_data = aggregate_by_date(data)

    print("=" * 60)
    print("AGGREGATED QUANTITIES BY DATE:")
    print("=" * 60)
    print(f"{'Sell Date':<25} {'Quantity':<15}")
    print("-" * 60)

    # Sort by date in ascending order
    from datetime import datetime

    def parse_date(date_str):
        """Parse date string in format 'MMM-DD-YYYY' to datetime object."""
        try:
            return datetime.strptime(date_str, "%b-%d-%Y")
        except ValueError:
            # If parsing fails, return a very early date to put it first
            return datetime(1900, 1, 1)

    def format_date(date_str):
        """Convert date from MMM-DD-YYYY to DD.MM.YYYY format."""
        try:
            dt = datetime.strptime(date_str, "%b-%d-%Y")
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            return date_str  # Return original if parsing fails

    sorted_dates = sorted(aggregated_data.items(), key=lambda x: parse_date(x[0]))

    total_quantity = 0
    for date_sold, total_qty in sorted_dates:
        formatted_date = format_date(date_sold)
        print(f"{formatted_date:<25} {total_qty:<15.4f}")
        total_quantity += total_qty

    print("=" * 60)
    print(f"Total unique dates: {len(aggregated_data)}")
    print(f"Total individual transactions: {len(data)}")
    print(f"Grand total quantity: {total_quantity:.4f}")
    print("=" * 60)


def extract_vested_stocks_from_text(text: str) -> List[Dict[str, str]]:
    """
    Extract vested stocks data from text.

    Args:
        text: Raw text containing vested stocks data

    Returns:
        List of dictionaries with Vest Date and Shares
    """
    vested_stocks = []
    lines = text.split("\n")

    # Find the start of the Vested Stocks section
    in_vested_section = False
    header_line_count = 0
    for line in lines:
        if "Vested Stocks" in line and "2024" in line:
            in_vested_section = True
            continue

        # Stop when we reach the ESPP section
        if "ESPP" in line:
            break

        if in_vested_section and line.strip():
            # Skip header lines
            if ("Award" in line and "Date" in line) or ("Date Date Price" in line):
                header_line_count += 1
                continue

            # Skip the total line at the end
            if (
                line.strip()
                .replace(".", "")
                .replace("'", "")
                .replace(" ", "")
                .isdigit()
            ):
                continue

            # Parse data lines - format: Award_Date Award_ID Vest_Date Award_Price Market_Value Shares ...
            parts = line.split()
            if len(parts) >= 6:
                try:
                    # Extract vest date (3rd column, index 2) and shares (6th column, index 5)
                    vest_date = parts[2]
                    shares = parts[5]

                    # Validate date format (should be DD.MM.YYYY)
                    if "." in vest_date and len(vest_date.split(".")) == 3:
                        vested_stocks.append({"Vest Date": vest_date, "Shares": shares})
                except (IndexError, ValueError) as e:
                    logger.debug(
                        f"Skipping line due to parsing error: {line}, error: {e}"
                    )

    return vested_stocks


def extract_espp_from_text(text: str) -> List[Dict[str, str]]:
    """
    Extract ESPP data from text.

    Args:
        text: Raw text containing ESPP data

    Returns:
        List of dictionaries with Off Period and Purchased Shares
    """
    espp_data = []
    lines = text.split("\n")

    # Find the start of the ESPP section
    in_espp_section = False
    header_line_count = 0
    for line in lines:
        if "ESPP (Employee Stock Purchase Plan)" in line:
            in_espp_section = True
            continue

        # Stop at the end of data or next section
        if in_espp_section and ("Total amount" in line or "Page" in line):
            break

        if in_espp_section and line.strip():
            # Skip header lines
            if ("Off Period" in line and "Purchased" in line) or (
                "Shares Price" in line
            ):
                header_line_count += 1
                continue

            # Skip lines that start with 'CHF' (these are continuation/summary lines)
            if line.strip().startswith("CHF"):
                continue

            # Parse data lines - format: Off_Period Purchased_Shares FMV_Price Purchase_Price ...
            parts = line.split()
            if len(parts) >= 2:
                try:
                    # Extract off period (1st column, index 0) and purchased shares (2nd column, index 1)
                    off_period = parts[0]
                    purchased_shares = parts[1]

                    # Validate that off period looks like a period identifier (should be digits)
                    if off_period.isdigit() or (
                        off_period.isalnum()
                        and purchased_shares.replace(".", "").isdigit()
                    ):
                        espp_data.append(
                            {
                                "Off Period": off_period,
                                "Purchased Shares": purchased_shares,
                            }
                        )
                except (IndexError, ValueError) as e:
                    logger.debug(
                        f"Skipping line due to parsing error: {line}, error: {e}"
                    )

    return espp_data

    return espp_data


def extract_vested_stocks(pdf_path: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Extract both vested stocks and ESPP data from vested stocks PDF.

    Args:
        pdf_path: Path to the vested stocks PDF file

    Returns:
        Dictionary containing both vested stocks and ESPP data
    """
    results = {"vested_stocks": [], "espp_data": []}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"PDF has {len(pdf.pages)} pages")

            for page_num, page in enumerate(pdf.pages, 1):
                logger.info(f"Processing page {page_num}")

                # Extract all text from the page
                page_text = page.extract_text()

                if page_text:
                    # Extract vested stocks data
                    vested_stocks = extract_vested_stocks_from_text(page_text)
                    if vested_stocks:
                        logger.info(
                            f"Found {len(vested_stocks)} vested stock "
                            f"entries on page {page_num}"
                        )
                        results["vested_stocks"].extend(vested_stocks)

                    # Extract ESPP data
                    espp_data = extract_espp_from_text(page_text)
                    if espp_data:
                        logger.info(
                            f"Found {len(espp_data)} ESPP entries on page {page_num}"
                        )
                        results["espp_data"].extend(espp_data)

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise

    return results


def display_vested_results(
    data: Dict[str, List[Dict[str, str]]], show_individual: bool = False
) -> None:
    """Display the results from salary_certificate PDF extraction."""
    print("=" * 80)
    print("VESTED STOCKS 2024")
    print("=" * 80)

    vested_stocks = data["vested_stocks"]
    if vested_stocks:
        # Show individual vested transactions if requested
        if show_individual:
            print("INDIVIDUAL VESTED TRANSACTIONS")
            print("=" * 80)
            print(f"{'Vest Date':<15} {'Quantity':<15}")
            print("-" * 30)

            for entry in vested_stocks:
                vest_date = entry["Vest Date"]
                shares = entry["Shares"]
                print(f"{vest_date:<15} {shares:<15}")

            print("-" * 30)
            print(f"Total individual vested transactions: {len(vested_stocks)}")
            print("\nAGGREGATED VESTED STOCKS BY DATE")
            print("=" * 80)

        # Aggregate shares by vest date
        date_shares = {}
        for entry in vested_stocks:
            vest_date = entry["Vest Date"]
            shares = entry["Shares"]

            # Convert shares to float
            try:
                shares_float = float(shares.replace(",", "").replace("'", ""))
                if vest_date in date_shares:
                    date_shares[vest_date] += shares_float
                else:
                    date_shares[vest_date] = shares_float
            except ValueError:
                pass

        # Sort dates chronologically
        from datetime import datetime

        def parse_vest_date(date_str):
            """Parse date string in format 'DD.MM.YYYY' to datetime object."""
            try:
                return datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                # If parsing fails, return a very early date
                return datetime(1900, 1, 1)

        sorted_dates = sorted(date_shares.items(), key=lambda x: parse_vest_date(x[0]))

        print(f"{'Vest Date':<15} {'Quantity':<15}")
        print("-" * 30)

        total_shares = 0
        for vest_date, shares in sorted_dates:
            print(f"{vest_date:<15} {shares:<15.3f}")
            total_shares += shares

        print("-" * 30)
        print(f"Total unique dates: {len(date_shares)}")
        print(f"Total shares: {total_shares:.3f}")
    else:
        print("No vested stocks data found")

    print("\n" + "=" * 80)
    print("ESPP (Employee Stock Purchase Plan)")
    print("=" * 80)

    espp_data = data["espp_data"]
    if espp_data:
        print(f"{'Off Period':<15} {'Purchased Shares':<20}")
        print("-" * 35)

        total_purchased = 0
        for entry in espp_data:
            off_period = entry["Off Period"]
            purchased_shares = entry["Purchased Shares"]
            print(f"{off_period:<15} {purchased_shares:<20}")

            # Try to add to total
            try:
                clean_shares = purchased_shares.replace(",", "").replace("'", "")
                total_purchased += float(clean_shares)
            except ValueError:
                pass

        print("-" * 35)
        print(f"Total entries: {len(espp_data)}")
        print(f"Total purchased shares: {total_purchased:.4f}")
    else:
        print("No ESPP data found")

    print("=" * 80)


def read_vested_data(
    pdf_path: str, show_individual: bool = False
) -> tuple[float, float]:
    """Extract and display data from salary_certificate PDF.

    Args:
        pdf_path: Path to the PDF file
        show_individual: Whether to show individual vested transactions

    Returns:
        Tuple of (total shares vested, total shares purchased)
    """
    if not Path(pdf_path).exists():
        print(f"PDF file not found: {pdf_path}")
        return 0.0, 0.0

    try:
        # Extract data from PDF
        data = extract_vested_data(pdf_path)

        if data["vested_stocks"] or data["espp_data"]:
            display_vested_results(data, show_individual)

            # Calculate total vested shares
            total_vested = 0.0
            for entry in data["vested_stocks"]:
                try:
                    shares = float(entry["Shares"].replace(",", "").replace("'", ""))
                    total_vested += shares
                except ValueError:
                    pass

            # Calculate total purchased shares from ESPP
            total_purchased = 0.0
            for entry in data["espp_data"]:
                try:
                    purchased_shares = entry["Purchased Shares"]
                    shares = float(purchased_shares.replace(",", "").replace("'", ""))
                    total_purchased += shares
                except ValueError:
                    pass

            return total_vested, total_purchased
        else:
            print("No data extracted from PDF")
            return 0.0, 0.0

    except Exception as e:
        print(f"Error processing PDF: {e}")
        return 0.0, 0.0


def read_sold_shares(pdf_path: str, show_individual: bool = False) -> float:
    """Extract and display sold shares data.

    Args:
        pdf_path: Path to the PDF file
        show_individual: Whether to show individual transactions

    Returns:
        Total shares sold
    """
    if not Path(pdf_path).exists():
        print(f"PDF file not found: {pdf_path}")
        return 0.0

    try:
        # Extract transaction data from PDF
        transactions = extract_table_from_pdf(pdf_path)

        if transactions:
            display_results(transactions, show_individual)

            # Calculate total sold shares
            total_sold = 0.0
            for transaction in transactions:
                try:
                    quantity = float(transaction.get("Quantity", "0"))
                    total_sold += quantity
                except ValueError:
                    pass

            return total_sold
        else:
            print("No transaction data extracted from PDF")
            return 0.0

    except Exception as e:
        print(f"Error processing PDF: {e}")
        return 0.0


def display_summary(
    total_vested: float, total_purchased: float, total_sold: float
) -> None:
    """Display summary of vested, purchased, and sold shares."""
    print("\n" + "=" * 80)
    print("SUMMARY 2024")
    print("=" * 80)
    print(f"{'Total Vested Shares:':<25} {total_vested:<15.3f}")
    print(f"{'Total Purchased Shares:':<25} {total_purchased:<15.3f}")
    print(f"{'Total Sold Shares:':<25} {total_sold:<15.3f}")
    print("-" * 40)

    difference = (total_vested + total_purchased) - total_sold
    if difference >= 0:
        print(f"{'Net Position (Remaining):':<25} {difference:<15.3f}")
    else:
        print(f"{'Net Position (Oversold):':<25} {abs(difference):<15.3f}")

    print("=" * 80)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process stock transaction data from PDF files for tax reporting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default paths
  python tax_form/main.py
  
  # Specify custom paths
  python tax_form/main.py --vested-pdf "data/salary_certificate.pdf" --sold-pdf data/sales.pdf
  
  # Process only vested stocks
  python tax_form/main.py --vested-pdf "data/salary_certificate.pdf" --no-sold
  
  # Process only sold shares with individual transactions shown
  python tax_form/main.py --sold-pdf data/sales.pdf --no-vested --show-individual
  
  # Show individual transactions for both types
  python tax_form/main.py --show-individual
        """,
    )

    parser.add_argument(
        "--vested-pdf",
        type=str,
        default="data/salary_certificate.pdf",
        help="Path to the PDF containing vested stocks and ESPP data "
        "(default: data/salary_certificate.pdf)",
    )

    parser.add_argument(
        "--sold-pdf",
        type=str,
        default="data/Custom transaction summary - Fidelity NetBenefits_ only sales.pdf",
        help="Path to the PDF containing sold shares data "
        "(default: data/Custom transaction summary - Fidelity NetBenefits_ only sales.pdf)",
    )

    parser.add_argument(
        "--no-vested",
        action="store_true",
        help="Skip processing vested stocks and ESPP data",
    )

    parser.add_argument(
        "--no-sold", action="store_true", help="Skip processing sold shares data"
    )

    parser.add_argument(
        "--show-individual",
        action="store_true",
        help="Show individual transactions in addition to aggregated data",
    )

    return parser.parse_args()


if __name__ == "__main__":
    # Set up cleaner output by suppressing debug info
    logging.getLogger("pdfplumber").setLevel(logging.WARNING)

    args = parse_arguments()

    total_vested = 0.0
    total_purchased = 0.0
    total_sold = 0.0

    # Process vested stocks and ESPP data
    if not args.no_vested:
        total_vested, total_purchased = read_vested_data(
            args.vested_pdf, args.show_individual
        )

    # Add separator if processing both types
    if not args.no_vested and not args.no_sold:
        print("\n" + "=" * 100 + "\n")

    # Process sold shares data
    if not args.no_sold:
        total_sold = read_sold_shares(args.sold_pdf, args.show_individual)

    # Display summary if both types were processed
    if not args.no_vested and not args.no_sold:
        display_summary(total_vested, total_purchased, total_sold)
