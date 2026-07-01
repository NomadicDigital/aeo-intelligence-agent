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
    "pdf_path": "",
    "raw_html": None,
    "key_improvements": [],
    "visibility_insight": "",
    "quick_win": "",
    "overall_score": 0,
    "high_level_summary": ""
})

print("\n=== TECHNICAL AUDIT RESULTS ===")
print("robots_txt:", result['robots_txt'])
print("llms_txt:", result['llms_txt'])
print("llms_full_txt:", result['llms_full_txt'])
print("schema:", result['schema'])
print("errors:", result['errors'])