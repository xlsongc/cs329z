"""Problem 1: classufiy the eamil as urgent / normal / ignore"""

from __future__ import annotations

from datetime import datetime
import json
import logging

from cs329z_hw1.types import Email, LMCallable

log = logging.getLogger(__name__)

VALID_PRIORITY = {"urgent", "normal", "ignore"}
UNKNOWN = {"category": "unknown", "reason": "Could not parse the model's reply."}

SYSTEM_PROMPT = """You are a professional working assistant that can help
specify the how urgent is each email to the user, based on the title, date,
and the actual content in the email. Judge every email from the point of view
of the person it is addressed to (the 'to' field), at the time it was sent. The
question is what that person should do with the message, not how important
the topic is to the company. 

The detailed information about the rules to decide the priority of the email:
## urgent

The recipient has to act or decide soon. Two things must both be true:

1. The email asks the recipient to do something, or reports a live problem
   that the recipient is responsible for (an outage, a failed payment, a
   customer or manager escalating an issue).
2. There is time pressure: the email states or clearly implies that the
   action is needed the same day, the next working day, or by a stated
   deadline no more than two working days away.
   A working day is Monday to Friday, counted from the email's date.

Examples:

- "The bank rejected this morning's wire. I need you to approve the
  corrected one by 1:00 PM or we pay a late penalty."
- "The customer's CFO is threatening to cancel. Can you call him before
  4:00 today?"

## normal

Legitimate work or personal mail that was written for this recipient or for
a small working group, with no deadline in the next two working days. This
covers status updates and FYIs, ordinary questions, documents sent for
review without a near deadline, meeting scheduling for later dates, replies
in an ongoing discussion, and personal notes from friends or family.

Examples:

- "Attached is the draft term sheet. Let me know if you have comments
  before our meeting the week after next."
- "Thanks for lunch yesterday. Are you still coming to the lake in
  August?"

## ignore

Mail the recipient can leave unread at no cost: advertising and spam from
vendors, newsletters and news digests, announcements sent to large employee
lists (events, training offerings, facilities notices), and automated
notifications that do not require the recipient to do anything.

Examples:

- "This week only: 40% off all standing desks. Reply REMOVE to
  unsubscribe."
- "To all employees: the annual bake sale is in the lobby on Friday from
  11:00 to 1:00."

## Deciding between two labels

- The wording does not decide the label. An email with "URGENT" in the
  subject that asks nothing of the recipient is not `urgent`. A calm email
  that says "I need your signature by 3:00 PM today" is `urgent`.
- A request with a deadline more than two working days away, or with no
  deadline, is `normal`.
- Mass mailings and advertising are `ignore` even when they use words such
  as "act now" or "important", because nothing is asked of this recipient in
  particular.
- An automated notice that asks this specific recipient to act (for
  example, an expense report waiting for their approval) is `normal`, or
  `urgent` if it states a deadline within two working days.
- A short personal or social message from someone the recipient knows is
  `normal`, not `ignore`.

Use the format in this way. ``category`` must be one of the three lower-case values(urgent, normal, ignore) and 
``reason`` is a non-empty string.

Here is an example for the returned message: 
{"reason": "The customers'manager secheduled an important meeting taody, you need to report the budget planning", "category": "urgent"}

The following is Email information:\n\n"""


def build_messages(email: Email) -> list[dict]:
    # parse the email components from json base on the Email type hint
    sent_at = datetime.fromisoformat(email["date"]).strftime("%A, %Y-%m-%d %H:%M %Z")
    recepients = ", ".join(email["to"]) or "No Recipients" # in Email type, this could a list of recipients
    subject = email["subject"] or "No Subject"
    email_body = email["body"] or "Empty Body"

    # comcatnate the email text
    email_text = f"""From: {email["from"]}
TO: {recepients}
Subject: {subject}
Date: {sent_at}
Email_body: {email_body}

"""


    message = [{"role": "user", "content": SYSTEM_PROMPT + email_text}]

    return message


def parse_reply(reply: str) -> dict:
    try:
        lm_reply = json.loads(reply)
    except json.JSONDecodeError:
        lm_reply = None
    if not lm_reply:
        return dict(UNKNOWN)
    if isinstance(lm_reply, dict):
        category = lm_reply.get("category")
        if not isinstance(category, str):
            return dict(UNKNOWN)
        category = category.strip().lower()

        if category not in VALID_PRIORITY:
            return dict(UNKNOWN)

        reason = lm_reply.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            reason = "Could not parse the model's reply"

        return {"category": category, "reason": reason.strip()}
    else:
        return dict(UNKNOWN)



def classify_priority(email: Email, lm: LMCallable) -> dict:
    message = build_messages(email)
    try:
        reply = lm(message)
    except Exception as e:
        log.warning("model call failed: %s", e)
        reply = None
    if not reply:
        return  {"category": "unknown", "reason": "LLM call failed"}
    final_reply = parse_reply(reply)
    return final_reply

