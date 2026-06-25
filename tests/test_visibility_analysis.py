import sys
sys.path.insert(0, 'src/aeo_agent')

from graph import app

result = app.invoke({
    "input_url": "https://www.fallowfieldscamping.com",
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
    "pdf_path": "",
    "raw_html": None
})

print("\n=== VISIBILITY RESULTS ===")
print("Prospect visibility:", result['prospect_visibility'])
print("Competitor visibility:", result['competitor_visibility'])