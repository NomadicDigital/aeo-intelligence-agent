import sys
sys.path.insert(0, 'src/aeo_agent')

from graph import app

result = app.invoke({
    "input_url": "https://www.bbc.co.uk",
    "email": "",
    "errors": [],
    "business_name": "",
    "description": "",
    "competitors": [],
    "core_queries": [],
    "llms_txt": {},
    "llms_full_txt": {},
    "robots_txt": {},
    "schema": {},
    "prospect_visibility": {},
    "competitor_visibility": {},
    "overall_score": 0,
    "high_level_summary": "",
})

print("Business:", result['business_name'])
print("Description:", result['description'])
print("Competitors:", result['competitors'])
print("Queries:", result['core_queries'])
print("Errors:", result['errors'])