import os, json
try:
    from google import genai
    from google.genai import types
except Exception:
    genai=None; types=None
MODEL=os.getenv('GEMINI_MODEL','gemini-2.5-flash')
def _client():
    key=os.getenv('GEMINI_API_KEY')
    return genai.Client(api_key=key) if key and genai else None
def _json(text):
    t=text.strip(); s=t.find('{'); e=t.rfind('}'); return json.loads(t[s:e+1]) if s>=0 and e>=0 else json.loads(t)
def analyze_environmental_report(title,category,location,description,image_bytes=None,mime_type=None):
    c=_client()
    if not c:return {'category':category,'summary':f'{title}: {description[:220]}','priority':'Medium','possible_causes':['Needs local verification','Insufficient contextual evidence'],'next_actions':['Verify the report and location','Document additional evidence','Refer to an appropriate local organization']}
    prompt=f'''You are GRIP, an environmental reporting assistant. Analyze conservatively and return ONLY JSON: {"category":"Water|Waste|Air|Climate|Biodiversity|Other","summary":"one concise sentence","priority":"Low|Medium|High","possible_causes":["...","..."],"next_actions":["...","...","..."]}. Never claim official verification. Title:{title}\nCategory:{category}\nLocation:{location}\nDescription:{description}'''
    content=[prompt]
    if image_bytes and mime_type and types: content.append(types.Part.from_bytes(data=image_bytes,mime_type=mime_type))
    try:return _json(c.models.generate_content(model=MODEL,contents=content).text)
    except Exception:return {'category':category,'summary':'AI analysis unavailable; report remains available for review.','priority':'Medium','possible_causes':['Requires human verification'],'next_actions':['Verify the evidence','Review the location','Refer as appropriate']}
def generate_green_innovation(report):
    c=_client()
    if not c:return {'problem':report['description'],'solution':'Create a small community-based service around prevention, monitoring, collection, or awareness for this issue.','implementation':'Pilot in one location, define the service, test with a small group, collect feedback, and measure results.','environmental_benefit':'Potential reduction in local pollution, subject to validation.','business_model':'Offer the service to schools, local organizations, tourism businesses, or community groups for a fee.','pilot':'Run a small 2–4 week pilot with before/after measurements.'}
    prompt=f'''You are GRIP's Green Innovation Lab. Return ONLY JSON with keys problem,solution,implementation,environmental_benefit,business_model,pilot. Create a realistic Pakistan-relevant green solution and possible business opportunity from this problem. Problem:{report["description"]}; Category:{report["category"]}; Location:{report["location"]}'''
    try:return _json(c.models.generate_content(model=MODEL,contents=prompt).text)
    except Exception:return {'problem':report['description'],'solution':'Generate a practical local solution after human validation.','implementation':'Pilot on one site and measure results.','environmental_benefit':'Potential environmental improvement after validation.','business_model':'Offer the service to organizations that benefit from the solution.','pilot':'Run a small, measurable pilot.'}
