# Data Dictionary: conversion_dataset.csv

One row per free tier user. 1,708 rows, 25 columns.

Built by `scripts/01_build_dataset.py`, which integrates five raw source exports
(clickstream, identity map, profiles, email engagement, billing) into this single
user level table.

Target variable: `upgraded` (13.9% positive).


## How this table was built

| Source export | System it mirrors | What it contributed |
|---|---|---|
| events.csv | Clickstream (Mixpanel / GA4) | Behavioral counts, recency, tenure |
| identity_map.csv | CDP (Segment) | Resolved anonymous browsers to user_id |
| profiles.csv | App database | School / year / major (volunteered) |
| email_engagement.csv | Email platform | Open and click rates |
| subscriptions.csv | Billing (Stripe) | The upgraded label |

Users whose anonymous activity never resolved to a known identity were dropped.
Missing profile data is retained as its own "unknown" category rather than imputed,
because the missingness is informative.


## Identity

| Column | Type | Description |
|---|---|---|
| user_id | string (1,708 unique) | Unique user identifier |


## Profile / Fit

| Column | Type | Description |
|---|---|---|
| profile_source | string (6 values) | Gate through which the student volunteered profile data: resume_template_form, info_session_registration, resume_workshop_registration, email_capture, self_completed_profile, or unknown |
| has_profile | int (0/1) | 1 if profile data exists, 0 if unknown |
| university_name | string (19 distinct) | Literal school name. Display only, not modeled. "(not provided)" if missing |
| school_tier | string | target, semi_target, non_target, or unknown. Modeled version of school |
| class_year | string | freshman, sophomore, junior, senior, or unknown |
| major_name | string (12 distinct) | Literal major. Display only, not modeled. "(not provided)" if missing |
| major_cat | string | finance_econ, stem, other, or unknown. Modeled version of major |


## High Intent Actions

| Column | Type | Description |
|---|---|---|
| mentor_booked | int (0/1) | Ever booked a mentor session. Strongest single predictor |
| live_resume_used | int (0/1) | Ever attended a live resume review session |
| resume_tool_used | int (0/1) | Ever used the resume tool |
| course_previews | int (0 to 12) | Number of paid course previews viewed |
| target_co_searches | int (0 to 14) | Number of searches for target firms (Goldman, JPMorgan, etc.) |


## Ambient Activity

| Column | Type | Description |
|---|---|---|
| logins | int (1 to 27) | Login count. Barely separates converters from non converters |
| content_views | int (1 to 44) | Content / article views |
| forum_posts | int (0 to 8) | Community forum posts |


## Engineered Features

| Column | Type | Description |
|---|---|---|
| total_events | int | All tracked actions summed |
| intent_events | int | High intent actions only (mentor + course + resume tool + company search + live session) |
| intent_ratio | float (0.0 to 0.88) | intent_events / total_events. Captures quality of engagement, not quantity |


## Recency / Tenure

| Column | Type | Description |
|---|---|---|
| tenure_days | int (1 to 209) | Days between first and last recorded event |
| days_since_active | int (0 to 164) | Days from last event to reference date. Lower = more recent |


## Email Engagement

| Column | Type | Description |
|---|---|---|
| email_open_rate | float (0.0 to 0.99) | Fraction of emails opened |
| email_click_rate | float (0.0 to 0.53) | Fraction of emails clicked |
| has_email_record | int (0/1) | 1 if user exists in the email platform |


## Label

| Column | Type | Description |
|---|---|---|
| upgraded | int (0/1) | 1 if the user upgraded to paid Academy, else 0. 13.9% positive |
