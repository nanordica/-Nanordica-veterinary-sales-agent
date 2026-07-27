"""Pipeline shape for the Ravimus Hackathon pipeline (single source of truth
for the setup script). All deal metadata lives in ONE JSON custom field."""

PIPELINE_NAME = "ravimus-hackathon"

STAGES = [
    "Discovered", "Enriched", "Qualified", "Contacted",
    "Engaged", "Naidis tellitud", "Won", "Lost",
]

# The single deal custom field (Pipedrive `text`) holding all state as JSON.
STATE_FIELD_NAME = "ravimus_hackathon_data"

# Setup creates exactly this one custom field.
CUSTOM_FIELDS = [(STATE_FIELD_NAME, "text")]

# Documented keys carried inside the JSON state (not enforced by Pipedrive).
STATE_KEYS = [
    "registry_id", "email", "clinic", "specialization", "network",
    "decision_style", "score", "ab_variant", "personal_link",
    "discount_code", "sample_claimed_at", "emails_sent",
    "last_contact_at", "lost_reason",
    "valid_until", "practice_scope", "source",
    "sample_reminder_sent", "thanked_at",
    "utm_id", "engaged_at",
]
