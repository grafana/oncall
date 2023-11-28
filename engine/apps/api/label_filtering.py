from typing import List, Tuple


def parse_label_query(label_query: List[str]) -> List[Tuple[str, str]]:
    """
    parse_label_query returns list of key-value tuples from a list of "raw" labels – key-value pairs separated with ':'.
    """
    kv_pairs = []
    for label in label_query:
        label_data = label.split(":")
        # Check if label_data is a valid key-value label pair]: ["key1", "value1"]
        if len(label_data) != 2:
            continue
        kv_pairs.append((label_data[0], label_data[1]))
    return kv_pairs
