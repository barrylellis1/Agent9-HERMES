"""
Business Glossary Provider

This provider manages business glossary terms, synonyms, and mappings to technical attributes.
It's part of the Unified Registry Access Layer and is used for term resolution,
synonym matching, and business-to-technical mapping.
"""

import os
import logging
from typing import Dict, List, Optional, Set, Any, Union

import yaml

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class BusinessTerm(BaseModel):
    """Model for a business glossary term with synonyms and technical mappings."""
    id: Optional[str] = Field(None, description="Unique identifier (used as DB primary key)")
    client_id: str = Field("default", description="Client/tenant scope ('default' = shared across all clients)")
    name: str = Field(..., description="Primary canonical name of the business term")
    synonyms: List[str] = Field(default_factory=list, description="Alternative terms/synonyms")
    description: Optional[str] = Field(None, description="Description of the business term")
    technical_mappings: Dict[str, str] = Field(
        default_factory=dict, 
        description="Mapping to technical attributes {system: technical_attribute}"
    )

class BusinessGlossaryProvider:
    """
    Provider for business glossary terms, synonyms, and technical mappings.
    Used for business-to-technical term translation and synonym matching.
    """
    
    def __init__(self, glossary_path: Optional[str] = None, *, auto_load: bool = True):
        """
        Initialize the Business Glossary Provider.
        
        Args:
            glossary_path: Path to the YAML glossary file (optional)
        """
        self.terms: Dict[str, BusinessTerm] = {}
        self.synonym_map: Dict[str, str] = {}  # Maps synonyms to canonical term names
        
        # Default path if none provided
        if glossary_path is None:
            glossary_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "business_glossary.yaml"
            )
        
        self.glossary_path = glossary_path
        if auto_load:
            self._load_glossary()

    def _load_glossary(self) -> None:
        """Load the business glossary from YAML file."""
        try:
            if os.path.exists(self.glossary_path):
                with open(self.glossary_path, 'r') as f:
                    glossary_data = yaml.safe_load(f)
                
                if not glossary_data:
                    logger.warning(f"Empty glossary file: {self.glossary_path}")
                    return
                
                # Process terms
                for term_data in glossary_data.get("terms", []):
                    try:
                        term = BusinessTerm(**term_data)
                        self.terms[term.name.lower()] = term
                        
                        # Add to synonym map
                        for synonym in term.synonyms:
                            self.synonym_map[synonym.lower()] = term.name.lower()
                    except Exception as e:
                        logger.error(f"Error loading term {term_data.get('name')}: {e}")
                
                logger.info(f"Loaded {len(self.terms)} business terms from glossary")
            else:
                logger.warning(f"Business glossary file not found: {self.glossary_path}")
                # Create a default empty glossary
                self._create_default_glossary()
        except Exception as e:
            logger.error(f"Error loading business glossary: {e}")
            # Create a default empty glossary
            self._create_default_glossary()
            
    async def load(self) -> Dict[str, Any]:
        """
        Async load method to comply with RegistryProvider interface.
        
        Returns:
            Dictionary with status information
        """
        try:
            self._load_glossary()
            return {
                "success": True,
                "message": f"Business glossary loaded successfully with {len(self.terms)} terms",
                "count": len(self.terms)
            }
        except Exception as e:
            logger.error(f"Error loading business glossary: {str(e)}")
            return {
                "success": False,
                "message": f"Error loading business glossary: {str(e)}",
                "error": str(e)
            }
    
    def _create_default_glossary(self) -> None:
        """Create a default empty glossary file if none exists."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.glossary_path), exist_ok=True)
            
            # Create a default glossary with sample terms
            default_glossary = {
                "terms": [
                    {
                        "name": "Revenue",
                        "synonyms": ["sales", "income", "turnover"],
                        "description": "Total income generated from sales",
                        "technical_mappings": {
                            "sap": "REVENUE",
                            "duckdb": "revenue"
                        }
                    },
                    {
                        "name": "Profit Margin",
                        "synonyms": ["margin", "profit percentage"],
                        "description": "Percentage of profit relative to revenue",
                        "technical_mappings": {
                            "sap": "PROFIT_MARGIN",
                            "duckdb": "profit_margin"
                        }
                    }
                ]
            }
            
            with open(self.glossary_path, 'w') as f:
                yaml.dump(default_glossary, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Created default business glossary at {self.glossary_path}")
        except Exception as e:
            logger.error(f"Error creating default business glossary: {e}")
    
    def get_all(self) -> List[BusinessTerm]:
        """
        Get all business terms.
        
        Returns:
            List of all business terms
        """
        return list(self.terms.values())
        
    def get(self, id_or_name: str) -> Optional[BusinessTerm]:
        """
        Get a business term by ID or name.
        
        Args:
            id_or_name: The ID or name of the business term to retrieve
            
        Returns:
            The business term if found, None otherwise
        """
        return self.get_term(id_or_name)
        
    def find_by_attribute(self, attr_name: str, attr_value: Any) -> List[BusinessTerm]:
        """
        Find business terms by a specific attribute value.
        
        Args:
            attr_name: The name of the attribute to search by
            attr_value: The value to search for
            
        Returns:
            List of matching business terms
        """
        results = []
        for term in self.terms.values():
            if hasattr(term, attr_name) and getattr(term, attr_name) == attr_value:
                results.append(term)
        return results
        
    def register(self, item: BusinessTerm) -> bool:
        """
        Register a new business term in the registry.
        
        Args:
            item: The business term to register
            
        Returns:
            True if registration succeeded, False otherwise
        """
        return self.add_term(item)
    
    def get_term(self, term_name: str) -> Optional[BusinessTerm]:
        """
        Get a business term by name or synonym.
        
        Args:
            term_name: Name or synonym of the term to get
            
        Returns:
            BusinessTerm if found, None otherwise
        """
        term_key = term_name.lower()
        
        # Direct lookup
        if term_key in self.terms:
            return self.terms[term_key]
        
        # Synonym lookup
        if term_key in self.synonym_map:
            canonical_term = self.synonym_map[term_key]
            return self.terms.get(canonical_term)
        
        return None
    
    def get_technical_mapping(self, term_name: str, system: str = "duckdb") -> Optional[str]:
        """
        Get the technical mapping for a business term.
        
        Args:
            term_name: Name or synonym of the business term
            system: System context for mapping (default: "duckdb")
            
        Returns:
            Technical attribute name if found, None otherwise
        """
        term = self.get_term(term_name)
        if not term:
            return None
        
        return term.technical_mappings.get(system.lower())
    
    def translate_business_terms(
        self, terms: List[str], system: str = "duckdb"
    ) -> Dict[str, Dict[str, Union[str, None]]]:
        """
        Translate a list of business terms to technical attribute names.
        
        Args:
            terms: List of business terms to translate
            system: System context for mapping (default: "duckdb")
            
        Returns:
            Dictionary of results with resolution status for each term
        """
        results = {}
        
        for term in terms:
            term_key = term.lower()
            technical_name = self.get_technical_mapping(term_key, system)
            
            results[term] = {
                "resolved": technical_name is not None,
                "technical_name": technical_name,
                "canonical_term": None
            }
            
            # Add canonical term info if found via synonym
            if term_key in self.synonym_map:
                canonical_term = self.synonym_map[term_key]
                results[term]["canonical_term"] = canonical_term
            elif term_key in self.terms:
                results[term]["canonical_term"] = term_key
        
        return results
    
    def add_term(self, term: BusinessTerm) -> bool:
        """
        Add a business term to the glossary.
        
        Args:
            term: BusinessTerm to add
            
        Returns:
            True if term was added, False otherwise
        """
        try:
            term_key = term.name.lower()
            self.terms[term_key] = term
            
            # Update synonym map
            for synonym in term.synonyms:
                self.synonym_map[synonym.lower()] = term_key
            
            # Save to file
            self._save_glossary()
            return True
        except Exception as e:
            logger.error(f"Error adding business term {term.name}: {e}")
            return False
    
    def upsert_term(self, term: BusinessTerm) -> bool:
        """
        Upsert a business term in the glossary.
        
        Args:
            term: BusinessTerm to upsert
            
        Returns:
            True if term was upserted, False otherwise
        """
        try:
            term_key = term.name.lower()
            existing_term = self.terms.get(term_key)
            if existing_term:
                # Update existing term
                existing_term.update(term)
                self.terms[term_key] = existing_term
            else:
                # Add new term
                self.terms[term_key] = term
                
                # Update synonym map
                for synonym in term.synonyms:
                    self.synonym_map[synonym.lower()] = term_key
            
            # Save to file
            self._save_glossary()
            return True
        except Exception as e:
            logger.error(f"Error upserting business term {term.name}: {e}")
            return False
    
    def delete_term(self, term_name: str) -> bool:
        """
        Delete a business term from the glossary.
        
        Args:
            term_name: Name of the business term to delete
            
        Returns:
            True if term was deleted, False otherwise
        """
        try:
            term_key = term_name.lower()
            if term_key in self.terms:
                del self.terms[term_key]
                
                # Remove from synonym map
                for synonym, canonical_term in list(self.synonym_map.items()):
                    if canonical_term == term_key:
                        del self.synonym_map[synonym]
            
            # Save to file
            self._save_glossary()
            return True
        except Exception as e:
            logger.error(f"Error deleting business term {term_name}: {e}")
            return False
    
    def _save_glossary(self) -> bool:
        """
        Save the business glossary to the YAML file.
        
        Returns:
            True if glossary was saved, False otherwise
        """
        try:
            glossary_data = {
                "terms": [term.model_dump() for term in self.terms.values()]
            }
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.glossary_path), exist_ok=True)
            
            with open(self.glossary_path, 'w') as f:
                yaml.dump(glossary_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved business glossary with {len(self.terms)} terms")
            return True
        except Exception as e:
            logger.error(f"Error saving business glossary: {e}")
            return False


def create_business_glossary_provider(config: Dict[str, Any] = None) -> BusinessGlossaryProvider:
    """
    Factory function to create a Business Glossary Provider.
    
    Args:
        config: Configuration dictionary with options:
            - glossary_path: Path to the YAML glossary file (optional)
        
    Returns:
        BusinessGlossaryProvider instance
    """
    if not config:
        config = {}
    
    glossary_path = config.get("glossary_path")
    return BusinessGlossaryProvider(glossary_path=glossary_path)


