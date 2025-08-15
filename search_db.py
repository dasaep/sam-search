"""
Modified search script that stores opportunities in MongoDB
"""

import logging
import sys
from datetime import date, datetime, timedelta
import yaml

import client
from client.rest import ApiException
from database import OpportunityDB
from config_db import MONGODB_CONFIG

log = logging.getLogger("search_db")
logging.basicConfig(level=logging.INFO)


def load_config() -> dict:
    with open("config.yaml", "r") as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def search(
    api_client: client.ApiClient,
    api_key: str,
    from_date: str,
    to_date: str,
    limit: int,
    naics: str,
) -> list[dict]:
    """Execute sam.gov search"""
    api_instance = client.SamApi(api_client)

    try:
        api_response = api_instance.search(
            api_key=api_key,
            posted_from=from_date,
            posted_to=to_date,
            limit=limit,
            naics=naics,
        )
        return api_response.to_dict()["value"]
    except ApiException as e:
        log.exception("Exception when calling SamApi->search: %s\n" % e)
        return []


def process_opportunity(raw_opp: dict, config: dict) -> dict:
    """Process raw opportunity data for database storage"""
    
    processed = {
        "title": raw_opp.get("title"),
        "agency": raw_opp.get("agency"),
        "posted_date": raw_opp.get("posted_date"),
        "due_date": raw_opp.get("due_date"),
        "type": raw_opp.get("type"),
        "set_aside": raw_opp.get("set_aside"),
        "naics": raw_opp.get("naics"),
        "url": raw_opp.get("url"),
        "raw_data": raw_opp
    }
    
    if processed["posted_date"]:
        try:
            if "T" in processed["posted_date"]:
                processed["posted_date_parsed"] = datetime.fromisoformat(processed["posted_date"])
            else:
                processed["posted_date_parsed"] = datetime.strptime(processed["posted_date"], "%Y-%m-%d")
        except:
            processed["posted_date_parsed"] = None
    
    if processed["due_date"]:
        try:
            if "T" in processed["due_date"]:
                processed["due_date_parsed"] = datetime.fromisoformat(processed["due_date"])
            else:
                processed["due_date_parsed"] = datetime.strptime(processed["due_date"], "%Y-%m-%d")
        except:
            processed["due_date_parsed"] = None
    
    return processed


def process_search(api_client: client.ApiClient, sam_api_key: str, config: dict, db: OpportunityDB) -> int:
    """Process SAM.gov search and store in database"""
    
    all_opportunities = []
    limit = 1000
    from_days_back = config["from_days_back"]
    from_date = (date.today() - timedelta(days=from_days_back)).strftime("%m/%d/%Y")
    to_date = date.today().strftime("%m/%d/%Y")
    
    log.info(f"Searching from {from_date} to {to_date}")
    
    for naics in config["naics"]:
        log.info(f"Searching NAICS code: {naics['code']} - {naics['desc']}")
        
        naics_results = search(
            api_client, sam_api_key, from_date, to_date, limit, naics["code"]
        )
        
        for result in naics_results:
            processed = process_opportunity(result, config)
            processed["naics_desc"] = naics["desc"]
            all_opportunities.append(processed)
    
    log.info(f"Found {len(all_opportunities)} total opportunities")
    
    if all_opportunities:
        count = db.bulk_upsert_opportunities(all_opportunities)
        log.info(f"Stored/updated {count} opportunities in database")
        return count
    
    return 0


def main(sam_api_key: str, mongo_url: str = None):
    """Main processing function"""
    
    log.info("Starting SAM.gov opportunity search and database storage")
    config = load_config()
    
    # Use provided URL or default to Atlas configuration
    connection_string = mongo_url or MONGODB_CONFIG["connection_string"]
    db_name = MONGODB_CONFIG["database_name"]
    
    log.info(f"Connecting to MongoDB Atlas database: {db_name}")
    db = OpportunityDB(connection_string=connection_string, db_name=db_name)
    
    try:
        api_config = client.Configuration()
        api_config.host = config["sam_url"]
        api_client = client.ApiClient(api_config)
        
        log.info("Processing search...")
        count = process_search(api_client, sam_api_key, config, db)
        
        stats = db.get_statistics()
        log.info(f"Database statistics: {stats}")
        
    finally:
        db.close()
    
    return count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search_db.py <sam_api_key> [mongo_url]")
        sys.exit(1)
    
    sam_key = sys.argv[1]
    mongo_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    main(sam_key, mongo_url)