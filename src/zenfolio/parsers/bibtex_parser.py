"""
BibTeX parser for academic publications
"""

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import splitname
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set

from .base_parser import ContentParser


class BibtexParser(ContentParser):
    """BibTeX parser for publications, implementing the ContentParser protocol."""

    def __init__(self, highlight_author: Optional[Union[str, List[str]]] = None):
        if highlight_author is None:
            self.all_highlight_terms = []
        elif isinstance(highlight_author, str):
            self.all_highlight_terms = [highlight_author] if highlight_author else []
        else:
            self.all_highlight_terms = [term for term in highlight_author if term]
        self.bib_database = None

    @property
    def supported_extensions(self) -> Set[str]:
        return {'.bib', '.bibtex'}

    @property
    def content_types(self) -> Set[str]:
        return {'publication'}

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse BibTeX file and return formatted publications"""
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            self.bib_database = bibtexparser.load(f)
        
        publications = []
        for entry in self.bib_database.entries:
            pub = self._format_entry(entry)
            if pub:
                publications.append(pub)
        
        publications.sort(key=lambda x: x['year'], reverse=True)
        return publications

    def parse_directory(self, directory_path: Path, content_type: str = None) -> List[Dict[str, Any]]:
        """Parse all .bib files in a directory."""
        items = []
        if not directory_path.exists():
            return items
        
        for file_path in directory_path.iterdir():
            if self.can_parse(file_path):
                items.extend(self.parse_file(file_path))
        
        return items

    def _format_entry(self, entry: dict) -> Optional[Dict[str, Any]]:
        if 'title' not in entry or 'year' not in entry:
            return None
        
        authors = self._parse_authors(entry.get('author', ''))
        highlighted_authors = self._highlight_authors(authors)
        
        return {
            'title': entry.get('title', '').replace('{', '').replace('}', ''),
            'year': int(entry.get('year', 0)),
            'venue': self._get_venue(entry),
            'authors': authors,
            'highlighted_authors': highlighted_authors,
            'links': self._extract_links(entry),
            'bibtex': self._get_raw_bibtex(entry),
            'highlight': entry.get('highlight', '').lower() in ['true', 'yes', '1']
        }

    def _get_raw_bibtex(self, entry: dict) -> str:
        """Get clean BibTeX string for citation (without website-specific fields)"""
        # Website-specific fields that should be excluded from citations
        website_fields = {
            'pdf', 'code', 'website', 'video', 'slides', 'poster', 'demo', 
            'supplement', 'supplementary', 'image', 'file', 'mendeley-tags',
            'abstract',  # Often too long for citations
            'highlight'  # Website-specific field for homepage display
        }
        
        # Create a filtered entry with only citation-appropriate fields
        clean_entry = {
            key: value for key, value in entry.items() 
            if key not in website_fields
        }
        
        # Create a temporary database with the clean entry
        temp_db = BibDatabase()
        temp_db.entries = [clean_entry]
        
        # Use the library's built-in dumps function
        return bibtexparser.dumps(temp_db).strip()
    
    def _get_venue(self, entry: dict) -> str:
        """Extract venue from entry"""
        entry_type = entry.get('ENTRYTYPE', '').lower()
        
        if entry_type == 'article':
            return entry.get('journal', 'Journal')
        elif entry_type in ['inproceedings', 'conference']:
            venue = entry.get('booktitle', 'Conference')
            return venue.replace('Proceedings of', '').strip()
        else:
            return entry.get('howpublished', 'Publication')
    
    def _format_author_name(self, author: str) -> str:
        """Convert 'LastName, FirstName' to 'FirstName LastName' using bibtexparser's splitname"""
        author = author.strip()
        try:
            # Use bibtexparser's robust name parsing
            name_parts = splitname(author, strict_mode=False)
            
            # Reconstruct as FirstName LastName
            parts = []
            if name_parts.get('first'):
                parts.extend(name_parts['first'])
            if name_parts.get('von'):
                parts.extend(name_parts['von'])
            if name_parts.get('last'):
                parts.extend(name_parts['last'])
            if name_parts.get('jr'):
                parts.extend(name_parts['jr'])
                
            return ' '.join(parts) if parts else author
        except:
            # Fallback to simple splitting if splitname fails
            if ',' in author:
                parts = [part.strip() for part in author.split(',', 1)]
                if len(parts) == 2:
                    last_name, first_name = parts
                    return f"{first_name} {last_name}"
            return author
    
    def _parse_authors(self, author_str: str) -> List[str]:
        """Parse and format authors."""
        if not author_str:
            return []
        return [self._format_author_name(author) for author in author_str.split(' and ')]

    def _highlight_authors(self, authors: List[str]) -> str:
        """Highlight author names based on the configured terms."""
        highlighted_authors = []
        for author in authors:
            should_highlight = any(term and term.lower() in author.lower() for term in self.all_highlight_terms)
            if should_highlight:
                highlighted_authors.append(f'<span class="highlight">{author}</span>')
            else:
                highlighted_authors.append(author)
        return ', '.join(highlighted_authors)
    
    def _extract_links(self, entry: dict) -> List[Dict[str, str]]:
        """Extract links from entry"""
        links = []
        
        # DOI/URL for paper
        if 'doi' in entry:
            links.append({'label': 'Paper', 'url': f"https://doi.org/{entry['doi']}"})
        elif 'url' in entry:
            links.append({'label': 'Paper', 'url': entry['url']})
        
        # PDF link
        if 'pdf' in entry:
            links.append({'label': 'PDF', 'url': entry['pdf']})
        
        # ArXiv
        if 'arxiv' in entry:
            arxiv_id = entry['arxiv']
            if not arxiv_id.startswith('http'):
                arxiv_id = f"https://arxiv.org/abs/{arxiv_id}"
            links.append({'label': 'arXiv', 'url': arxiv_id})
        
        # Code/GitHub
        if 'code' in entry:
            links.append({'label': 'Code', 'url': entry['code']})
        elif 'github' in entry:
            links.append({'label': 'Code', 'url': entry['github']})
        
        # Other links
        if 'website' in entry:
            links.append({'label': 'Website', 'url': entry['website']})
        if 'video' in entry:
            links.append({'label': 'Video', 'url': entry['video']})
        if 'slides' in entry:
            links.append({'label': 'Slides', 'url': entry['slides']})
        if 'poster' in entry:
            links.append({'label': 'Poster', 'url': entry['poster']})
        if 'demo' in entry:
            links.append({'label': 'Demo', 'url': entry['demo']})
        if 'supplement' in entry or 'supplementary' in entry:
            supp_url = entry.get('supplement', entry.get('supplementary'))
            links.append({'label': 'Supplement', 'url': supp_url})
        
        return links