import requests
from bs4 import BeautifulSoup
import time
from typing import Set, List, Dict
import json
import os
from datetime import datetime

class WikiAnimalScraper:
    def __init__(self):
        self.base_url = "https://en.wikipedia.org"
        self.visited_pages = set()
        self.visited_categories = set()
        self.animal_data = []
        self.total_categories_processed = 0
        self.total_pages_found = 0
        self.total_pages_processed = 0
        
        # Load existing data if available
        self.load_existing_data()
        
    def load_existing_data(self):
        """Load existing data from partial file if it exists."""
        partial_file = 'animal_data_partial.json'
        if os.path.exists(partial_file):
            try:
                with open(partial_file, 'r', encoding='utf-8') as f:
                    self.animal_data = json.load(f)
                    self.visited_pages = {entry['url'] for entry in self.animal_data}
                print(f"Loaded {len(self.animal_data)} existing entries")
            except Exception as e:
                print(f"Error loading existing data: {str(e)}")
    
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
        try:
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
            
            return subcategories, pages
        except Exception as e:
            print(f"Error getting subcategories from {url}: {str(e)}")
            return set(), set()
    
    def extract_page_info(self, url: str) -> Dict:
        """Extract relevant information from an animal page."""
        try:
            soup = self.get_page_content(url)
            
            # Get title
            title_elem = soup.find('h1', {'id': 'firstHeading'})
            if not title_elem:
                return None
            title = title_elem.text.strip()
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
                categories = [link.text.strip() for link in catlinks.find_all('a')]
            
            # Check if it's actually an animal-related page
            is_animal_page = any(keyword in cat.lower() for cat in categories 
                               for keyword in ['animal', 'fauna', 'species', 'mammals', 
                                             'birds', 'reptiles', 'amphibians', 'fish', 'insects'])
            if not is_animal_page:
                return None
            
            # Get main content
            main_content = content_div.find('div', {'class': 'mw-parser-output'})
            if not main_content:
                return None
            
            # Remove unwanted elements
            for element in main_content.find_all(['table', 'div', 'script', 'style', 'sup', 'span']):
                try:
                    if element.get('class') and any('infobox' in c for c in element.get('class', [])):
                        continue  # Keep infoboxes
                    element.decompose()
                except Exception:
                    continue
            
            # Get all paragraphs
            paragraphs = main_content.find_all('p', recursive=False)
            main_text = '\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
            
            if not main_text:
                return None
            
            return {
                'title': title,
                'url': url,
                'main_text': main_text,
                'categories': categories,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error extracting content from {url}: {str(e)}")
            return None
    
    def is_valid_article(self, url: str) -> bool:
        """Check if the URL is a valid article (not a special page)."""
        invalid_patterns = ['Category:', 'File:', 'Template:', 'Help:', 'Wikipedia:', 'Portal:', 'Special:']
        return not any(pattern in url for pattern in invalid_patterns)
    
    def scrape_animals(self, start_url: str = "https://en.wikipedia.org/wiki/Category:Animals"):
        """Main method to scrape animal pages."""
        category_queue = {start_url}
        
        print("Starting animal page collection and processing...")
        print(f"Continuing from {len(self.animal_data)} existing entries")
        print("This will take some time. Progress will be shown regularly...")
        
        while category_queue:
            current_url = category_queue.pop()
            
            if current_url in self.visited_categories:
                continue
            
            self.visited_categories.add(current_url)
            self.total_categories_processed += 1
            
            try:
                # Get new categories and pages
                new_subcategories, new_pages = self.get_subcategories_and_pages(current_url)
                category_queue.update(new_subcategories)
                
                # Process pages immediately
                for page_url in new_pages:
                    if page_url not in self.visited_pages:
                        self.visited_pages.add(page_url)
                        self.total_pages_found += 1
                        
                        try:
                            page_info = self.extract_page_info(page_url)
                            if page_info and page_info['main_text']:
                                self.animal_data.append(page_info)
                                self.total_pages_processed += 1
                                print(f"Added animal: {page_info['title']}")
                                
                                # Save progress every 10 successful pages
                                if len(self.animal_data) % 10 == 0:
                                    self.save_data('animal_data_partial.json')
                                    self.save_data('animal_data.json')  # Also save to main file
                                    print(f"\nProgress update:")
                                    print(f"Categories processed: {self.total_categories_processed}")
                                    print(f"Categories remaining: {len(category_queue)}")
                                    print(f"Total pages found: {self.total_pages_found}")
                                    print(f"Pages processed: {self.total_pages_processed}")
                                    print(f"Articles saved: {len(self.animal_data)}")
                        except Exception as e:
                            print(f"Error processing page {page_url}: {str(e)}")
                        
                        time.sleep(1)  # Rate limiting for page processing
                
                # Show progress update for categories
                if self.total_categories_processed % 5 == 0:
                    print(f"\nCategory progress:")
                    print(f"Categories processed: {self.total_categories_processed}")
                    print(f"Categories remaining: {len(category_queue)}")
                    print(f"Current category: {current_url}")
            
            except Exception as e:
                print(f"Error processing category {current_url}: {str(e)}")
            
            time.sleep(1)  # Rate limiting for category processing
    
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
