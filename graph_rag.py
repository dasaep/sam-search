"""
GraphRAG implementation using Neo4j for opportunity knowledge graph
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from neo4j import GraphDatabase
import os

log = logging.getLogger("graph_rag")


class OpportunityGraphRAG:
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password"
    ):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self._create_constraints()
    
    def _create_constraints(self):
        """Create indexes and constraints in Neo4j"""
        with self.driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Opportunity) REQUIRE o.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Agency) REQUIRE a.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:NAICS) REQUIRE n.code IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Capability) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (k:Keyword) REQUIRE k.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    log.debug(f"Constraint may already exist: {e}")
    
    def add_opportunity(self, opportunity: Dict[str, Any]):
        """Add opportunity and its relationships to the graph"""
        
        with self.driver.session() as session:
            # Create opportunity node
            session.run("""
                MERGE (o:Opportunity {id: $id})
                SET o.title = $title,
                    o.posted_date = $posted_date,
                    o.due_date = $due_date,
                    o.type = $type,
                    o.set_aside = $set_aside,
                    o.url = $url,
                    o.description = $description
            """, {
                "id": opportunity.get("_id", opportunity.get("url")),
                "title": opportunity.get("title"),
                "posted_date": opportunity.get("posted_date"),
                "due_date": opportunity.get("due_date"),
                "type": opportunity.get("type"),
                "set_aside": opportunity.get("set_aside"),
                "url": opportunity.get("url"),
                "description": opportunity.get("raw_data", {}).get("description", "")[:1000]
            })
            
            # Create agency relationship
            if opportunity.get("agency"):
                session.run("""
                    MERGE (a:Agency {name: $agency})
                    WITH a
                    MATCH (o:Opportunity {id: $opp_id})
                    MERGE (o)-[:POSTED_BY]->(a)
                """, {
                    "agency": opportunity["agency"],
                    "opp_id": opportunity.get("_id", opportunity.get("url"))
                })
            
            # Create NAICS relationship
            if opportunity.get("naics"):
                session.run("""
                    MERGE (n:NAICS {code: $naics})
                    SET n.description = $naics_desc
                    WITH n
                    MATCH (o:Opportunity {id: $opp_id})
                    MERGE (o)-[:CLASSIFIED_AS]->(n)
                """, {
                    "naics": opportunity["naics"],
                    "naics_desc": opportunity.get("naics_desc", ""),
                    "opp_id": opportunity.get("_id", opportunity.get("url"))
                })
            
            # Extract and link keywords from title and description
            self._extract_keywords(
                opportunity.get("_id", opportunity.get("url")),
                opportunity.get("title", "") + " " + 
                opportunity.get("raw_data", {}).get("description", "")
            )
    
    def _extract_keywords(self, opportunity_id: str, text: str):
        """Extract keywords from text and create relationships"""
        
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = []
        
        # Common government contracting keywords
        important_terms = [
            "software", "development", "cloud", "security", "data",
            "analytics", "AI", "machine learning", "automation",
            "integration", "modernization", "support", "services",
            "consulting", "training", "maintenance", "infrastructure"
        ]
        
        text_lower = text.lower()
        for term in important_terms:
            if term in text_lower:
                keywords.append(term)
        
        # Create keyword nodes and relationships
        with self.driver.session() as session:
            for keyword in keywords:
                session.run("""
                    MERGE (k:Keyword {name: $keyword})
                    WITH k
                    MATCH (o:Opportunity {id: $opp_id})
                    MERGE (o)-[:CONTAINS_KEYWORD]->(k)
                """, {
                    "keyword": keyword,
                    "opp_id": opportunity_id
                })
    
    def add_capability_match(
        self,
        opportunity_id: str,
        capability: Dict[str, Any],
        match_score: float
    ):
        """Add capability and match relationship to graph"""
        
        with self.driver.session() as session:
            # Create capability node
            session.run("""
                MERGE (c:Capability {id: $cap_id})
                SET c.name = $name,
                    c.description = $description
            """, {
                "cap_id": capability.get("_id"),
                "name": capability.get("name"),
                "description": capability.get("description", "")
            })
            
            # Create match relationship
            session.run("""
                MATCH (o:Opportunity {id: $opp_id})
                MATCH (c:Capability {id: $cap_id})
                MERGE (o)-[m:MATCHES]->(c)
                SET m.score = $score,
                    m.analyzed_at = $analyzed_at
            """, {
                "opp_id": opportunity_id,
                "cap_id": capability.get("_id"),
                "score": match_score,
                "analyzed_at": datetime.utcnow().isoformat()
            })
    
    def add_document(
        self,
        opportunity_id: str,
        document: Dict[str, Any]
    ):
        """Add document node and relationship"""
        
        with self.driver.session() as session:
            session.run("""
                MERGE (d:Document {id: $doc_id})
                SET d.name = $name,
                    d.type = $type,
                    d.url = $url
                WITH d
                MATCH (o:Opportunity {id: $opp_id})
                MERGE (o)-[:HAS_DOCUMENT]->(d)
            """, {
                "doc_id": document.get("_id"),
                "name": document.get("document_name"),
                "type": document.get("document_type"),
                "url": document.get("document_url"),
                "opp_id": opportunity_id
            })
    
    def find_similar_opportunities(
        self,
        opportunity_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Find similar opportunities based on graph relationships"""
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (o1:Opportunity {id: $opp_id})
                MATCH (o1)-[:CONTAINS_KEYWORD]->(k:Keyword)
                MATCH (o2:Opportunity)-[:CONTAINS_KEYWORD]->(k)
                WHERE o1 <> o2
                WITH o2, COUNT(k) as shared_keywords
                ORDER BY shared_keywords DESC
                LIMIT $limit
                RETURN o2.id as id, o2.title as title, 
                       o2.agency as agency, shared_keywords
            """, {
                "opp_id": opportunity_id,
                "limit": limit
            })
            
            return [dict(record) for record in result]
    
    def get_agency_opportunities(self, agency_name: str) -> List[Dict]:
        """Get all opportunities from a specific agency"""
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Agency {name: $agency})
                MATCH (o:Opportunity)-[:POSTED_BY]->(a)
                RETURN o.id as id, o.title as title, 
                       o.posted_date as posted_date
                ORDER BY o.posted_date DESC
            """, {
                "agency": agency_name
            })
            
            return [dict(record) for record in result]
    
    def get_opportunity_network(self, opportunity_id: str) -> Dict:
        """Get the network of relationships for an opportunity"""
        
        with self.driver.session() as session:
            # Get all relationships
            result = session.run("""
                MATCH (o:Opportunity {id: $opp_id})
                OPTIONAL MATCH (o)-[:POSTED_BY]->(a:Agency)
                OPTIONAL MATCH (o)-[:CLASSIFIED_AS]->(n:NAICS)
                OPTIONAL MATCH (o)-[:CONTAINS_KEYWORD]->(k:Keyword)
                OPTIONAL MATCH (o)-[:MATCHES]->(c:Capability)
                OPTIONAL MATCH (o)-[:HAS_DOCUMENT]->(d:Document)
                RETURN o, a, n, 
                       collect(DISTINCT k.name) as keywords,
                       collect(DISTINCT c.name) as capabilities,
                       collect(DISTINCT d.name) as documents
            """, {
                "opp_id": opportunity_id
            })
            
            record = result.single()
            if record:
                return {
                    "opportunity": dict(record["o"]),
                    "agency": dict(record["a"]) if record["a"] else None,
                    "naics": dict(record["n"]) if record["n"] else None,
                    "keywords": record["keywords"],
                    "capabilities": record["capabilities"],
                    "documents": record["documents"]
                }
            
            return None
    
    def query_graph(self, cypher_query: str, parameters: Dict = None) -> List[Dict]:
        """Execute custom Cypher query"""
        
        with self.driver.session() as session:
            result = session.run(cypher_query, parameters or {})
            return [dict(record) for record in result]
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()