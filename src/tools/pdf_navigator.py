"""
PDF Navigator - CLI-based PDF tooling for IRS forms
Implements the paper's approach: open(), find(), goto(), worksheet()

This ensures agent reasoning is grounded in official IRS PDFs.
"""

import os
import re
from typing import Optional, List, Dict, Any
from pathlib import Path
import pdfplumber
from PyPDF2 import PdfReader


class PDFNavigator:
    """
    PDF-native tooling for tax form agents.
    Provides grounded access to IRS instruction PDFs.
    """
    
    def __init__(self, irs_forms_path: Optional[str] = None):
        """
        Initialize PDF Navigator
        
        Args:
            irs_forms_path: Path to directory containing IRS PDFs
        """
        self.irs_forms_path = irs_forms_path or os.getenv("IRS_FORMS_PATH", "data/irs_forms")
        self.current_pdf = None
        self.current_pdf_path = None
        self.pdf_reader = None
        self.pdf_plumber = None
        self.pages_cache = {}
        
    def open(self, form_name: str) -> bool:
        """
        Open an IRS form PDF
        
        Args:
            form_name: Name of form (e.g., "1040", "schedule-b", "schedule-c")
            
        Returns:
            True if successfully opened
        """
        # Normalize form name
        form_name = form_name.lower().replace(" ", "-")
        
        # Try different naming conventions
        possible_names = [
            f"f{form_name}-2024.pdf",
            f"f{form_name}--2024.pdf",
            f"{form_name}-2024.pdf",
            f"f{form_name}.pdf",
            f"{form_name}.pdf",
            f"i{form_name}-2024.pdf",  # Instructions
            f"i{form_name}.pdf"
        ]
        
        for name in possible_names:
            path = Path(self.irs_forms_path) / name
            if path.exists():
                self._load_pdf(path)
                return True
        
        print(f"Warning: Could not find PDF for form '{form_name}'")
        print(f"Searched in: {self.irs_forms_path}")
        print(f"Tried: {possible_names}")
        return False
    
    def _load_pdf(self, path: Path):
        """Load PDF using both PyPDF2 and pdfplumber"""
        self.current_pdf_path = path
        self.pdf_reader = PdfReader(str(path))
        self.pdf_plumber = pdfplumber.open(str(path))
        self.pages_cache = {}
        print(f"Loaded PDF: {path.name} ({len(self.pdf_reader.pages)} pages)")
    
    def find(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for text/regex in current PDF
        
        Args:
            query: Search string or regex pattern
            case_sensitive: Case-sensitive search
            
        Returns:
            List of matches with page numbers and context
        """
        if not self.pdf_plumber:
            raise ValueError("No PDF loaded. Call open() first.")
        
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for page_num, page in enumerate(self.pdf_plumber.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            
            # Cache page text
            self.pages_cache[page_num] = text
            
            # Find all matches on this page
            for match in re.finditer(query, text, flags):
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].replace('\n', ' ')
                
                matches.append({
                    'page': page_num,
                    'match': match.group(),
                    'context': context,
                    'position': match.start()
                })
        
        return matches
    
    def goto(self, page: int, line: Optional[str] = None) -> str:
        """
        Navigate to specific page and optionally find a line
        
        Args:
            page: Page number (1-indexed)
            line: Optional line identifier to find (e.g., "Line 11")
            
        Returns:
            Page text or section around line
        """
        if not self.pdf_plumber:
            raise ValueError("No PDF loaded. Call open() first.")
        
        if page < 1 or page > len(self.pdf_plumber.pages):
            raise ValueError(f"Page {page} out of range (1-{len(self.pdf_plumber.pages)})")
        
        # Get page text (use cache if available)
        if page in self.pages_cache:
            text = self.pages_cache[page]
        else:
            text = self.pdf_plumber.pages[page - 1].extract_text()
            self.pages_cache[page] = text
        
        if line:
            # Find the line and return context
            matches = re.finditer(re.escape(line), text, re.IGNORECASE)
            for match in matches:
                # Get paragraph around the match
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 500)
                return text[start:end]
            
            return f"Line '{line}' not found on page {page}\n\nFull page text:\n{text[:1000]}..."
        
        return text
    
    def get_line_instructions(self, line: str, form_name: Optional[str] = None) -> str:
        """
        Get IRS instructions for a specific form line
        
        Args:
            line: Line identifier (e.g., "Line 11", "Schedule C Line 31")
            form_name: Form to search (if different from current)
            
        Returns:
            Instructions text for that line
        """
        # Open form if specified
        if form_name and not self.current_pdf_path:
            if not self.open(form_name):
                return f"Could not load form '{form_name}'"
        
        if not self.pdf_plumber:
            return "No PDF loaded. Unable to get instructions."
        
        # Search for the line
        matches = self.find(line, case_sensitive=False)
        
        if not matches:
            return f"No instructions found for '{line}'"
        
        # Return the first match with extended context
        best_match = matches[0]
        page_num = best_match['page']
        text = self.goto(page_num, line)
        
        return f"=== {line} Instructions (Page {page_num}) ===\n\n{text}"
    
    def worksheet(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Extract an embedded worksheet from the PDF
        
        Args:
            name: Worksheet name (e.g., "Capital Gains Worksheet", "EIC")
            
        Returns:
            Worksheet data if found
        """
        if not self.pdf_plumber:
            raise ValueError("No PDF loaded. Call open() first.")
        
        # Search for worksheet
        matches = self.find(name, case_sensitive=False)
        
        if not matches:
            return None
        
        # Get the page with the worksheet
        page_num = matches[0]['page']
        page = self.pdf_plumber.pages[page_num - 1]
        
        # Try to extract tables
        tables = page.extract_tables()
        
        return {
            'name': name,
            'page': page_num,
            'tables': tables,
            'text': page.extract_text()
        }
    
    def get_tax_table(self, income_range: tuple) -> Optional[str]:
        """
        Extract tax table for specific income range
        
        Args:
            income_range: (min, max) income range
            
        Returns:
            Relevant tax table section
        """
        if not self.pdf_plumber:
            # Try to open tax table instructions
            if not self.open("1040"):
                return None
        
        # Search for income range in tax tables
        min_income, max_income = income_range
        
        # Tax tables usually at the end of 1040 instructions
        # Search last 20 pages
        total_pages = len(self.pdf_plumber.pages)
        start_page = max(1, total_pages - 20)
        
        for page_num in range(start_page, total_pages + 1):
            text = self.goto(page_num)
            # Look for income range
            if str(min_income) in text or str(max_income) in text:
                return f"=== Tax Table (Page {page_num}) ===\n\n{text}"
        
        return None
    
    def close(self):
        """Close current PDF"""
        if self.pdf_plumber:
            self.pdf_plumber.close()
        self.pdf_reader = None
        self.pdf_plumber = None
        self.current_pdf_path = None
        self.pages_cache = {}


# Convenience functions for agents
def get_irs_instructions(line: str, form: str = "1040") -> str:
    """Quick function to get IRS instructions for a line"""
    nav = PDFNavigator()
    nav.open(form)
    return nav.get_line_instructions(line)


def search_irs_form(query: str, form: str = "1040") -> List[Dict[str, Any]]:
    """Quick function to search in an IRS form"""
    nav = PDFNavigator()
    nav.open(form)
    return nav.find(query)


if __name__ == "__main__":
    # Test the PDF navigator
    print("Testing PDF Navigator...")
    
    nav = PDFNavigator()
    
    # Test opening a form
    if nav.open("1040"):
        print("\nSearching for 'standard deduction'...")
        matches = nav.find("standard deduction")
        print(f"Found {len(matches)} matches")
        if matches:
            print(f"\nFirst match: Page {matches[0]['page']}")
            print(f"Context: {matches[0]['context']}")
        
        # Test goto
        print("\nGetting Line 11 instructions...")
        instructions = nav.get_line_instructions("Line 11")
        print(instructions[:500] + "...")
    else:
        print("\nNote: Add IRS PDF forms to data/irs_forms/ to test")
        print("Download from: https://www.irs.gov/forms-instructions")
