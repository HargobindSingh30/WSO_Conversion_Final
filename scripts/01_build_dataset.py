"""
01_build_dataset.py

Data Integration Pipeline (Python / Pandas)

Takes five raw source exports and assembles them into one clean, analysis-ready
table: one row per free-tier user, with engineered behavioral and engagement
features and the upgrade label.

Source tables:
    events.csv            Clickstream export, keyed on anonymous visitor ID
    identity_map.csv      Identity resolution: anonymous ID to user ID
    profiles.csv          Volunteered school/year/major (partial coverage)
    email_engagement.csv  Email open and click rates per user
    subscriptions.csv     Billing export: only upgraders appear

Output:
    data/conversion_dataset.csv    One row per resolved user, 25 columns
"""

import pandas as pd
import numpy as np

DATA = "data"

# Load the five source tables
events   = pd.read_csv(f"{DATA}/events.csv", parse_dates=["event_ts"])
idmap    = pd.read_csv(f"{DATA}/identity_map.csv", parse_dates=["identified_date"])
profiles = pd.read_csv(f"{DATA}/profiles.csv")
email    = pd.read_csv(f"{DATA}/email_engagement.csv")
subs     = pd.read_csv(f"{DATA}/subscriptions.csv", parse_dates=["upgrade_date"])

print("Loaded sources:")
print(f"  events            {len(events):>7,} rows")
print(f"  identity_map      {len(idmap):>7,} rows")
print(f"  profiles          {len(profiles):>7,} rows")
print(f"  email_engagement  {len(email):>7,} rows")
print(f"  subscriptions     {len(subs):>7,} rows")
print()


# STAGE 1: Resolve identities
#
# The clickstream is keyed on anon_id (a browser cookie), not user_id (a person).
# We join to the identity map to attach user_id. Anonymous visitors who never
# identified themselves cannot be attributed and are dropped.

resolved_map = idmap[idmap["user_id"].notna()][["anon_id", "user_id"]]
n_total_events = len(events)

events_resolved = events.merge(resolved_map, on="anon_id", how="inner")
n_dropped = n_total_events - len(events_resolved)

print("STAGE 1: Identity resolution")
print(f"  Events before:          {n_total_events:>7,}")
print(f"  Events after resolve:   {len(events_resolved):>7,}")
print(f"  Unattributable dropped: {n_dropped:>7,}  ({n_dropped/n_total_events*100:.1f}% of events)")
print()

known_users = pd.DataFrame({"user_id": resolved_map["user_id"].unique()})
print(f"  Known (resolvable) users: {len(known_users):,}")
print()


# STAGE 2: Aggregate events to one row per user
#
# The event stream is long format (one row per action). We pivot event counts
# into columns and engineer recency, tenure, and depth of engagement features.

