"""Fictional, realistic demonstration scenarios. Never presented as real evidence."""
from datetime import datetime, timedelta, timezone
import json
from ai_service import generate
from database import connect
from prompts import STATUSES

SCENARIOS = [
    ("Plastic litter collecting beside a stream in Skardu", "Waste & litter", "Skardu, Gilgit-Baltistan",
     "Plastic wrappers, bottles and mixed household litter are collecting on a dry bank beside a small stream near a residential lane. Residents are concerned that the next rise in water level could carry waste downstream. The extent and collection arrangements need an on-site review.",
     "Reported", "Can we first confirm a safe access point and an approved place for collected waste?"),
    ("Cloudy runoff entering a neighbourhood water channel", "Water pollution", "Danyor, Gilgit",
     "A resident observed cloudy runoff entering a roadside water channel after rain. The source and composition are unknown. Photos and observations at consistent times could help qualified water staff decide whether sampling is needed.",
     "Under Review", "Record the time and recent rainfall so observations can be compared."),
    ("Recurring evening smoke near a market collection point", "Air quality", "Rawalpindi, Punjab",
     "Shopkeepers describe recurring evening smoke near a waste collection point. The exact source and pollutant levels have not been established. A safe observation log and a review of collection options could help identify the next step.",
     "Verified", "A collection alternative needs a reliable destination before businesses can commit."),
    ("Litter and foot traffic affecting a lakeside habitat", "Biodiversity", "Kachura, Skardu",
     "A community walk identified discarded packaging and informal footpaths near lakeside vegetation. A local conservation specialist should advise on sensitive areas and suitable low-disturbance access before a stewardship activity is organized.",
     "Action Required", "Please avoid sharing precise nesting locations in public comments."),
    ("Exposed soil washing from a neighbourhood slope", "Land & soil", "Abbottabad, Khyber Pakhtunkhwa",
     "Residents noticed soil reaching a footpath after rainfall below a small exposed slope. Stability, ownership and drainage need checking before planting or earthworks. Repeat photographs from stable ground could establish a baseline.",
     "Under Review", "A drainage assessment should come before choosing plants or barriers."),
    ("Repeat litter survey after a park clean-up", "Waste & litter", "Islamabad, Islamabad Capital Territory",
     "In this demonstration scenario, a community group completed an ordinary litter collection and agreed on a follow-up survey with the site manager. Collected material went to an agreed collection service. Continued observation is needed to check whether litter returns.",
     "Resolved", "A follow-up observation next week will help check whether the improvement lasts."),
]


def seed_demo() -> None:
    """Seed exactly once, atomically, including across concurrent first visits."""
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT 1 FROM metadata WHERE key='demo_seed_v1'").fetchone():
            return
        for index, (title, category, location, description, status, comment) in enumerate(SCENARIOS):
            created = datetime.now(timezone.utc) - timedelta(days=index + 1)
            report = dict(title=title, category=category, location=location, description=description)
            envelope = generate(report, force_demo=True)
            timestamp = created.isoformat(timespec="seconds")
            cursor = conn.execute("""INSERT INTO reports
                (title,description,category,location,status,analysis,is_demo,created_at,updated_at,submission_token)
                VALUES (?,?,?,?,?,?,1,?,?,?)""",
                (title, description, category, location, status, json.dumps(envelope), timestamp,
                 timestamp, f"seed-report-{index}"))
            report_id = cursor.lastrowid
            for step, stage in enumerate(STATUSES[:STATUSES.index(status) + 1]):
                event_time = (created + timedelta(hours=step)).isoformat(timespec="seconds")
                conn.execute("INSERT INTO status_events (report_id,status,actor,note,created_at) VALUES (?,?,?,?,?)",
                             (report_id, stage, "Demo facilitator",
                              "Illustrative community progress only. This fictional scenario is not an independently verified incident.", event_time))
            conn.execute("INSERT INTO comments (report_id,author,body,created_at,submission_token) VALUES (?,?,?,?,?)",
                         (report_id, "Demo participant", comment, timestamp, f"seed-comment-{index}"))
        conn.execute("INSERT INTO metadata VALUES ('demo_seed_v1','complete')")
