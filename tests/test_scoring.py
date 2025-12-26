from app.scoring.engine import compute_turn_score


def test_topic_matching_increases_content():
    comp = {"content": 60}
    stt = {"transcript": "I focused on situation and result, with clear action steps"}
    res = compute_turn_score(comp, stt_metrics=stt, expected_topics=["situation","action","result"])
    assert res["details"]["content"]["score"] >= 70


def test_filler_penalty_hits_delivery():
    comp = {"delivery": 90}
    stt = {"transcript": "um uh like I did", "filler_words": [{"word":"um"},{"word":"uh"},{"word":"like"}], "pause_segments": []}
    res = compute_turn_score(comp, stt_metrics=stt)
    # delivery should be penalized below baseline
    assert res["details"]["delivery"]["score"] < 90


def test_emotion_stress_reduces_confidence():
    comp = {"confidence": 80}
    stt = {"transcript": "I was nervous"}
    emotion_events = [{"label":"stress","score":0.8}]
    res = compute_turn_score(comp, stt_metrics=stt, emotion_events=emotion_events)
    assert res["details"]["confidence"]["score"] < 80
