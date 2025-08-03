"""CrewAI Documentation Scraper"""

import asyncio
import hashlib
import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import structlog
import httpx
from bs4 import BeautifulSoup

logger = structlog.get_logger()


@dataclass
class ScrapedDocument:
    """Scraped document data"""
    url: str
    title: str
    content: str
    content_hash: str
    metadata: Dict[str, any]
    last_modified: Optional[str] = None
    category: Optional[str] = None
    

@dataclass
class ScrapeResult:
    """Result of scraping operation"""
    documents: List[ScrapedDocument]
    total_processed: int
    new_documents: int
    updated_documents: int
    errors: List[str]
    duration_seconds: float


class CrewAIDocsScraper:
    """Scraper for CrewAI official documentation"""
    
    def __init__(
        self,
        base_url: str = "https://docs.crewai.com",
        timeout_seconds: int = 30,
        max_concurrent: int = 5,
        rate_limit_delay: float = 1.0
    ):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.max_concurrent = max_concurrent
        self.rate_limit_delay = rate_limit_delay
        
        # Track processed URLs
        self._processed_urls: Set[str] = set()
        self._url_hashes: Dict[str, str] = {}  # URL -> content hash
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Statistics
        self._stats = {
            "pages_scraped": 0,
            "bytes_downloaded": 0,
            "errors_count": 0,
            "avg_response_time_ms": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize HTTP client"""
        self._client = httpx.AsyncClient(
            timeout=self.timeout_seconds,
            headers={
                "User-Agent": "Vector-Wave-Knowledge-Base/1.0.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            },
            follow_redirects=True
        )
        
        logger.info(
            "CrewAI docs scraper initialized",
            base_url=self.base_url,
            timeout=self.timeout_seconds
        )
    
    async def scrape_all(self, force_update: bool = False) -> ScrapeResult:
        """Scrape all documentation pages"""
        start_time = time.time()
        
        try:
            logger.info("Starting full documentation scrape", force_update=force_update)
            
            # Discover all documentation URLs
            urls = await self._discover_documentation_urls()
            logger.info(f"Discovered {len(urls)} documentation pages")
            
            # Scrape documents with concurrency control
            documents, errors = await self._scrape_documents(urls, force_update)
            
            # Calculate statistics
            duration = time.time() - start_time
            new_docs = sum(1 for doc in documents if doc.url not in self._processed_urls)
            updated_docs = len(documents) - new_docs
            
            # Update processed URLs
            for doc in documents:
                self._processed_urls.add(doc.url)
                self._url_hashes[doc.url] = doc.content_hash
            
            result = ScrapeResult(
                documents=documents,
                total_processed=len(documents),
                new_documents=new_docs,
                updated_documents=updated_docs,
                errors=errors,
                duration_seconds=duration
            )
            
            logger.info(
                "Documentation scrape completed",
                total_pages=len(documents),
                new_docs=new_docs,
                updated_docs=updated_docs,
                errors_count=len(errors),
                duration_seconds=round(duration, 2)
            )
            
            return result
            
        except Exception as e:
            logger.error("Full scrape failed", error=str(e))
            raise
    
    async def scrape_incremental(self, since_timestamp: Optional[float] = None) -> ScrapeResult:
        """Scrape only changed/new documents since timestamp"""
        start_time = time.time()
        
        try:
            logger.info(
                "Starting incremental documentation scrape",
                since_timestamp=since_timestamp
            )
            
            # For now, we'll do a simple implementation
            # In a production system, this would check last-modified headers
            # or use a sitemap with timestamps
            
            urls = await self._discover_documentation_urls()
            
            # Filter URLs that might have changed
            urls_to_check = []
            for url in urls:
                # Check if we need to update this URL
                if await self._should_update_url(url, since_timestamp):
                    urls_to_check.append(url)
            
            logger.info(f"Found {len(urls_to_check)} potentially updated pages")
            
            if not urls_to_check:
                return ScrapeResult(
                    documents=[],
                    total_processed=0,
                    new_documents=0,
                    updated_documents=0,
                    errors=[],
                    duration_seconds=time.time() - start_time
                )
            
            # Scrape the filtered URLs
            documents, errors = await self._scrape_documents(urls_to_check, force_update=False)
            
            # Filter out documents that haven't actually changed
            changed_documents = []
            for doc in documents:
                old_hash = self._url_hashes.get(doc.url)
                if old_hash != doc.content_hash:
                    changed_documents.append(doc)
                    self._url_hashes[doc.url] = doc.content_hash
            
            duration = time.time() - start_time
            
            result = ScrapeResult(
                documents=changed_documents,
                total_processed=len(urls_to_check),
                new_documents=sum(1 for doc in changed_documents if doc.url not in self._processed_urls),
                updated_documents=sum(1 for doc in changed_documents if doc.url in self._processed_urls),
                errors=errors,
                duration_seconds=duration
            )
            
            # Update processed URLs
            for doc in changed_documents:
                self._processed_urls.add(doc.url)
            
            logger.info(
                "Incremental scrape completed",
                checked_pages=len(urls_to_check),
                changed_docs=len(changed_documents),
                duration_seconds=round(duration, 2)
            )
            
            return result
            
        except Exception as e:
            logger.error("Incremental scrape failed", error=str(e))
            raise
    
    async def _discover_documentation_urls(self) -> List[str]:
        """Discover all documentation URLs"""
        if not self._client:
            raise RuntimeError("Scraper not initialized")
        
        try:
            # Start with the main docs page
            response = await self._client.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all documentation links
            urls = set()
            
            # Look for navigation links
            nav_links = soup.find_all('a', href=True)
            for link in nav_links:
                href = link['href']
                if href.startswith('/'):
                    full_url = urljoin(self.base_url, href)
                elif href.startswith(self.base_url):
                    full_url = href
                else:
                    continue
                
                # Filter for documentation pages
                if self._is_documentation_url(full_url):
                    urls.add(full_url)
            
            # Also try to find sitemap or known documentation sections
            known_sections = [
                '/core-concepts/',
                '/how-to-guides/',
                '/tools/',
                '/llms/',
                '/memory/',
                '/planning/',
                '/flows/',
                '/installation/',
            ]
            
            for section in known_sections:
                section_url = urljoin(self.base_url, section)
                try:
                    section_urls = await self._discover_section_urls(section_url)
                    urls.update(section_urls)
                except Exception as e:
                    logger.warning(f"Failed to discover URLs in section {section}", error=str(e))
            
            return list(urls)
            
        except Exception as e:
            logger.error("Failed to discover documentation URLs", error=str(e))
            raise
    
    async def _discover_section_urls(self, section_url: str) -> List[str]:
        """Discover URLs within a documentation section"""
        if not self._client:
            return []
        
        try:
            response = await self._client.get(section_url)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            urls = set()
            
            # Find all links in this section
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if href.startswith('/'):
                    full_url = urljoin(self.base_url, href)
                elif href.startswith(self.base_url):
                    full_url = href
                else:
                    continue
                
                if self._is_documentation_url(full_url):
                    urls.add(full_url)
            
            return list(urls)
            
        except Exception:
            return []
    
    def _is_documentation_url(self, url: str) -> bool:
        """Check if URL is a documentation page"""
        parsed = urlparse(url)
        
        # Must be from the same domain
        if not url.startswith(self.base_url):
            return False
        
        # Skip non-HTML files
        if parsed.path.endswith(('.pdf', '.zip', '.tar.gz', '.json', '.xml')):
            return False
        
        # Skip fragments and query parameters for now
        if parsed.fragment or parsed.query:
            return False
        
        # Skip certain paths
        skip_paths = ['/api/', '/admin/', '/login/', '/logout/', '/search/']
        if any(skip_path in parsed.path for skip_path in skip_paths):
            return False
        
        return True
    
    async def _should_update_url(self, url: str, since_timestamp: Optional[float]) -> bool:
        """Check if URL should be updated based on timestamp"""
        if not since_timestamp:
            return True
        
        # Simple implementation - in production, check Last-Modified header
        if not self._client:
            return True
        
        try:
            # Send HEAD request to check Last-Modified
            response = await self._client.head(url)
            if response.status_code == 200:
                last_modified = response.headers.get('last-modified')
                if last_modified:
                    # Parse last-modified header and compare with since_timestamp
                    # For now, just return True
                    pass
            
            # Fallback: check if we have a hash for this URL
            return url not in self._url_hashes
            
        except Exception:
            # If we can't check, assume it needs updating
            return True
    
    async def _scrape_documents(self, urls: List[str], force_update: bool) -> Tuple[List[ScrapedDocument], List[str]]:
        """Scrape documents from URLs with concurrency control"""
        documents = []
        errors = []
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def scrape_single_url(url: str) -> Optional[ScrapedDocument]:
            async with semaphore:
                try:
                    # Rate limiting
                    await asyncio.sleep(self.rate_limit_delay)
                    
                    doc = await self._scrape_single_document(url)
                    
                    # Check if document has changed
                    if not force_update and url in self._url_hashes:
                        if self._url_hashes[url] == doc.content_hash:
                            logger.debug(f"Document unchanged: {url}")
                            return None
                    
                    return doc
                    
                except Exception as e:
                    error_msg = f"Failed to scrape {url}: {str(e)}"
                    errors.append(error_msg)
                    logger.error("Document scraping failed", url=url, error=str(e))
                    return None
        
        # Execute scraping tasks
        tasks = [scrape_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif result is not None:
                documents.append(result)
        
        return documents, errors
    
    async def _scrape_single_document(self, url: str) -> ScrapedDocument:
        """Scrape a single document"""
        if not self._client:
            raise RuntimeError("Scraper not initialized")
        
        start_time = time.time()
        
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            
            # Update stats
            response_time_ms = (time.time() - start_time) * 1000
            self._stats["pages_scraped"] += 1
            self._stats["bytes_downloaded"] += len(response.content)
            self._update_avg_response_time(response_time_ms)
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup, url)
            
            # Extract main content
            content = self._extract_content(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup, response)
            
            # Calculate content hash
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            # Determine category
            category = self._determine_category(url, soup)
            
            document = ScrapedDocument(
                url=url,
                title=title,
                content=content,
                content_hash=content_hash,
                metadata=metadata,
                last_modified=response.headers.get('last-modified'),
                category=category
            )
            
            logger.debug(
                "Document scraped",
                url=url,
                title=title[:50],
                content_length=len(content),
                response_time_ms=round(response_time_ms, 2)
            )
            
            return document
            
        except Exception as e:
            self._stats["errors_count"] += 1
            logger.error("Failed to scrape document", url=url, error=str(e))
            raise
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract page title"""
        # Try different title sources
        title_candidates = [
            soup.find('h1'),
            soup.find('title'),
            soup.find('meta', property='og:title'),
            soup.find('meta', name='twitter:title')
        ]
        
        for candidate in title_candidates:
            if candidate:
                if candidate.name == 'meta':
                    title = candidate.get('content', '')
                else:
                    title = candidate.get_text(strip=True)
                
                if title:
                    return title
        
        # Fallback to URL-based title
        return urlparse(url).path.split('/')[-1] or 'Untitled'
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content area
        content_selectors = [
            'main',
            '.documentation-content',
            '.content',
            '.docs-content',
            'article',
            '.post-content'
        ]
        
        content_element = None
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
        
        if not content_element:
            # Fallback to body content
            content_element = soup.find('body')
        
        if content_element:
            # Extract text while preserving some structure
            content = content_element.get_text(separator='\n', strip=True)
            
            # Clean up excessive whitespace
            lines = [line.strip() for line in content.split('\n')]
            lines = [line for line in lines if line]  # Remove empty lines
            
            return '\n'.join(lines)
        
        return ''
    
    def _extract_metadata(self, soup: BeautifulSoup, response: httpx.Response) -> Dict[str, any]:
        """Extract metadata from page"""
        metadata = {
            'source_type': 'web',
            'scraped_at': time.time(),
            'content_type': response.headers.get('content-type', ''),
            'content_length': len(response.content)
        }
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            if name and content:
                metadata[f'meta_{name}'] = content
        
        # Extract Open Graph data
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            prop = tag.get('property', '').replace('og:', '')
            content = tag.get('content')
            if prop and content:
                metadata[f'og_{prop}'] = content
        
        return metadata
    
    def _determine_category(self, url: str, soup: BeautifulSoup) -> str:
        """Determine document category based on URL and content"""
        path = urlparse(url).path.lower()
        
        # Category mapping based on URL path
        category_patterns = {
            'installation': ['install', 'setup', 'getting-started'],
            'core-concepts': ['concepts', 'basics', 'fundamentals'],
            'how-to-guides': ['how-to', 'guides', 'tutorials'],
            'tools': ['tools', 'integrations'],
            'llms': ['llm', 'language-model', 'ai-model'],
            'memory': ['memory', 'persistence'],
            'planning': ['planning', 'strategy'],
            'flows': ['flows', 'workflow'],
            'reference': ['api', 'reference', 'docs']
        }
        
        for category, patterns in category_patterns.items():
            if any(pattern in path for pattern in patterns):
                return category
        
        # Try to determine from page content/structure
        if soup.find(text=lambda text: 'installation' in text.lower() if text else False):
            return 'installation'
        elif soup.find('code') and soup.find('pre'):
            return 'how-to-guides'
        
        return 'general'
    
    def _update_avg_response_time(self, response_time_ms: float) -> None:
        """Update average response time"""
        alpha = 0.1
        if self._stats["avg_response_time_ms"] == 0:
            self._stats["avg_response_time_ms"] = response_time_ms
        else:
            self._stats["avg_response_time_ms"] = (
                alpha * response_time_ms + 
                (1 - alpha) * self._stats["avg_response_time_ms"]
            )
    
    async def get_stats(self) -> Dict[str, any]:
        """Get scraper statistics"""
        return self._stats.copy()
    
    async def close(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("CrewAI docs scraper closed")