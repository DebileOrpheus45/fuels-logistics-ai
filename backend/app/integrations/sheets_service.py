"""
Google Sheets integration for updating external dashboards.

Setup Instructions:
1. Go to Google Cloud Console: https://console.cloud.google.com
2. Enable Google Sheets API: APIs & Services > Enable APIs > Google Sheets API
3. Create a Service Account:
   - APIs & Services > Credentials > Create Credentials > Service Account
   - Download the JSON key file
4. Save the JSON file as 'sheets_credentials.json' in the backend folder
5. Share your Google Sheet with the service account email (found in the JSON file)

The service account email looks like: your-service@your-project.iam.gserviceaccount.com
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if gspread is available
try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    logger.warning("Google Sheets libraries not installed. Run: pip install gspread google-auth")


# Paths for credentials
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'sheets_credentials.json')

# Scopes for Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


class GoogleSheetsService:
    """Google Sheets service for updating external dashboards."""

    def __init__(self):
        self.client = None
        self.is_configured = False
        self._cached_sheets = {}

        if SHEETS_AVAILABLE:
            self._initialize()

    def _initialize(self):
        """Initialize Google Sheets client."""
        if not os.path.exists(CREDENTIALS_PATH):
            logger.warning(f"Sheets credentials not found: {CREDENTIALS_PATH}")
            return

        try:
            creds = Credentials.from_service_account_file(
                CREDENTIALS_PATH,
                scopes=SCOPES
            )
            self.client = gspread.authorize(creds)
            self.is_configured = True
            logger.info("Google Sheets service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Google Sheets: {e}")

    def open_spreadsheet(self, spreadsheet_id: str) -> Optional[Any]:
        """
        Open a spreadsheet by ID.

        Args:
            spreadsheet_id: The Google Sheets ID (from URL)

        Returns:
            gspread Spreadsheet object or None
        """
        if not self.is_configured:
            logger.warning("Google Sheets not configured")
            return None

        if spreadsheet_id in self._cached_sheets:
            return self._cached_sheets[spreadsheet_id]

        try:
            sheet = self.client.open_by_key(spreadsheet_id)
            self._cached_sheets[spreadsheet_id] = sheet
            return sheet
        except Exception as e:
            logger.error(f"Error opening spreadsheet {spreadsheet_id}: {e}")
            return None

    def update_cell(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        row: int,
        col: int,
        value: Any
    ) -> bool:
        """
        Update a single cell in a worksheet.

        Args:
            spreadsheet_id: The Google Sheets ID
            worksheet_name: Name of the worksheet tab
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured:
            logger.info(f"[MOCK] Update cell ({row}, {col}) = {value}")
            return True

        try:
            sheet = self.open_spreadsheet(spreadsheet_id)
            if not sheet:
                return False

            worksheet = sheet.worksheet(worksheet_name)
            worksheet.update_cell(row, col, value)
            logger.info(f"Updated cell ({row}, {col}) in {worksheet_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating cell: {e}")
            return False

    def update_eta_column(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        po_number: str,
        po_column: int,
        eta_column: int,
        eta_value: str
    ) -> bool:
        """
        Find a PO number in a column and update its ETA in another column.

        Args:
            spreadsheet_id: The Google Sheets ID
            worksheet_name: Name of the worksheet tab
            po_number: PO number to find
            po_column: Column number where PO numbers are (1-indexed)
            eta_column: Column number where ETAs should be updated (1-indexed)
            eta_value: New ETA value to set

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured:
            logger.info(f"[MOCK] Update ETA for PO {po_number}: {eta_value}")
            return True

        try:
            sheet = self.open_spreadsheet(spreadsheet_id)
            if not sheet:
                return False

            worksheet = sheet.worksheet(worksheet_name)

            # Get all values in the PO column
            po_values = worksheet.col_values(po_column)

            # Find the row with matching PO number
            row = None
            for i, val in enumerate(po_values, start=1):
                if str(val).strip() == str(po_number).strip():
                    row = i
                    break

            if row is None:
                logger.warning(f"PO {po_number} not found in column {po_column}")
                return False

            # Update the ETA
            worksheet.update_cell(row, eta_column, eta_value)
            logger.info(f"Updated ETA for PO {po_number} (row {row}): {eta_value}")
            return True

        except Exception as e:
            logger.error(f"Error updating ETA: {e}")
            return False

    def batch_update(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        updates: List[Dict[str, Any]]
    ) -> bool:
        """
        Perform multiple cell updates at once.

        Args:
            spreadsheet_id: The Google Sheets ID
            worksheet_name: Name of the worksheet tab
            updates: List of dicts with 'row', 'col', 'value'

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured:
            logger.info(f"[MOCK] Batch update: {len(updates)} cells")
            return True

        try:
            sheet = self.open_spreadsheet(spreadsheet_id)
            if not sheet:
                return False

            worksheet = sheet.worksheet(worksheet_name)

            # Convert to gspread format
            cells = []
            for update in updates:
                cell = worksheet.cell(update['row'], update['col'])
                cell.value = update['value']
                cells.append(cell)

            worksheet.update_cells(cells)
            logger.info(f"Batch updated {len(updates)} cells in {worksheet_name}")
            return True

        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            return False

    def read_range(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        range_notation: str
    ) -> Optional[List[List[Any]]]:
        """
        Read a range of cells.

        Args:
            spreadsheet_id: The Google Sheets ID
            worksheet_name: Name of the worksheet tab
            range_notation: A1 notation range (e.g., "A1:D10")

        Returns:
            2D list of values or None
        """
        if not self.is_configured:
            logger.warning("Google Sheets not configured")
            return None

        try:
            sheet = self.open_spreadsheet(spreadsheet_id)
            if not sheet:
                return None

            worksheet = sheet.worksheet(worksheet_name)
            return worksheet.get(range_notation)

        except Exception as e:
            logger.error(f"Error reading range: {e}")
            return None

    def append_row(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        values: List[Any]
    ) -> bool:
        """
        Append a row to the end of a worksheet.

        Args:
            spreadsheet_id: The Google Sheets ID
            worksheet_name: Name of the worksheet tab
            values: List of values for the new row

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured:
            logger.info(f"[MOCK] Append row: {values}")
            return True

        try:
            sheet = self.open_spreadsheet(spreadsheet_id)
            if not sheet:
                return False

            worksheet = sheet.worksheet(worksheet_name)
            worksheet.append_row(values)
            logger.info(f"Appended row to {worksheet_name}")
            return True

        except Exception as e:
            logger.error(f"Error appending row: {e}")
            return False


# Create singleton instance
sheets_service = GoogleSheetsService()
