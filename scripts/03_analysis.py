"""
03_analysis.py

Runs analytical SQL queries against the clean user table to answer
"who converts and why?" Results are printed and saved to JSON for
the dashboard.

Analyses:
    A. Overall conversion rate and class balance
    B. Conversion by acquisition channel (profile_source)
    C. Conversion by fit segments (school tier, class year, major)
    D. Intent action lift (mentor booking, resume tool, live session)
    E. Converter vs non converter behavioral profile
    F. Intent vs ambient activity contrast
"""

import sqlite3
import pandas as pd
import json

DB = "outputs/wso_conversion.db"
conn = sqlite3.connect(DB)

def q(sql):
    return pd.read_sql_query(sql, conn)

results = {}


# A. Overall conversion rate

overall = q("""
    SELECT COUNT(*) AS users,
           SUM(upgraded) AS upgraders,
           ROUND(100.0*AVG(upgraded),1) AS conversion_pct
    FROM users;
""")
results["overall"] = overall.to_dict("records")[0]
print("A. OVERALL")
print(overall.to_string(index=False))
print()


# B. Conversion by acquisition channel

channel = q("""
    SELECT profile_source,
           COUNT(*) AS users,
           SUM(upgraded) AS upgraders,
           ROUND(100.0*AVG(upgraded),1) AS conversion_pct
    FROM users
    GROUP BY profile_source
    ORDER BY conversion_pct DESC;
""")
results["by_channel"] = channel.to_dict("records")
print("B. CONVERSION BY ACQUISITION CHANNEL")
print(channel.to_string(index=False))
print()


# C. Conversion by fit segments

tier = q("""
    SELECT school_tier, COUNT(*) AS users, SUM(upgraded) AS upgraders,
           ROUND(100.0*AVG(upgraded),1) AS conversion_pct
    FROM users GROUP BY school_tier ORDER BY conversion_pct DESC;
""")
year = q("""
    SELECT class_year, COUNT(*) AS users, SUM(upgraded) AS upgraders,
           ROUND(100.0*AVG(upgraded),1) AS conversion_pct
    FROM users GROUP BY class_year ORDER BY conversion_pct DESC;
""")
major = q("""
    SELECT major_cat, COUNT(*) AS users, SUM(upgraded) AS upgraders,
           ROUND(100.0*AVG(upgraded),1) AS conversion_pct
    FROM users GROUP BY major_cat ORDER BY conversion_pct DESC;
""")
results["by_school_tier"] = tier.to_dict("records")
results["by_class_year"]  = year.to_dict("records")
results["by_major_cat"]   = major.to_dict("records")
print("C. FIT SEGMENTS")
print(tier.to_string(index=False))
print()
print(year.to_string(index=False))
print()
print(major.to_string(index=False))
print()


# D. Intent action lift

intent_actions = {}
for col in ["mentor_booked", "live_resume_used", "resume_tool_used"]:
    r = q(f"""
        SELECT {col} AS flag, COUNT(*) AS users, SUM(upgraded) AS upgraders,
               ROUND(100.0*AVG(upgraded),1) AS conversion_pct
        FROM users GROUP BY {col} ORDER BY {col} DESC;
    """)
    yes = float(r[r.flag==1]["conversion_pct"].iloc[0])
    no  = float(r[r.flag==0]["conversion_pct"].iloc[0])
    intent_actions[col] = {"yes_pct": yes, "no_pct": no, "lift_x": round(yes/no,1)}
    print(f"D. {col}: yes={yes}%  no={no}%  lift={round(yes/no,1)}x")
results["intent_actions"] = intent_actions
print()


# E. Converter vs non converter behavioral profile

profile = q("""
    SELECT upgraded,
           ROUND(AVG(course_previews),2)    AS avg_course_previews,
           ROUND(AVG(target_co_searches),2) AS avg_target_co_searches,
           ROUND(AVG(intent_ratio),3)       AS avg_intent_ratio,
           ROUND(AVG(logins),2)             AS avg_logins,
           ROUND(AVG(content_views),2)      AS avg_content_views,
           ROUND(AVG(forum_posts),2)        AS avg_forum_posts,
           ROUND(AVG(email_open_rate),3)    AS avg_email_open_rate,
           ROUND(AVG(days_since_active),1)  AS avg_days_since_active
    FROM users GROUP BY upgraded ORDER BY upgraded;
""")
results["converter_profile"] = profile.to_dict("records")
print("E. CONVERTER (1) vs NON CONVERTER (0) PROFILE")
print(profile.to_string(index=False))
print()


# F. Intent vs ambient contrast
# Ratio of converter mean to non converter mean. Higher = stronger separation.

contrast = q("""
    SELECT
      ROUND( (SELECT AVG(course_previews) FROM users WHERE upgraded=1) /
             (SELECT AVG(course_previews) FROM users WHERE upgraded=0), 2) AS course_preview_ratio,
      ROUND( (SELECT AVG(intent_ratio) FROM users WHERE upgraded=1) /
             (SELECT AVG(intent_ratio) FROM users WHERE upgraded=0), 2) AS intent_ratio_ratio,
      ROUND( (SELECT AVG(logins) FROM users WHERE upgraded=1) /
             (SELECT AVG(logins) FROM users WHERE upgraded=0), 2) AS login_ratio,
      ROUND( (SELECT AVG(content_views) FROM users WHERE upgraded=1) /
             (SELECT AVG(content_views) FROM users WHERE upgraded=0), 2) AS content_view_ratio;
""")
results["intent_vs_ambient"] = contrast.to_dict("records")[0]
print("F. INTENT vs AMBIENT (converter/non converter mean ratio)")
print(contrast.to_string(index=False))
print()

conn.close()

with open("outputs/analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved: outputs/analysis_results.json")
