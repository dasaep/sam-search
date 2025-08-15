"""
Capability matching system for analyzing opportunities
"""

import re
from typing import Dict, List, Any
from database import OpportunityDB
import logging

log = logging.getLogger("capability_matcher")


class CapabilityMatcher:
    def __init__(self, db: OpportunityDB):
        self.db = db
    
    def calculate_match(self, opportunity: Dict[str, Any], capability: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate match percentage between opportunity and capability"""
        
        match_details = {
            'keyword_matches': [],
            'naics_match': False,
            'agency_match': False,
            'value_match': None,
            'set_aside_match': False
        }
        
        score = 0
        max_score = 100
        
        opp_text = f"{opportunity.get('title', '')} {opportunity.get('raw_data', {}).get('description', '')}".lower()
        
        if capability.get('keywords'):
            keyword_weight = 40
            matched_keywords = []
            
            for keyword in capability['keywords']:
                if keyword.lower() in opp_text:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                match_details['keyword_matches'] = matched_keywords
                score += keyword_weight * (len(matched_keywords) / len(capability['keywords']))
        
        if capability.get('naics_codes') and opportunity.get('naics'):
            naics_weight = 30
            if opportunity['naics'] in capability['naics_codes']:
                match_details['naics_match'] = True
                score += naics_weight
        
        if capability.get('preferred_agencies') and opportunity.get('agency'):
            agency_weight = 20
            
            for preferred_agency in capability['preferred_agencies']:
                if preferred_agency.lower() in opportunity['agency'].lower():
                    match_details['agency_match'] = True
                    score += agency_weight
                    break
        
        if capability.get('preferred_set_asides') and opportunity.get('set_aside'):
            set_aside_weight = 10
            if opportunity['set_aside'] in capability['preferred_set_asides']:
                match_details['set_aside_match'] = True
                score += set_aside_weight
        
        match_percentage = min(score, 100)
        
        return {
            'capability_id': str(capability['_id']),
            'capability_name': capability['name'],
            'match_percentage': match_percentage,
            'match_details': match_details
        }
    
    def analyze_opportunity(self, opportunity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze an opportunity against all active capabilities"""
        
        capabilities = self.db.get_capabilities(active_only=True)
        matches = []
        
        for capability in capabilities:
            match = self.calculate_match(opportunity, capability)
            
            if match['match_percentage'] > 0:
                self.db.save_match(
                    str(opportunity['_id']),
                    str(capability['_id']),
                    match['match_percentage'],
                    match['match_details']
                )
                matches.append(match)
        
        matches.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return matches
    
    def batch_analyze(self, opportunity_ids: List[str] = None) -> int:
        """Batch analyze multiple opportunities"""
        
        if opportunity_ids:
            opportunities = [self.db.get_opportunity_by_id(oid) for oid in opportunity_ids]
            opportunities = [o for o in opportunities if o]
        else:
            opportunities = self.db.get_opportunities(limit=1000)
        
        count = 0
        for opportunity in opportunities:
            self.analyze_opportunity(opportunity)
            count += 1
            
            if count % 10 == 0:
                log.info(f"Analyzed {count} opportunities")
        
        log.info(f"Completed analysis of {count} opportunities")
        return count