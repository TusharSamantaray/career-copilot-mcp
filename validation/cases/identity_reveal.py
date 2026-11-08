"""Identity is revealed only after both sides confirm, and only what each
chose to share. One made-up candidate, two made-up recruiters."""
import json

from copilot import facts, intro, journey, persona, recruiter, store

ID = "identity_reveal"
TITLE = "Identity revealed only when both sides confirm"
BACKLOG = "B-055"
BEFORE = ("No introduction step: the only way to meet a persona would be "
          "to learn who they are first.")


def run(user, measure):
    me, hr, other = f"{user}-cand", f"{user}-hr", f"{user}-hr2"
    journey.save_profile(me, {"target_role": "Frontend Engineer"})
    facts.add(me, "Owned React and TypeScript checkout for 3 markets",
              employer="Pinecrest", ownership="owned", confirmed=True,
              apply=True)
    preview = persona.publish(me)
    pid = persona.publish(me, accept=True,
                          preview_id=preview["preview_id"])["persona_id"]
    recruiter.chat(hr, pid, "What have they built in React?")
    sent = intro.request(hr, pid, "Fabrikam", "Frontend Engineer",
                         "Your checkout work fits our team. Open to talk?")
    iid = sent["intro_id"]
    early = intro.reveal(hr, iid, True, "Riley, riley@fabrikam.example")
    measure("revealed after only the recruiter confirmed",
            early["revealed"], False)
    box = json.dumps(intro.inbox(me))
    measure("recruiter's contact visible before both confirm",
            "riley@" in box, False)
    measure("candidate confirming without saying what to share",
            intro.reveal(me, iid, True, "").get("revealed"), False)
    stranger = intro.reveal(other, iid, True, "Mallory")
    measure("a third person can confirm someone else's intro",
            "error" not in stranger, False)
    done = intro.reveal(me, iid, True, "Sam, sam@example.org")
    measure("revealed once both confirm", done["revealed"], True)
    measure("each side gets only what the other chose to share",
            (done["they_shared"],
             intro.reveal(hr, iid, True, "x")["they_shared"]),
            ("Riley, riley@fabrikam.example", "Sam, sam@example.org"))
    note = store.get(me, "persona")["reveals"][0]
    measure("persona notes the reveal came after the merit screen",
            note["after_screen"], True)
    second = intro.request(other, pid, "Contoso", "UI Engineer",
                           "Would you like to talk?")
    intro.reveal(me, second["intro_id"], False)
    late = intro.reveal(other, second["intro_id"], True, "Mallory")
    measure("declined intro can still be revealed", late["revealed"], False)
