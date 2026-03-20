"""
Santander Chile scraper using Playwright.

NOTE: Web scraping may violate Santander's Terms of Service.
Use at your own risk. The selectors below may need updating
if Santander changes their portal layout.

Portal: https://banco.santander.cl
"""
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import BankSource, TransactionType
from app.scrapers.base import BaseScraper, RawTransaction


class SantanderScraper(BaseScraper):

    LOGIN_URL = "https://banco.santander.cl/personas"

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
                # Step 1: Navigate to login
                await page.goto(self.LOGIN_URL, wait_until="networkidle")

                # Step 2: Enter RUT
                # NOTE: Selectors may need adjustment based on current portal HTML
                await page.fill('input[name="rut"], input[id*="rut"]', self._normalize_rut(self.rut))
                await page.click('button[type="submit"], button:has-text("Continuar")')
                await page.wait_for_load_state("networkidle")

                # Step 3: Enter password
                await page.fill('input[type="password"]', self.password)
                await page.click('button[type="submit"], button:has-text("Ingresar")')
                await page.wait_for_load_state("networkidle")

                # Step 4: Navigate to account movements
                # This path will vary — adjust to the actual portal navigation
                await page.goto("https://banco.santander.cl/personas/cuentas/movimientos", wait_until="networkidle")

                # Step 5: Parse transaction table
                # The selector below is illustrative — inspect the actual portal to get real selectors
                rows = await page.query_selector_all("table.movimientos tbody tr, [data-testid='movement-row']")

                for row in rows:
                    tx = await self._parse_row(row, since_date)
                    if tx:
                        transactions.append(tx)

            finally:
                await browser.close()

        return transactions

    async def _parse_row(self, row, since_date: datetime) -> RawTransaction | None:
        """Parse a single table row into a RawTransaction. Adjust selectors as needed."""
        try:
            cells = await row.query_selector_all("td")
            if len(cells) < 3:
                return None

            date_text = await cells[0].inner_text()
            description = await cells[1].inner_text()
            amount_text = await cells[2].inner_text()

            # Parse date — Santander typically uses DD/MM/YYYY
            tx_date = datetime.strptime(date_text.strip(), "%d/%m/%Y")
            if tx_date < since_date:
                return None

            # Parse amount — strip currency symbols and thousand separators
            clean_amount = amount_text.strip().replace("$", "").replace(".", "").replace(",", ".").strip()
            is_credit = clean_amount.startswith("+")
            clean_amount = clean_amount.lstrip("+-")
            amount = Decimal(clean_amount)

            return RawTransaction(
                date=tx_date,
                description=description.strip(),
                amount=amount,
                transaction_type=TransactionType.CREDIT if is_credit else TransactionType.DEBIT,
                bank_source=BankSource.SANTANDER,
                external_id=f"santander-{tx_date.date()}-{amount}",
            )
        except (ValueError, IndexError):
            return None
