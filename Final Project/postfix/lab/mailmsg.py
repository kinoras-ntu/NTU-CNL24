import email
import base64
import email.header
import json
from openai import OpenAI


class MailMessage:
    def __init__(self, data):
        message = email.message_from_bytes(data)

        self.key = ""
        self.subject = self.decode(message.get("Subject", "No Subject"))
        self.sender = self.decode(message.get("From", "No Sender"))
        self.body = ""

        for part in message.walk():
            charset = part.get_content_charset()
            if part.get_content_type() == "text/plain" and charset:
                content = part.get_payload(decode=True).decode(charset)
                if charset.lower() in ["gb2312", "gb18030", "big5"]:
                    content = base64.b64decode(content).decode(charset)
                self.body += str(content)

    def __str__(self):
        return str({"subject": self.subject, "sender": self.sender, "body": self.body})

    def decode(self, data):
        return "".join(
            word.decode(encoding or "utf-8") if isinstance(word, bytes) else word
            for word, encoding in email.header.decode_header(data)
        )

    def check(self):
        count = 3
        while True and count > 0:
            try:
                prompt = (
                    "# Task Description\n\n"
                    + "**Task:** Determine whether the following email is spam or not.\n\n"
                    + "**Main considerations:**\n"
                    + "1. Assess the trustworthiness of the sender:\n"
                    + "  - Be cautious of normal users pretending to be an administrator.\n"
                    + "  - Consider the possibility that the user's account may have been compromised.\n"
                    + "2. Evaluate the purpose and the context of the email:\n"
                    + "  - Determine if it asks you to perform any actions that could be harmful or risky.\n"
                    + "  - Check if the purpose of the email aligns with the sender's supposed identity.\n"
                    + "  - Assess if the email is direct or forwarded, especially from personal accounts, to prevent credibility misuse in fraudulent claims. \n"
                    + "3. Identify any suspicious links or text:\n"
                    + "  - Verify if the links genuinely belong to the claimed sender (e.g., distinguishing between 'apple.com' and 'app1e.com').\n"
                    + "  - Inspect the format and structure of URLs in the email for unusual characters or patterns.\n"
                    + "  - Be particularly wary of administrative actions directed to personal websites or directories under the same domain, as this is a common phishing tactic.\n"
                    + "4. For forwarded or replied emails:\n"
                    + "  - The address of a forwarded or replied mail is usually different from the original mail\n"
                    + "  - Check the messages and intention of the forwarder/replier and the original message separately, and then evaluate their connection.\n"
                    + "**Response format:**\n"
                    + "Please response in JSON format text. Do not use markdown syntax.\n"
                    + "- The first property is called 'probability'. It is a floating point number from 0 to 1 representing the probability of the message being spam (0: very unlikely, 1: very sure).\n"
                    + "- The second property is called 'reason', It is a string representing the main reason of your judgement. Since this is the title, it needs to be clear and brief.\n"
                    + "- The third field is called 'description', it is a detailed explanation (within 40 words) of your decision to the user.\n\n"
                    + "---\n\n"
                    + "# Problem\n\n"
                    + f"**Subject:**\n{self.subject}\n\n"
                    + f"**Sender:**\n{self.sender}\n\n"
                    + f"**Content:**\n{self.body}\n\n"
                    + "**Response:**"
                )

                completion = OpenAI(api_key=self.key).chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                )
                result = json.loads(completion.choices[0].message.content)
                if all(k in result for k in ("probability", "reason", "description")):
                    return result
                raise
            except:
                count -= 1
                continue
        return {
            "probability": -1,
            "reason": "Service unavailable",
            "description": "We're currently unable to scan your email for spam. Please be cautious and avoid opening emails from unknown sources or clicking on any suspicious links.",
        }