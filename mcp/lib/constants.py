"""Pipeline shape for the Ravimus Latvia-vets pipeline (single source of truth
for the setup script). Field types are deliberately varchar/text/double — no
enums — to avoid Pipedrive option-ID indirection."""

PIPELINE_NAME = "ravimus-latvia-vets"

# Ordered stage names (order_nr = index + 1).
STAGES = [
    "Discovered",
    "Enriched",
    "Qualified",
    "Contacted",
    "Engaged",
    "Naidis tellitud",
    "Won",
    "Lost",
]

# Deal custom fields: (friendly_name, pipedrive_field_type).
# Allowed-value vocab is documented here but not enforced by Pipedrive.
CUSTOM_FIELDS = [
    ("registry_id", "varchar"),       # registry unique id (dedup)
    ("email", "varchar"),             # registry email
    ("clinic", "text"),               # clinic name/location/type
    ("specialization", "text"),       # animals / specialty
    ("network", "text"),              # links to other registry vets
    ("decision_style", "varchar"),    # facts/results/innovation/peers/welfare/business
    ("score", "double"),              # 0-100 qualification score
    ("ab_variant", "varchar"),        # "A" | "B"
    ("personal_link", "varchar"),     # personal Wix link
    ("discount_code", "varchar"),     # personal coupon code
    ("sample_claimed_at", "varchar"), # ISO-8601 UTC
    ("emails_sent", "double"),        # count, max 5
    ("last_contact_at", "varchar"),   # ISO-8601 UTC
    ("lost_reason", "varchar"),       # opt-out|bounce|said-no|unqualified|no-reply
]
