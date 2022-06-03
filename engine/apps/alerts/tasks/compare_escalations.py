def compare_escalations(request_id, active_escalation_id):
    if request_id == active_escalation_id:
        return True
    return False
