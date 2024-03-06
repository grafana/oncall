class BeneficiaryCannotTakeOwnShiftSwapRequest(Exception):
    """
    Raised when a beneficiary tries to 'take' their own shift swap request
    """


class ShiftSwapRequestNotOpenForTaking(Exception):
    """
    Indicates that the shift swap request is not in a state which allows it to be assigned to a benefactor (aka "taken")
    """
