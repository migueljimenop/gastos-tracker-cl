"""
Falabella (CMR Falabella) Chile scraper using Playwright.

NOTE: Web scraping may violate Falabella's Terms of Service.
Use at your own risk. The selectors below may need updating
if Falabella changes their portal layout.

Portal: https://www.falabella.com/falabella-cl/myAccount/cmr
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from app.models import BankSource, TransactionType
from app.scrapers.base import BaseScraper, RawTransaction


class FalabellaScraper(BaseScraper):

    LOGIN_URL = "https://www.falabella.com/falabella-cl/myAccount/login"
    MOVEMENTS_URL = "https://www.falabella.com/falabella-cl/myAccount/cmr/movimientos"

    async def fetch_transactions(self, months_back: int = 1) -> list[RawTransaction]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")

        transactions: list[RawTransaction] = []
        since_date = datetime.now() - timedelta(days=30 * months_back)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            try:
                # Step 1: Go to login
                await page.goto(self.LOGIN_URL, wait_until="networkidle")

                # Step 2: Enter RUT
                # NOTE: Inspect the actual portal for correct selectors
                await page.fill('input[name="rut"], input[placeholder*="RUT"]', self._normalize_rut(self.rut))
                await page.fill('input[type="password"]', self.password)
                await page.click('button[type="submit"]')
                await page.wait_for_load_state("networkidle")

                # Step 3: Go to CMR movements
                await page.goto(self.MOVEMENTS_URL, wait_until="networkidle")

                # Step 4: Optionally select date range (Falabella may have a date filter)
                # This is portal-specific — add date picker interactions here if needed

                # Step 5: Parse movements
                rows = await page.query_selector_all("[class*='movement-row'], table tbody tr")

                for row in rows:
                    tx = await self._parse_row(row, since_date)
                    if tx:
                        transactions.append(tx)

            finally:
                await browser.close()

        return transactions

    async def _parse_row(self, row, since_date: datetime) -> Optional[RawTransaction]:
        """Parse a single movement row. Adjust selectors based on Falabella's actual HTML."""
        try:
            cells = await row.query_selector_all("td, [class*='cell']")
            if len(cells) < 3:
                return None

            date_text = await cells[0].inner_text()
            description = await cells[1].inner_text()
            amount_text = await cells[2].inner_text()

            # Falabella typically uses DD-MM-YYYY or DD/MM/YYYY
            for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    tx_date = datetime.strptime(date_text.strip(), fmt)
                    break
                except ValueError:
                    continue
            else:
                return None

            if tx_date < since_date:
                return None

            clean_amount = (
                amount_text.strip()
                .replace("$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
            is_credit = clean_amount.startswith("+") or "abono" in description.lower()
            clean_amount = clean_amount.lstrip("+-")
            amount = Decimal(clean_amount)

            return RawTransaction(
                date=tx_date,
                description=description.strip(),
                amount=amount,
                transaction_type=TransactionType.CREDIT if is_credit else TransactionType.DEBIT,
                bank_source=BankSource.FALABELLA,
                external_id=f"falabella-{tx_date.date()}-{amount}",
            )
        except (ValueError, IndexError, Exception):
            return None
