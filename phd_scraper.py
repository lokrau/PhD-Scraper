import requests
import pandas as pd
import time
import os
from bs4 import BeautifulSoup

BASE_URL = "https://fellowshipbard.com/category/phd-scholarships/"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_university_links():
    """
    Collects links to individual university PhD scholarship pages by paginating through the listing.
    Returns a list of URLs.
    """
    page = 1
    all_links = []

    # Limit pagination to 5 pages
    while page <= 5:
        # Construct the correct URL for each page
        paged_url = f"{BASE_URL}page/{page}/" if page > 1 else BASE_URL
        print(f"Fetching university links from: {paged_url}")
        
        # Send HTTP request to the page
        response = requests.get(paged_url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Stopped at page {page}: status code {response.status_code}")
            break

        # Parse the page content
        soup = BeautifulSoup(response.text, "html.parser")
        # Extract all links that point to university posts
        links = [a.get("href") for a in soup.select('a.elementor-post__thumbnail__link') if a.get("href")]

        # Stop if no more links are found
        if not links:
            print(f"No links found on page {page}. Assuming end of listings.")
            break

        all_links.extend(links)
        page += 1
        time.sleep(1)  # Don't overload the server with requests

    return all_links


def get_positions_from_university_page(url):
    """
    Scrapes PhD positions from an individual university page.
    Returns a list of dictionaries, each containing position details.
    """
    try:
        # Request the university's scholarship page
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract university name from the page title
        university_name = soup.find("h1", class_="entry-title").text.strip()

        # Find the main content container
        content_div = soup.find("div", class_="entry-content")
        if not content_div:
            return []

        children = list(content_div.children) # Flatten the HTML tree
        positions = []
        i = 0

        # Loop through all children of the content
        while i < len(children):
            tag = children[i]
            # Look for position sections marked with <h1>
            if tag.name == "h1":
                try:
                    title = tag.get_text(strip=True)

                    # Description (next <p>)
                    i += 1
                    while i < len(children) and children[i].name != "p":
                        i += 1
                    description = children[i].get_text(strip=True)

                    # Application Deadline (next <h3>)
                    i += 1
                    while i < len(children) and children[i].name != "h3":
                        i += 1
                    deadline_raw = children[i].get_text(strip=True)
                    deadline = deadline_raw.replace("Application Deadline:", "").strip()

                    # Apply link (next <p> with <a>)
                    i += 1
                    while i < len(children) and children[i].name != "p":
                        i += 1
                    apply_tag = children[i].find("a")
                    link = apply_tag["href"] if apply_tag else None

                    # Filter out postdoctoral positions
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
                    print(f"Error parsing position at index {i}: {e}")
            i += 1

        return positions
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return []


def scrape_all():
    """
    Master function to scrape all PhD positions from all university pages.
    Returns a list of all positions found.
    """
    all_positions = []
    university_links = get_university_links()
    print(f"Found {len(university_links)} university links.")

    # Iterate over each university's page and collect position data
    for url in university_links:
        print(f"Scraping: {url}")
        positions = get_positions_from_university_page(url)
        all_positions.extend(positions)
        time.sleep(1)  # Don't overload the server with requests

    return all_positions

if __name__ == "__main__":
    data = scrape_all() # Get all PhD position data
    df = pd.DataFrame(data) # Convert to DataFrame
    os.makedirs("data", exist_ok=True) # Create data directory if it doesn't exist
    df.to_csv("data/phd_positions.csv", index=False) # Save to CSV
    print("Scraping complete. Saved to data/phd_positions.csv")