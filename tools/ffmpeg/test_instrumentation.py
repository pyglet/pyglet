import instrumentation as ins

def test_no_unknown_state_fields_in_mp_events():
    all_fields = ins.MediaPlayerStateIterator.fields.keys()
    ok = True
    for evname in ins.mp_events:
        if evname == "version":
            continue
        for name in ins.mp_events[evname]["update_names"]:
            if name not in all_fields:
                print("Error, in evname '%s' unknown field '%s' in 'update_names'" % (evname, name))
                ok = False
        for name in ins.mp_events[evname]["other_fields"]:
            if name not in all_fields:
                print("Error, in evname '%s' unknown field '%s' in 'other_fields'" % (evname, name))
                ok = False
    if ok:
        print("test_no_unknown_state_fields_in_mp_events: passed")

def test_evname_in_mp_events_testcases():
    ok = True
    for evname in ins.mp_events:
        if evname == "version":
            continue
        for i, args in enumerate(ins.mp_events[evname]["test_cases"]):
            if evname != args[0]:
                msg = "Error, for evname %s the testase #%d does not match evname"
                print(msg % (evname, i))
                ok = False
    if ok:
        print("test_evname_in_mp_events_testcases: passed")
    

test_no_unknown_state_fields_in_mp_events()
test_evname_in_mp_events_testcases()
