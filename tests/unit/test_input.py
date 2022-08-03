from pyglet import input


def test_parse_all_controller_mappings():
    # check all the mapping strings to confirm
    # that they can be properly parsed.
    for mapping in input.controller.mapping_list:
        guid = mapping.split(',')[0]
        assert input.controller.get_mapping(guid)
