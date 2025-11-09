from twins_recognition.classifier import classify_pair, THRESHOLDS

def test_classify_pair_boundaries():
    base = [0.0]*128
    # twins
    close = [0.0]*127 + [THRESHOLDS['twins'] - 0.01]
    r = classify_pair(base, close)
    assert r.label == 'twins'
    # siblings
    sib = [0.0]*127 + [ (THRESHOLDS['twins'] + THRESHOLDS['siblings'])/2 ]
    r2 = classify_pair(base, sib)
    assert r2.label == 'siblings'
    # similar
    sim = [0.0]*127 + [ (THRESHOLDS['siblings'] + THRESHOLDS['similar'])/2 ]
    r3 = classify_pair(base, sim)
    assert r3.label == 'similar'
    # different
    diff = [0.0]*127 + [ THRESHOLDS['similar'] + 0.1 ]
    r4 = classify_pair(base, diff)
    assert r4.label == 'different'
