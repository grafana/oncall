class SendgridEmailMessageStatuses(object):
    """
    https://sendgrid.com/docs/for-developers/tracking-events/event/#delivery-events
    """

    # Delivery events
    ACCEPTED = 10
    PROCESSED = 20
    DEFERRED = 30
    DELIVERED = 40
    DROPPED = 50
    BOUNCE = 60  # "event": "bounce", "type: "bounce"
    BLOCKED = 70  # "event": "bounce", "type: "blocked"

    # Engagement events
    OPEN = 80
    CLICK = 90
    UNSUBSCRIBE = 100
    SPAMREPORT = 110
    # Group Unsubscribe - ?
    # Group Resubscribe - ?

    CHOICES = (
        (ACCEPTED, "accepted"),
        (PROCESSED, "processed"),
        (DEFERRED, "deferred"),
        (DELIVERED, "delivered"),
        (DROPPED, "dropped"),
        (BOUNCE, "bounce"),
        (BLOCKED, "blocked"),
        (OPEN, "open"),
        (CLICK, "click"),
        (UNSUBSCRIBE, "unsubscribe"),
        (SPAMREPORT, "spamreport"),
    )

    DETERMINANT = {
        "accepted": ACCEPTED,
        "processed": PROCESSED,
        "deferred": DEFERRED,
        "delivered": DELIVERED,
        "dropped": DROPPED,
        "bounce": BOUNCE,
        "blocked": BLOCKED,
        "open": OPEN,
        "click": CLICK,
        "unsubscribe": UNSUBSCRIBE,
        "spamreport": SPAMREPORT,
    }
