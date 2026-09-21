"""
BibTeX parser for academic publications
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import bibtexparser
from bibtexparser import BibtexFormat, Library, write_string
from bibtexparser.middlewares import LatexDecodingMiddleware
from bibtexparser.middlewares.names import (
    parse_single_name_into_parts,
    split_multiple_persons_names,
)
from bibtexparser.model import Entry, Field

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
        self.bib_library = None
        self._latex_decoder = LatexDecodingMiddleware()

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
        
        try:
            self.bib_library = bibtexparser.parse_file(str(file_path))
            if self.bib_library.failed_blocks:
                raise ValueError(
                    f"{len(self.bib_library.failed_blocks)} block(s) "
                    "could not be parsed"
                )
        except Exception as error:
            raise ValueError(f"Could not parse BibTeX file '{file_path}': {error}") from error

        publications = []
        for model_entry in self.bib_library.entries:
            entry = self._entry_to_dict(model_entry)
            try:
                pub = self._format_entry(entry)
            except Exception as error:
                entry_id = entry.get('ID', '<no id>')
                print(f"⚠️  Warning: Skipping BibTeX entry '{entry_id}' in {file_path.name}: {error}")
                continue
            if pub:
                publications.append(pub)

        publications.sort(key=lambda x: x['year'], reverse=True)
        return publications

    @staticmethod
    def _entry_to_dict(entry: Entry) -> Dict[str, Any]:
        return {
            "ENTRYTYPE": entry.entry_type,
            "ID": entry.key,
            **{field.key: field.value for field in entry.fields},
        }

    def _decode_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        model_entry = Entry(
            entry_type=entry.get("ENTRYTYPE", "misc"),
            key=entry.get("ID", "entry"),
            fields=[
                Field(key, value)
                for key, value in entry.items()
                if key not in {"ENTRYTYPE", "ID"}
            ],
        )
        library = self._latex_decoder.transform(Library([model_entry]))
        return self._entry_to_dict(library.entries[0])

    def _decode_latex(self, value: str) -> str:
        entry = Entry("misc", "decode", [Field("value", value)])
        library = self._latex_decoder.transform(Library([entry]))
        return library.entries[0]["value"]

    def parse_directory(self, directory_path: Path, content_type: str = None) -> List[Dict[str, Any]]:
        """Parse all .bib files in a directory."""
        items = []
        if not directory_path.exists():
            return items
        
        for file_path in directory_path.iterdir():
            if not file_path.is_file() or file_path.name.startswith(('_', '.')):
                continue
            if self.can_parse(file_path):
                items.extend(self.parse_file(file_path))

        return items

    def _format_entry(self, entry: dict) -> Optional[Dict[str, Any]]:
        if 'title' not in entry or 'year' not in entry:
            return None

        # Keep the original entry intact for copied BibTeX, while decoding
        # LaTeX escapes in the human-readable title, authors, and venue.
        display_entry = self._decode_entry(entry)

        # Split authors from the RAW field: convert_to_unicode strips the
        # braces that protect corporate names like {Barnes and Noble}.
        # LaTeX escapes are decoded per name after splitting.
        authors = [
            self._decode_latex(name)
            for name in self._parse_authors(entry.get('author', ''))
        ]
        highlighted_authors = self._highlight_authors(authors)
        links = self._extract_links(entry)
        primary_url = next(
            (
                link["url"]
                for link in links
                if link["label"] in {"Paper", "PDF", "arXiv"}
            ),
            "",
        )
        
        return {
            'id': entry.get('ID', ''),
            'title': display_entry.get('title', '').replace('{', '').replace('}', ''),
            # Years like "in press", "2023a", or "2023/2024" must not abort
            # the whole file; extract the first 4-digit year or fall back to 0.
            'year': self._extract_year(entry.get('year', '')),
            'venue': self._get_venue(display_entry),
            'authors': authors,
            'highlighted_authors': highlighted_authors,
            'links': links,
            'primary_url': primary_url,
            'bibtex': self._get_raw_bibtex(entry),
            'highlight': entry.get('highlight', '').lower() in ['true', 'yes', '1'],
            'image': entry.get('image', ''),
            'abstract': display_entry.get('abstract', ''),
            'directions': [
                value.strip()
                for value in display_entry.get('direction', '').split(',')
                if value.strip()
            ],
            'homepage_order': (
                int(entry['homepage_order'])
                if entry.get('homepage_order', '').isdigit()
                else None
            ),
        }

    @staticmethod
    def _extract_year(value: Any) -> int:
        match = re.search(r'\d{4}', str(value))
        return int(match.group()) if match else 0

    def _get_raw_bibtex(self, entry: dict) -> str:
        """Get clean BibTeX string for citation (without website-specific fields)"""
        # Website-specific fields that should be excluded from citations
        website_fields = {
            'pdf', 'code', 'website', 'video', 'slides', 'poster', 'demo', 
            'supplement', 'supplementary', 'image', 'file', 'mendeley-tags',
            'abstract',  # Often too long for citations
            'highlight', 'direction', 'homepage_order', 'project', 'dataset'
        }
        
        citation_entry = Entry(
            entry_type=entry.get("ENTRYTYPE", "misc"),
            key=entry.get("ID", "entry"),
            fields=[
                Field(key, value)
                for key, value in entry.items()
                if key not in {"ENTRYTYPE", "ID"}
                and key.lower() not in website_fields
            ],
        )
        bibtex_format = BibtexFormat()
        bibtex_format.indent = "  "
        return write_string(
            Library([citation_entry]),
            bibtex_format=bibtex_format,
        ).strip()
    
    def _get_venue(self, entry: dict) -> str:
        """Extract venue from entry"""
        entry_type = entry.get('ENTRYTYPE', '').lower()
        
        if entry_type == 'article':
            return entry.get('journal', 'Journal')
        elif entry_type in ['inproceedings', 'conference', 'incollection', 'inbook']:
            venue = entry.get('booktitle', 'Conference')
            return venue.replace('Proceedings of', '').strip()
        else:
            return entry.get('howpublished', 'Publication')
    
    def _format_author_name(self, author: str) -> str:
        """Convert a BibTeX name to first-name-first display order."""
        author = author.strip()
        # A fully-braced name is a corporate author ({Barnes and Noble}):
        # display it verbatim, without the protective braces.
        if author.startswith('{') and author.endswith('}'):
            inner = author[1:-1]
            if inner.count('{') == inner.count('}'):
                return inner.strip()
        try:
            name_parts = parse_single_name_into_parts(author, strict=False)
            return name_parts.merge_first_name_first or author
        except Exception:
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
        return [
            self._format_author_name(author)
            for author in self._split_authors(author_str)
        ]

    @staticmethod
    def _split_authors(author_str: str) -> List[str]:
        """Split a BibTeX author field without breaking braced names."""
        return split_multiple_persons_names(author_str)

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
        if 'project' in entry:
            links.append({'label': 'Project', 'url': entry['project']})
        if 'dataset' in entry:
            links.append({'label': 'Dataset', 'url': entry['dataset']})
        if 'supplement' in entry or 'supplementary' in entry:
            supp_url = entry.get('supplement', entry.get('supplementary'))
            links.append({'label': 'Supplement', 'url': supp_url})
        
        return links