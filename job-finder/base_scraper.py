import pandas as pd
from playwright.sync_api import sync_playwright
from abc import ABC, abstractmethod
import os


class BaseJobScraper(ABC):
    """
    Abstract base class for Playwright job scrapers.
    Handles browser lifecycle, safe text extraction, and CSV exporting.
    """

    def __init__(self, output_filename="scraped_jobs.csv", slow_mo=300):
        self.jobs = []
        self.output_filename = output_filename
        self.slow_mo = slow_mo

    @abstractmethod
    def build_search_url(self, job_title, location):
        """
        Must be implemented by subclasses to return the site-specific URL.
        """
        pass

    @abstractmethod
    def collect_jobs(self, page):
        """
        Must be implemented by subclasses to handle pagination/scrolling
        and extracting elements via site-specific selectors.
        """
        pass

    def search_jobs(self, job_title, location=""):
        """
        Standardized browser initialization and navigation flow.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                slow_mo=self.slow_mo
            )

            context = browser.new_context()
            page = context.new_page()

            search_url = self.build_search_url(job_title, location)
            print(f"\nOpening:\n{search_url}\n")

            page.goto(
                search_url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            # Brief pause to allow dynamic content to settle
            page.wait_for_timeout(3000)

            # Defer to the subclass for specific scraping logic
            self.collect_jobs(page)

            browser.close()

    def safe_text(self, locator):
        """
        Safely extracts inner text from a locator, returning an empty
        string if the element is missing to prevent script crashes.
        """
        try:
            return locator.first.inner_text().strip()
        except Exception:
            return ""

    def save_results(self):
        if not self.jobs:
            print("No jobs found to save.")
            return

        os.makedirs("results", exist_ok=True)

        file_path = os.path.join("results", self.output_filename)

        # Delete existing file if present
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted existing file: {file_path}")

        df = pd.DataFrame(self.jobs)

        df.to_csv(
            file_path,
            index=False,
            encoding="utf-8-sig"
        )

        print(f"Saved {len(df)} jobs -> {file_path}")