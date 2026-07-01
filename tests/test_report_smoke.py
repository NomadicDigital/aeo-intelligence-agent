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
    "raw_html": None,
    "key_improvements": [],
    "visibility_insight": "",
    "quick_win": "",
    "overall_score": 0,
    "high_level_summary": ""
})

print("\n=== REPORT RESULTS ===")
print("Overall Score:", result['overall_score'])
print("High Level Summary:", result['high_level_summary'])
print("Key Improvements:", result['key_improvements'])
print("Visibility Insight:", result['visibility_insight'])
print("Quick Win:", result['quick_win'])