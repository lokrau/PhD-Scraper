import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URLS = [
    "https://fellowshipbard.com/category/phd-scholarships/",
    "https://vacancyedu.com/fully-funded-phd-positions/"
]

def get_university_links(base_url):
    """
    Collects links to individual university PhD scholarship pages for a given base URL.
    Returns a list of URLs.
    """
    page = 1
    all_links = []

    while page <= 5:
        paged_url = f"{base_url}page/{page}/" if page > 1 else base_url
        print(f"Fetching university links from: {paged_url}")
        
        try:
            response = requests.get(paged_url, headers=HEADERS)
            if response.status_code != 200:
                print(f"Stopped at page {page}: status code {response.status_code}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            links = [a.get("href") for a in soup.select('a.elementor-post__thumbnail__link') if a.get("href")]

            if not links:
                print(f"No links found on page {page}. Assuming end of listings.")
                break

            all_links.extend(links)
            page += 1
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching links from {paged_url}: {e}")
            break

    return all_links


def get_positions_from_university_page(url):
    """
    Scrapes PhD positions from an individual university page.
    Returns a list of dictionaries, each containing position details.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        university_name = soup.find("h1", class_="entry-title").text.strip()
        content_div = soup.find("div", class_="entry-content")
        if not content_div:
            return []

        children = list(content_div.children)
        positions = []
        i = 0

        while i < len(children):
            tag = children[i]
            if tag.name == "h1":
                try:
                    title = tag.get_text(strip=True)

                    # Get description
                    i += 1
                    while i < len(children) and children[i].name != "p":
                        i += 1
                    description = children[i].get_text(strip=True)

                    # Get deadline
                    i += 1
                    while i < len(children) and children[i].name != "h3":
                        i += 1
                    deadline_raw = children[i].get_text(strip=True)
                    deadline = deadline_raw.replace("Application Deadline:", "").strip()

                    # Get application link
                    i += 1
                    while i < len(children) and children[i].name != "p":
                        i += 1
                    apply_tag = children[i].find("a")
                    link = apply_tag["href"] if apply_tag else None

                    if "Postdoctoral Position" not in title:
                        positions.append({
                            "university": university_name,
                            "title": title,
                            "description": description,
                            "application_deadline": deadline,
                            "application_link": link,
                            "source_url": url
                        })
                except Exception as e:
                    print(f"Error parsing position at index {i} on {url}: {e}")
            i += 1

        return positions
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return []


def scrape_all():
    """
    Master function to scrape all PhD positions from all supported base URLs.
    Returns a list of all positions found.
    """
    all_positions = []

    for base_url in BASE_URLS:
        print(f"\nScraping source: {base_url}")
        university_links = get_university_links(base_url)
        print(f"Found {len(university_links)} university links.")

        for url in university_links:
            print(f"Scraping: {url}")
            positions = get_positions_from_university_page(url)
            all_positions.extend(positions)
            time.sleep(1)

    return all_positions


if __name__ == "__main__":
    data = scrape_all()
    df = pd.DataFrame(data)
    df.to_csv("phd_positions.csv", index=False)
    print("Scraping complete. Saved to phd_positions.csv")
