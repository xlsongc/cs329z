"""Problem Set 1, Problem 2: Digest Pipeline"""

from __future__ import annotations

from datetime import datetime
import json
import logging

from cs329z_hw1.types import Email, LMCallable

from .priority import classify_priority

log = logging.getLogger(__name__)

URGENCY_RANK = {"urgent": 0, "normal": 1, "unknown": 1, "ignore": 2}
DIGEST_SYSTEM_PROMPT = """You are a professional working assistant that can help summarize a whole day's emails into a concise daily digest.
Do the digest work based on the priority of the emails, for the urgent emails, you will be provided with the email's information with the content,
for normal emails, you will only get the email's basic infomration, such as the subject, from, and date.
when send back the digest, you should first list all the urgent emials, urgent emails should come with a short desctiption of the email's content, should contain
the company, project, and the site name; then you can use a short description to describe normal emails.
The following is an example of the digest format:

URGENT:
1. Subject: [Subject of the email] Description: [Short description of the email's content, including  company, project, and the site name] 
   # for example, "Subject: Orlin Valley Gas margin call: approve the $4.2M wire by 2PM"

You have xxx normal emails today, mainly about xxx(one sentence).

The digest should be concise and clear, and should not contain any unnecessary information. The digest should be less than 250 words. 
The following is the list of emails that you need to summarize into a digest:
"""


def classify_all(emails: list[Email], lm: LMCallable) -> list[tuple[Email, dict]]:
    """Classify all emails in the list and return a list of tuples of (email, classification)"""
    results = []
    for email in emails:
        classification = classify_priority(email, lm)
        results.append((email, classification))
    return results

def drop_ignore(pairs: list[tuple[Email, dict]]) -> list[tuple[Email, dict]]:
    """Drop all emails that are classified as 'ignore'"""
    return [(email, classification) for email, classification in pairs if classification.get("category") != "ignore"]


def is_better(a: tuple[Email, dict], b: tuple[Email, dict]) -> bool:
    email_a, cls_a = a[0], a[1]["category"]
    email_b, cls_b = b[0], b[1]["category"]

    if URGENCY_RANK[cls_a] < URGENCY_RANK[cls_b]:
        return True
    elif URGENCY_RANK[cls_a] > URGENCY_RANK[cls_b]:
        return False
    else:
        return email_a["date"] > email_b["date"]  # latest date is better


def one_per_thread(pairs: list[tuple[Email, dict]]) -> list[tuple[Email, dict]]:
    best = {}
    for email, cls in pairs:
        tid = email["thread_id"]
        if tid not in best or is_better((email, cls), best[tid]):
            best[tid] = (email, cls)
    return list(best.values())

def sort_by_urgency(pairs: list[tuple[Email, dict]]) -> list[tuple[Email, dict]]:
    return sorted(pairs, key=lambda x: (URGENCY_RANK[x[1]["category"]]))

def format_email(email: Email, cls: dict) -> str:
    """Format an email and its classification into a string for the digest"""
    if cls["category"] == "urgent":
        return f"URGENT: {cls['reason']}" + f"\nSubject: {email['subject'] or '(no subject)'}\nFrom: {email['from']}\nDate: {email['date']}\nContent: {email['body'][:1500]}\n\n" # set a limit for the content length to avoid too long digest and token limit
    else:
        return "NORMAL" +f"\nSubject: {email['subject'] or '(no subject)'}\nFrom: {email['from']}\nDate: {email['date']}\n\n"

def build_digest_message(pairs: list[tuple[Email, dict]]) -> list[dict]:
    """Build a digest message from a list of (email, classification) tuples to be sent to the llm"""
    urgent_emails = []
    normal_emails = []
    for email, cls in pairs:
        if cls["category"] == "urgent":
            urgent_emails.append(format_email(email, cls))
        else:
            normal_emails.append(format_email(email, cls))
    urgent_text = "\n\n".join(urgent_emails)
    normal_text = "\n\n".join(normal_emails)
    user_content = f"""URGENT ({len(urgent_emails)} emails):
{urgent_text}
OTHER ({len(normal_emails)} emails):
{normal_text}
"""
    return [
        {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

def write_digest(pairs: list[tuple[Email, dict]], lm: LMCallable) -> str:
    """Write a digest from a list of (email, classification) tuples using the llm"""
    message = build_digest_message(pairs)
    try:
        digest = lm(message)
    except Exception as e:
        log.warning("model call failed: %s", e)
        digest = "The model call failed, please try again later."
    return digest

def daily_digest(emails: list[Email], lm: LMCallable) -> str:
    """Generate a daily digest from a list of emails using the llm"""
    if not emails:
        return "No emails to summarize."
    pairs = classify_all(emails, lm)
    pairs = drop_ignore(pairs)
    pairs = one_per_thread(pairs)
    pairs = sort_by_urgency(pairs)
    digest = write_digest(pairs, lm)
    return digest

