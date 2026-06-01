from base_scraper import BaseJobScraper
from playwright.sync_api import sync_playwright


class LinkedInJobFinder(BaseJobScraper):
    """
    LinkedIn-specific scraper implementing the BaseJobScraper.
    Handles infinite scrolling and nested browser calls for job deadlines.
    """

    def __init__(self):
        # Pass the specific filename and slow_mo delay to the base class
        super().__init__(output_filename="linkedin_jobs.csv", slow_mo=500)

    def build_search_url(self, job_title, location):
        return (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={job_title}"
            f"&location={location}"
            f"&sortBy=DD"
        )

    def collect_jobs(self, page):
        # 1. Trigger lazy loading via scrolling
        self._scroll_jobs(page)

        # 2. Extract job cards
        cards = page.locator(".base-card")
        count = cards.count()

        print(f"\nFound {count} jobs\n")

        for index in range(min(count, 100)):
            try:
                card = cards.nth(index)

                # safe_text is inherited from BaseJobScraper
                title = self.safe_text(card.locator(".base-search-card__title"))
                company = self.safe_text(card.locator(".base-search-card__subtitle"))
                location = self.safe_text(card.locator(".job-search-card__location"))
                posted = self.safe_text(card.locator("time"))

                job_url = card.locator("a").first.get_attribute("href")

                print(f"[{index + 1}] {title} | {company} | {location} | {posted}")

                # Fetch deadline using the secondary headless browser logic
                deadline = self.get_deadline(job_url)

                self.jobs.append({
                    "Title": title,
                    "Company": company,
                    "Location": location,
                    "Posted Date": posted,
                    "Application Deadline": deadline,
                    "Job URL": job_url
                })

            except Exception as e:
                print(f"Skipping card: {e}")

    def _scroll_jobs(self, page):
        """Helper method specific to LinkedIn's infinite scroll UI."""
        print("Loading more jobs...")
        for _ in range(15):
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(2000)

    def get_deadline(self, job_url):
        """
        Helper method that spawns a temporary headless browser to
        extract deadline information from the actual job posting.
        """
        deadline = "N/A"

        if not job_url:
            return deadline

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto(job_url, timeout=30000)
                page.wait_for_timeout(3000)

                body = page.locator("body").inner_text()

                keywords = [
                    "Apply before",
                    "Application deadline",
                    "Deadline",
                    "Closing date"
                ]

                for line in body.split("\n"):
                    for keyword in keywords:
                        if keyword.lower() in line.lower():
                            deadline = line.strip()
                            browser.close()
                            return deadline
                browser.close()

        except Exception:
            pass
        return deadline


def main():
    print("=" * 60)
    print("LinkedIn Job Finder (OOP Version)")
    print("=" * 60)

    job_title = input("\nEnter Job Title: ").strip()
    location = input("Enter Location: ").strip()

    bot = LinkedInJobFinder()
    # search_jobs and save_results are inherited from the base class
    bot.search_jobs(job_title=job_title, location=location)
    bot.save_results()


if __name__ == "__main__":
    main()