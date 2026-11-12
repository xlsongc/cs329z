
def format_email(email: dict[str, Any]) -> str:
    """
    Format an email dictionary into a string for display.
    """
    return f"From: {email['from']}\nTo: {email['to']}\nSubject: {email['subject']}\nDate: {email['date']}\n\n{email['body']}"'


def build_messages(question: str, emails: list[dict[str, Any]], queries: list[str], is_last_hop: bool) -> list[dict]:

    return

