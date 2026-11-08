from datetime import datetime, timezone, timedelta

from app.models.lead import LeadRecord, EngagementEvent


def get_seed_scenarios():

    now = datetime.now(timezone.utc)

    hot_lead = LeadRecord(
        lead_id="LEAD-HOT-001",
        source="Website",
        created_at=now - timedelta(days=5),
        last_contact_at=now - timedelta(days=2),
        declared_need="Enterprise software",
        stage="New",
        contact_available=True,
        pending_follow_up=True,
        follow_up_due_at=now - timedelta(days=1),
    )

    hot_events = [
        EngagementEvent(
            event_id="HOT-E1",
            event_type="inquiry",
            occurred_at=now - timedelta(hours=2),
        ),
        EngagementEvent(
            event_id="HOT-E2",
            event_type="meeting_attended",
            occurred_at=now - timedelta(hours=1),
        ),
    ]

    warm_lead = LeadRecord(
        lead_id="LEAD-WARM-001",
        source="Referral",
        created_at=now - timedelta(days=20),
        last_contact_at=now - timedelta(days=15),
        declared_need="CRM implementation",
        stage="Contacted",
        contact_available=True,
    )

    warm_events = [
        EngagementEvent(
            event_id="WARM-E1",
            event_type="inquiry",
            occurred_at=now - timedelta(days=3),
        ),
    ]

    stale_lead = LeadRecord(
        lead_id="LEAD-STALE-001",
        source="Website",
        created_at=now - timedelta(days=90),
        last_contact_at=now - timedelta(days=75),
        declared_need=None,
        stage="New",
        contact_available=True,
    )

    stale_events = []

    return {
        "hot": {
            "description": "Recent inquiry with high fit and overdue follow-up.",
            "lead": hot_lead,
            "engagement_events": hot_events,
        },
        "warm": {
            "description": "Moderate engagement with a valid declared need.",
            "lead": warm_lead,
            "engagement_events": warm_events,
        },
        "stale": {
            "description": "Old lead with no recognized engagement.",
            "lead": stale_lead,
            "engagement_events": stale_events,
        },
    }