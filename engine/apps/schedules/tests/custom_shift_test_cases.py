from apps.schedules.models import CustomOnCallShift

"""
Simplified shift definition to test that shifts contain the correct users.
This test is only checking the start date of the shift is landing on the correct day.
If you need a test for precise hours that should be a different test so that these cases
can stay easy to define.

Define custom shift test case parameters:
users_per_group - Recurrence groups, generates users for each group based on number, Users are named A-Z
shift_start - Date to start shift
day_mask - Which days are included, None to include all
total_days - Length of shift (end = start + total_days)
frequency - Recurrence frequency
interval - Recurrence interval
expected_result - Dict where each day displays the users that should be scheduled
"""
CUSTOM_SHIFT_TEST_CASES = [
    (
        # Original Test Case
        [1, 1, 1],
        "2024-08-01",
        ["FR"],
        21,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-02": "A",
            "2024-08-09": "B",
            "2024-08-16": "C",
        },
    ),
    (
        # Weekdays Start Monday Daily
        [1, 1, 1, 1, 1],
        "2024-08-05",
        ["MO", "TU", "WE", "TH", "FR"],
        14,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-05": "A",
            "2024-08-06": "B",
            "2024-08-07": "C",
            "2024-08-08": "D",
            "2024-08-09": "E",
            "2024-08-12": "A",
            "2024-08-13": "B",
            "2024-08-14": "C",
            "2024-08-15": "D",
            "2024-08-16": "E",
        },
    ),
    (
        # Weekdays Start Monday Daily Interval 2
        [1, 1, 1, 1],
        "2024-08-05",
        ["MO", "TU", "WE", "TH", "FR"],
        14,
        CustomOnCallShift.FREQUENCY_DAILY,
        2,
        {
            "2024-08-05": "A",
            "2024-08-06": "A",
            "2024-08-07": "B",
            "2024-08-08": "B",
            "2024-08-09": "C",
            "2024-08-12": "C",
            "2024-08-13": "D",
            "2024-08-14": "D",
            "2024-08-15": "A",
            "2024-08-16": "A",
        },
    ),
    (
        # Weekdays Start Monday Weekly
        [1, 1, 1, 1, 1],
        "2024-08-05",
        ["MO", "TU", "WE", "TH", "FR"],
        14,
        CustomOnCallShift.FREQUENCY_WEEKLY,
        1,
        {
            "2024-08-05": "A",
            "2024-08-06": "A",
            "2024-08-07": "A",
            "2024-08-08": "A",
            "2024-08-09": "A",
            "2024-08-12": "B",
            "2024-08-13": "B",
            "2024-08-14": "B",
            "2024-08-15": "B",
            "2024-08-16": "B",
        },
    ),
    (
        # Weekdays Start Monday Monthly
        [1, 1, 1, 1, 1],
        "2024-08-26",
        ["MO", "TU", "WE", "TH", "FR"],
        14,
        CustomOnCallShift.FREQUENCY_MONTHLY,
        1,
        {
            "2024-08-26": "A",
            "2024-08-27": "A",
            "2024-08-28": "A",
            "2024-08-29": "A",
            "2024-08-30": "A",
            "2024-09-02": "B",
            "2024-09-03": "B",
            "2024-09-04": "B",
            "2024-09-05": "B",
            "2024-09-06": "B",
        },
    ),
    (
        # Weekdays Start Thursday Daily
        [1, 1, 1, 1, 1],
        "2024-08-08",
        ["MO", "TU", "WE", "TH", "FR"],
        14,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-08": "A",
            "2024-08-09": "B",
            "2024-08-12": "C",
            "2024-08-13": "D",
            "2024-08-14": "E",
            "2024-08-15": "A",
            "2024-08-16": "B",
            "2024-08-19": "C",
            "2024-08-20": "D",
            "2024-08-21": "E",
        },
    ),
    (
        # Weekdays Start Thursday Weekly
        [1, 1, 1, 1, 1],
        "2024-08-08",
        ["MO", "TU", "WE", "TH", "FR"],
        14,
        CustomOnCallShift.FREQUENCY_WEEKLY,
        1,
        {
            "2024-08-08": "A",
            "2024-08-09": "A",
            "2024-08-12": "B",
            "2024-08-13": "B",
            "2024-08-14": "B",
            "2024-08-15": "B",
            "2024-08-16": "B",
            "2024-08-19": "C",
            "2024-08-20": "C",
            "2024-08-21": "C",
        },
    ),
    (
        # Weekdays Start Thursday Monthly
        [1, 1, 1, 1, 1],
        "2024-08-29",
        ["MO", "TU", "WE", "TH", "FR"],
        14,
        CustomOnCallShift.FREQUENCY_MONTHLY,
        1,
        {
            "2024-08-29": "A",
            "2024-08-30": "A",
            "2024-09-02": "B",
            "2024-09-03": "B",
            "2024-09-04": "B",
            "2024-09-05": "B",
            "2024-09-06": "B",
            "2024-09-09": "B",
            "2024-09-10": "B",
            "2024-09-11": "B",
        },
    ),
    (
        # All Days uneven groups
        [2, 1],
        "2024-08-14",
        None,
        9,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-14": "AB",
            "2024-08-15": "C",
            "2024-08-16": "AB",
            "2024-08-17": "C",
            "2024-08-18": "AB",
            "2024-08-19": "C",
            "2024-08-20": "AB",
            "2024-08-21": "C",
            "2024-08-22": "AB",
        },
    ),
    (
        # Weekends Start Saturday
        [1, 1, 1],
        "2024-08-03",
        ["SA", "SU"],
        15,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-03": "A",
            "2024-08-04": "B",
            "2024-08-10": "C",
            "2024-08-11": "A",
            "2024-08-17": "B",
        },
    ),
    (
        # Weekends Start Saturday Users > Shifts
        [1, 1, 1, 1, 1],
        "2024-08-03",
        ["SA", "SU"],
        14,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-03": "A",
            "2024-08-04": "B",
            "2024-08-10": "C",
            "2024-08-11": "D",
        },
    ),
    (
        # Weekends Start Saturday Users > Shifts
        [1, 1, 1, 1, 1],
        "2024-08-03",
        ["SA", "SU"],
        14,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-03": "A",
            "2024-08-04": "B",
            "2024-08-10": "C",
            "2024-08-11": "D",
        },
    ),
    (
        # Weekends Start Thursday
        [1],
        "2024-08-01",
        ["SA", "SU"],
        5,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-03": "A",
            "2024-08-04": "A",
        },
    ),
    (
        # Weekends Start Thursday
        [1, 1, 1],
        "2024-08-01",
        ["SA", "SU"],
        17,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-03": "A",
            "2024-08-04": "B",
            "2024-08-10": "C",
            "2024-08-11": "A",
            "2024-08-17": "B",
        },
    ),
    (
        # Weekends Start Thursday Users > Shifts
        [1, 1, 1, 1, 1, 1],
        "2024-08-01",
        ["SA", "SU"],
        17,
        CustomOnCallShift.FREQUENCY_DAILY,
        1,
        {
            "2024-08-03": "A",
            "2024-08-04": "B",
            "2024-08-10": "C",
            "2024-08-11": "D",
            "2024-08-17": "E",
        },
    ),
    (
        # Weekends Start Thursday Interval 2
        [1, 1, 1],
        "2024-08-01",
        ["SA", "SU"],
        17,
        CustomOnCallShift.FREQUENCY_DAILY,
        2,
        {
            "2024-08-03": "A",
            "2024-08-04": "A",
            "2024-08-10": "B",
            "2024-08-11": "B",
            "2024-08-17": "C",
        },
    ),
    (
        # Weekends Start Saturday Weekly
        [1, 1, 1],
        "2024-08-01",
        ["SA", "SU"],
        18,
        CustomOnCallShift.FREQUENCY_WEEKLY,
        1,
        {
            "2024-08-03": "A",
            "2024-08-04": "A",
            "2024-08-10": "B",
            "2024-08-11": "B",
            "2024-08-17": "C",
            "2024-08-18": "C",
        },
    ),
    (
        # Weekends Start Saturday Weekly Interval 2
        [1, 1, 1],
        "2024-08-01",
        ["SA", "SU"],
        18,
        CustomOnCallShift.FREQUENCY_WEEKLY,
        2,
        {
            "2024-08-03": "A",
            "2024-08-04": "A",
            "2024-08-17": "B",
            "2024-08-18": "B",
        },
    ),
    (
        # Weekends Start Thursday Monthly
        [1, 1, 1],
        "2024-08-29",
        ["SA", "SU"],
        18,
        CustomOnCallShift.FREQUENCY_MONTHLY,
        1,
        {
            "2024-08-31": "A",
            "2024-09-01": "B",
            "2024-09-07": "B",
            "2024-09-08": "B",
            "2024-09-14": "B",
            "2024-09-15": "B",
        },
    ),
]