# Count each event type per user
event_counts = (
    events_resolved
    .groupby(["user_id", "event_name"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

rename_map = {
    "login": "logins",
    "content_view": "content_views",
    "course_preview": "course_previews",
    "company_search": "target_co_searches",
    "forum_post": "forum_posts",
    "resume_tool_use": "resume_tool_uses",
    "mentor_booking": "mentor_bookings",
    "live_resume_session": "live_resume_sessions",
}
event_counts = event_counts.rename(columns=rename_map)

for col in rename_map.values():
    if col not in event_counts.columns:
        event_counts[col] = 0

# Binary intent flags: did the user ever take this high intent action?
event_counts["mentor_booked"]    = (event_counts["mentor_bookings"] > 0).astype(int)
event_counts["resume_tool_used"] = (event_counts["resume_tool_uses"] > 0).astype(int)
event_counts["live_resume_used"] = (event_counts["live_resume_sessions"] > 0).astype(int)

# Recency and tenure from event timestamps
REF_DATE = events_resolved["event_ts"].max()
ts_stats = (
    events_resolved
    .groupby("user_id")["event_ts"]
    .agg(first_event="min", last_event="max", total_events="count")
    .reset_index()
)
ts_stats["days_since_active"] = (REF_DATE - ts_stats["last_event"]).dt.days
ts_stats["tenure_days"]       = (ts_stats["last_event"] - ts_stats["first_event"]).dt.days

# Depth of engagement: what fraction of a user's activity is high intent?
intent_event_cols  = ["course_previews", "target_co_searches",
                      "resume_tool_uses", "mentor_bookings", "live_resume_sessions"]
event_counts["intent_events"] = event_counts[intent_event_cols].sum(axis=1)

user = (
    known_users
    .merge(event_counts, on="user_id", how="left")
    .merge(ts_stats[["user_id", "days_since_active", "tenure_days", "total_events"]],
           on="user_id", how="left")
)

behavioral_cols = list(rename_map.values()) + ["mentor_booked", "resume_tool_used",
                    "live_resume_used", "intent_events", "total_events"]
user[behavioral_cols] = user[behavioral_cols].fillna(0)
user["days_since_active"] = user["days_since_active"].fillna(user["days_since_active"].max())
user["tenure_days"]       = user["tenure_days"].fillna(0)

user["intent_ratio"] = np.where(user["total_events"] > 0,
                                user["intent_events"] / user["total_events"], 0.0).round(3)

print("STAGE 2: Event aggregation")
print(f"  User level rows: {len(user):,}")
print(f"  Behavioral features built: {len(behavioral_cols)+2}")
print()


# STAGE 3: Join profiles (volunteered school/year/major)
#
# Only ~66% of users volunteered profile data through one of the free offering
# gates. Missing values are filled with "unknown" as an explicit category,
# because the missingness is informative (less engaged users are less likely
# to have volunteered).

user = user.merge(profiles, on="user_id", how="left")

profile_cat_cols = ["profile_source", "school_tier", "class_year", "major_cat"]
for c in profile_cat_cols:
    user[c] = user[c].fillna("unknown")

user["university_name"] = user["university_name"].fillna("(not provided)")
user["major_name"]      = user["major_name"].fillna("(not provided)")
user["has_profile"] = (user["profile_source"] != "unknown").astype(int)

print("STAGE 3: Profile join")
print(f"  Users with profile: {user['has_profile'].sum():,}  "
      f"({user['has_profile'].mean()*100:.1f}%)")
print(f"  Users unknown:      {(user['has_profile']==0).sum():,}")
print()


# STAGE 4: Join email engagement
#
# A small number of users have no email record at all. Missing rates default to 0.

user = user.merge(email, on="user_id", how="left")
user["email_open_rate"]  = user["email_open_rate"].fillna(0.0)
user["email_click_rate"] = user["email_click_rate"].fillna(0.0)
user["has_email_record"] = user["user_id"].isin(email["user_id"]).astype(int)

print("STAGE 4: Email join")
print(f"  Users with email record: {user['has_email_record'].sum():,}")
print()


# STAGE 5: Derive the upgrade label from billing
#
# The billing export only contains rows for users who upgraded. A user is labeled
# as upgraded (1) if they appear in the subscriptions table, otherwise 0.

upgraders = set(subs["user_id"])
user["upgraded"] = user["user_id"].isin(upgraders).astype(int)

print("STAGE 5: Label derivation")
print(f"  Upgraders: {user['upgraded'].sum():,}  ({user['upgraded'].mean()*100:.1f}%)")
print()


# STAGE 6: Clean and finalize

final_cols = [
    "user_id",
    "profile_source", "has_profile", "university_name", "school_tier",
    "class_year", "major_name", "major_cat",
    "mentor_booked", "live_resume_used", "resume_tool_used",
    "course_previews", "target_co_searches",
    "logins", "content_views", "forum_posts",
    "total_events", "intent_events", "intent_ratio",
    "tenure_days", "days_since_active",
    "email_open_rate", "email_click_rate", "has_email_record",
    "upgraded",
]
clean = user[final_cols].copy()

int_cols = ["has_profile","mentor_booked","live_resume_used","resume_tool_used",
            "course_previews","target_co_searches","logins","content_views","forum_posts",
            "total_events","intent_events","tenure_days","days_since_active",
            "has_email_record","upgraded"]
clean[int_cols] = clean[int_cols].astype(int)

assert clean[int_cols].isna().sum().sum() == 0, "unexpected nulls in integer columns"

clean.to_csv(f"{DATA}/conversion_dataset.csv", index=False)

print("=" * 60)
print("CLEAN DATASET WRITTEN: data/conversion_dataset.csv")
print("=" * 60)
print(f"  Rows (users):   {len(clean):,}")
print(f"  Columns:        {clean.shape[1]}")
print(f"  Upgrade rate:   {clean['upgraded'].mean()*100:.1f}%")
print(f"  Positives:      {clean['upgraded'].sum():,}")
