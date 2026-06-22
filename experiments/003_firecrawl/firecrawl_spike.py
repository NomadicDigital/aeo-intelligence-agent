import os
from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv()

api_key = os.getenv("FIRECRAWL_API_KEY")
app = Firecrawl(api_key=api_key)

data = app.scrape('firecrawl.dev')

print(data)
