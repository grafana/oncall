def parse_label_query(request):
    """
    parse_label_query returns list of key-value tuples from a request 'label' query param.
    It expects label query param to be key-value pairs separated with ':'.
    """
    labelList = request.query_params.getlist("label", [])
    kvPairs = []
    for label in labelList:
        label_data = label.split(":")
        # Check if label_data is a valid key-value label pair]: ["key1", "value1"]
        if len(label_data) != 2:
            continue
        kvPairs.append(label_data)
    return kvPairs
