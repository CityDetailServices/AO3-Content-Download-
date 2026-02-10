import requests
from bs4 import BeautifulSoup
import os
import re
import time
from urllib.parse import urljoin, urlparse

def download_ao3_work(work_url, output_dir="ao3_download"):
    """Download entire AO3 work including all chapters"""

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    print(f"Fetching work info from: {work_url}")

    # Get work index page to find all chapter links
    response = session.get(work_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract work metadata
    work_title = soup.find('h1', class_='title').get_text(strip=True) if soup.find('h1', class_='title') else "Unknown Work"
    author_elem = soup.find('a', href=re.compile(r'/users/'))
    author = author_elem.get_text(strip=True) if author_elem else "Unknown Author"

    print(f"Title: {work_title}")
    print(f"Author: {author}")

    # Find all chapter links
    chapter_links = []
    chapter_list = soup.find('ol', class_='index group')
    if chapter_list:
        for li in chapter_list.find_all('li', recursive=False):
            link = li.find('a', href=True)
            if link:
                chapter_links.append(urljoin(work_url, link['href']))
    else:
        # Single chapter work
        chapter_links = [work_url]

    print(f"Found {len(chapter_links)} chapters")

    # Download each chapter
    for i, chapter_url in enumerate(chapter_links, 1):
        print(f"Downloading chapter {i}/{len(chapter_links)}: {chapter_url}")

        try:
            chapter_response = session.get(chapter_url)
            chapter_response.raise_for_status()
            chapter_soup = BeautifulSoup(chapter_response.text, 'html.parser')

            # Extract chapter title
            chapter_title_elem = chapter_soup.find('h2', class_='title')
            chapter_title = chapter_title_elem.get_text(strip=True) if chapter_title_elem else f"Chapter {i}"

            # Extract chapter content
            content = chapter_soup.find('div', id='workskin')
            if not content:
                content = chapter_soup.find('div', role='article')

            if content:
                # Clean up content - remove headers, navigation, etc.
                for unwanted in content.find_all(['h1', 'h2', 'h3', '.actions', '.notes', 'hr']):
                    unwanted.decompose()

                # Save as HTML
                html_filename = f"{i:03d}_{re.sub(r'[^\w\s-]', '', chapter_title)[:50]}.html"
                html_path = os.path.join(output_dir, html_filename)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(f"<html><head><title>{work_title} - {chapter_title}</title></head><body>")
                    f.write(str(content))
                    f.write("</body></html>")

                # Save as Markdown (cleaner text)
                md_content = content.get_text(separator='\n\n', strip=True)
                md_filename = f"{i:03d}_{re.sub(r'[^\w\s-]', '', chapter_title)[:50]}.md"
                md_path = os.path.join(output_dir, md_filename)
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {work_title}\n\n")
                    f.write(f"**Author:** {author}\n\n")
                    f.write(f"## {chapter_title}\n\n")
                    f.write(md_content)

                print(f"  Saved: {html_filename} and {md_filename}")

            # Be respectful - add delay between requests
            time.sleep(1)

        except Exception as e:
            print(f"  Error downloading chapter {i}: {e}")

    # Create index file
    index_path = os.path.join(output_dir, "INDEX.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f"# {work_title}\n\n")
        f.write(f"**Author:** {author}\n")
        f.write(f"**Chapters:** {len(chapter_links)}\n\n")
        f.write("## Chapter List\n\n")
        for i, chapter_url in enumerate(chapter_links, 1):
            chapter_name = f"{i:03d}_*.md"
            f.write(f"- [{chapter_name}]({chapter_url})\n")

    print(f"\nDownload complete! Files saved to: {output_dir}")

# Usage
if __name__ == "__main__":
    target_url = "https://archiveofourown.org/works/70746881/chapters/183904501"
    download_ao3_work(target_url)
