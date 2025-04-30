import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import Set, List, Dict
import json

class WikiAnimalScraper:
    def __init__(self):
        self.base_url = "https://en.wikipedia.org"
        self.visited_pages = set()
        self.visited_categories = set()
        self.animal_data = []
        self.total_categories_processed = 0
        self.total_pages_found = 0
        self.total_pages_processed = 0
        
    def get_page_content(self, url: str) -> BeautifulSoup:
        """Get page content and return BeautifulSoup object."""
        response = requests.get(url)
        return BeautifulSoup(response.content, 'html.parser')
    
    def is_animal_category(self, category: str) -> bool:
        """Check if the category is animal-related."""
        animal_keywords = {
            'animals', 'fauna', 'species', 'vertebrates', 'invertebrates',
            'mammals', 'birds', 'reptiles', 'amphibians', 'fish', 'insects',
            'molluscs', 'crustaceans', 'arachnids', 'worms', 'endangered',
            'extinct', 'wildlife', '_by_', 'animal'
        }
        exclude_keywords = {
            'help:', 'wikipedia:', 'template:', 'portal:', 'special:', 'file:',
            'mediawiki:', 'user:', 'talk:', 'project:'
        }
        category_lower = category.lower()
        return (any(keyword in category_lower for keyword in animal_keywords) and 
                not any(keyword in category_lower for keyword in exclude_keywords))
    
    def get_subcategories_and_pages(self, url: str) -> tuple[set[str], set[str]]:
        """Get all subcategories and pages from a category page."""
        soup = self.get_page_content(url)
        subcategories = set()
        pages = set()
        
        # Get subcategories from all possible locations
        for div_id in ['mw-subcategories', 'mw-normal-catlinks', 'mw-hidden-catlinks']:
            category_div = soup.find('div', {'id': div_id})
            if category_div:
                for link in category_div.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/wiki/Category:') and self.is_animal_category(href):
                        subcategories.add(self.base_url + href)
        
        # Get pages from the category
        pages_div = soup.find('div', {'id': 'mw-pages'})
        if pages_div:
            for link in pages_div.find_all('a', href=True):
                href = link['href']
                if href.startswith('/wiki/') and self.is_valid_article(href):
                    pages.add(self.base_url + href)
        
        # Handle pagination
        next_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if ('pagefrom=' in href or 'pageuntil=' in href) and 'Category:' in href:
                if href.startswith('/w/'):
                    next_links.append(self.base_url + href)
                elif href.startswith('/wiki/'):
                    next_links.append(self.base_url + href)
        
        # Process pagination links
        for next_page_url in next_links:
            try:
                next_soup = self.get_page_content(next_page_url)
                next_pages_div = next_soup.find('div', {'id': 'mw-pages'})
                if next_pages_div:
                    for page_link in next_pages_div.find_all('a', href=True):
                        page_href = page_link['href']
                        if page_href.startswith('/wiki/') and self.is_valid_article(page_href):
                            pages.add(self.base_url + page_href)
                
                # Also check for subcategories in paginated pages
                for div_id in ['mw-subcategories', 'mw-normal-catlinks']:
                    next_cat_div = next_soup.find('div', {'id': div_id})
                    if next_cat_div:
                        for link in next_cat_div.find_all('a', href=True):
                            href = link['href']
                            if href.startswith('/wiki/Category:') and self.is_animal_category(href):
                                subcategories.add(self.base_url + href)
            except Exception as e:
                print(f"Error getting next page: {str(e)}")
            time.sleep(1)  # Rate limiting for pagination
                    
        return subcategories, pages
    
    def extract_page_info(self, url: str) -> Dict:
        """Extract relevant information from an animal page."""
        soup = self.get_page_content(url)
        
        # Get title
        title = soup.find('h1', {'id': 'firstHeading'}).text if soup.find('h1', {'id': 'firstHeading'}) else ''
        if not title:
            return None
            
        # Get main content
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            return None
            
        # Get categories first to verify it's an animal page
        categories = []
        catlinks = soup.find('div', {'id': 'mw-normal-catlinks'})
        if catlinks:
            categories = [link.text for link in catlinks.find_all('a')]
            
        # Check if it's actually an animal-related page
        if not any('animal' in cat.lower() or 
                  'fauna' in cat.lower() or 
                  'species' in cat.lower() or
                  'mammals' in cat.lower() or
                  'birds' in cat.lower() or
                  'reptiles' in cat.lower() or
                  'amphibians' in cat.lower() or
                  'fish' in cat.lower() or
                  'insects' in cat.lower() for cat in categories):
            return None
            
        # Get all paragraphs after removing unwanted elements
        main_content = content_div.find('div', {'class': 'mw-parser-output'})
        if not main_content:
            return None
            
        # Remove unwanted elements
        for element in main_content.find_all(['table', 'div', 'script', 'style', 'sup', 'span']):
            if element.get('class') and any('infobox' in c for c in element.get('class', [])):
                continue  # Keep infoboxes
            element.decompose()
            
        # Get all paragraphs
        paragraphs = main_content.find_all('p', recursive=False)
        main_text = '\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
        
        if not main_text:
            return None
            
        return {
            'title': title,
            'url': url,
            'main_text': main_text,
            'categories': categories
        }
            
        # Get all paragraphs after removing unwanted elements
        main_content = content_div.find('div', {'class': 'mw-parser-output'})
        if not main_content:
            return None
            
        # Remove unwanted elements
        for element in main_content.find_all(['table', 'div', 'script', 'style', 'sup', 'span']):
            if element.get('class') and any('infobox' in c for c in element.get('class', [])):
                continue  # Keep infoboxes
            element.decompose()
            
        # Get all paragraphs
        paragraphs = main_content.find_all('p', recursive=False)
        main_text = '\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
        
        # Get categories from the bottom of the page
        categories = []
        catlinks = soup.find('div', {'id': 'mw-normal-catlinks'})
        if catlinks:
            categories = [link.text for link in catlinks.find_all('a')]
        
        return {
            'title': title,
            'url': url,
            'main_text': main_text,
            'categories': categories
        }
    
    def is_valid_article(self, url: str) -> bool:
        """Check if the URL is a valid article (not a special page)."""
        invalid_patterns = ['Category:', 'File:', 'Template:', 'Help:', 'Wikipedia:', 'Portal:', 'Special:']
        return not any(pattern in url for pattern in invalid_patterns)

    def scrape_animals(self, start_url: str = "https://en.wikipedia.org/wiki/Category:Animals"):
        """Main method to scrape animal pages."""
        category_queue = {start_url}
        pages_to_process = set()
        
        print("Starting animal page collection...")
        print("This will take some time. Progress will be shown every few categories...")
        
        # First, collect all pages from categories
        while category_queue:
            current_url = category_queue.pop()
            
            if current_url in self.visited_categories:
                continue
                
            self.visited_categories.add(current_url)
            self.total_categories_processed += 1
            
            try:
                new_subcategories, new_pages = self.get_subcategories_and_pages(current_url)
                category_queue.update(new_subcategories)
                new_pages = {page for page in new_pages if page not in self.visited_pages}
                pages_to_process.update(new_pages)
                self.total_pages_found += len(new_pages)
                
                if self.total_categories_processed % 5 == 0:
                    print(f"\nProgress update:")
                    print(f"Categories processed: {self.total_categories_processed}")
                    print(f"Categories remaining: {len(category_queue)}")
                    print(f"Total pages found: {self.total_pages_found}")
                    print(f"Pages processed: {self.total_pages_processed}")
                    print(f"Current category: {current_url}")
            except Exception as e:
                print(f"Error processing category {current_url}: {str(e)}")
            
            # Save progress periodically
            if self.total_categories_processed % 20 == 0 and len(self.animal_data) > 0:
                self.save_data('animal_data_partial.json')
                print(f"\nSaved {len(self.animal_data)} entries to animal_data_partial.json")
            
            time.sleep(1)  # Rate limiting
            
        print(f"\nCategory collection complete!")
        print(f"Total categories processed: {self.total_categories_processed}")
        print(f"Total pages found: {self.total_pages_found}")
        print("Starting content extraction...")
        
        # Then process all collected pages
        total_pages = len(pages_to_process)
        print(f"Starting to process {total_pages} pages...")
        
        for i, page_url in enumerate(pages_to_process, 1):
            if page_url in self.visited_pages:
                continue
                
            self.visited_pages.add(page_url)
            try:
                page_info = self.extract_page_info(page_url)
                if page_info and page_info['main_text']:  # Only add if we got content
                    self.animal_data.append(page_info)
                    self.total_pages_processed += 1
                    
                    if self.total_pages_processed % 10 == 0:
                        print(f"\nProgress: {self.total_pages_processed}/{total_pages} pages processed")
                        print(f"Latest addition: {page_info['title']}")
                        # Save progress periodically
                        self.save_data('animal_data_partial.json')
                        print(f"Saved {len(self.animal_data)} entries to animal_data_partial.json")
            except Exception as e:
                print(f"Error processing {page_url}: {str(e)}")
            
            time.sleep(1)  # Rate limiting
    
    def save_data(self, filename: str = 'animal_data.json'):
        """Save the collected data to a JSON file."""
        try:
            print(f"\nAttempting to save {len(self.animal_data)} entries to {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.animal_data, f, ensure_ascii=False, indent=2)
            print(f"Successfully saved data to {filename}")
        except Exception as e:
            print(f"Error saving data to {filename}: {str(e)}")

if __name__ == "__main__":
    scraper = WikiAnimalScraper()
    scraper.scrape_animals()
    scraper.save_data()
