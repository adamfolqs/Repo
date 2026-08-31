"""Reply triage and matching."""
import sys, pathlib, json, csv, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from track_replies import classify, normalize_address, load_replies

def test_address():
    assert normalize_address("Jen Lauren <Jen@Example.com>") == "jen@example.com"
    assert normalize_address("plain@x.co") == "plain@x.co"
    assert normalize_address(None) == ""
    print("  address normalisation OK")

def test_classify():
    assert classify("Sure! my whatsapp is +1 555 0100") == "interested"
    assert classify("Me interesa, mi WhatsApp es +52...") == "interested"
    assert classify("Thanks but not interested") == "declined"
    # A decline that also mentions a number must not read as a win.
    assert classify("no thanks, don't have whatsapp") == "declined"
    assert classify("I am out of office until Monday") == "auto-reply"
    assert classify("Address not found") == "bounced"
    assert classify("who is this") == "replied"
    print("  reply triage OK")

def test_attribution_when_the_sender_is_not_the_recipient():
    """All three cases are from the real campaign's first hour."""
    from track_replies import attribute
    roster = {"julie@mightyjoy.com", "collabs@leeleecreates.com",
              "adoseofwellness@nowadaystalent.com", "hello@x.com"}
    # bounce names the dead address in its body
    assert attribute({"from":"mailer-daemon@googlemail.com",
        "snippet":"Your message wasn't delivered to collabs@leeleecreates.com because..."},
        roster) == "collabs@leeleecreates.com"
    # colleague replies from their own address on the same domain
    assert attribute({"from":"philip@mightyjoy.com","snippet":"we don't use whatsapp"},
                     roster) == "julie@mightyjoy.com"
    # agency states who it is answering for
    assert attribute({"from":"kaspar@nowadaystalent.com","snippet":"strong fit",
                      "for":"adoseofwellness@nowadaystalent.com"},
                     roster) == "adoseofwellness@nowadaystalent.com"
    # an unrelated stranger is not attributed to anyone
    assert attribute({"from":"random@elsewhere.com","snippet":"hi"}, roster) == ""
    print("  reply attribution (bounce / colleague / agency) OK")


def test_ambiguous_domain_is_not_guessed():
    """Two recipients at one agency: guessing would credit the wrong creator."""
    from track_replies import attribute
    roster = {"a@agency.com", "b@agency.com"}
    assert attribute({"from":"boss@agency.com","snippet":"interested"}, roster) == ""
    print("  ambiguous same-domain reply left unattributed OK")


def test_absent_reply_does_not_clear_sent():
    d = pathlib.Path(tempfile.mkdtemp())
    roster = d / "campaign_roster.csv"
    fields = ["handle","email","segment","sent_at","reply_status","replied_at",
              "reply_snippet","notes"]
    with roster.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader()
        w.writerow({"handle":"a","email":"a@x.co","segment":"B_generic",
                    "sent_at":"2026-09-01","reply_status":"sent","replied_at":"",
                    "reply_snippet":"","notes":""})
    import track_replies as tr
    tr.ROSTER, tr.REPLIES = roster, d / "replies.json"
    tr.main()
    row = list(csv.DictReader(roster.open()))[0]
    assert row["sent_at"] == "2026-09-01", "send record was erased"
    assert row["reply_status"] == "sent", "status overwritten by a non-reply"
    print("  no-reply leaves the send record intact OK")

if __name__ == "__main__":
    for fn in [test_address, test_classify,
               test_attribution_when_the_sender_is_not_the_recipient,
               test_ambiguous_domain_is_not_guessed,
               test_absent_reply_does_not_clear_sent]:
        print(fn.__name__ + ":"); fn()
    print("\nALL TRACK-REPLY TESTS PASSED")
