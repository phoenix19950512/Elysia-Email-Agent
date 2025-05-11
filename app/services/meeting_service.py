import datetime
from app.auth.graph_auth import GraphAuth
from app.models.schema import MeetingDetails, MeetingNotes
from config import USER_EMAIL

class MeetingService:
    def __init__(self):
        self.auth = GraphAuth()
        self.user_email = USER_EMAIL

    def get_upcoming_meetings(self, days: int = 7):
        now = datetime.datetime.utcnow()
        end = now + datetime.timedelta(days=days)
        
        print("Getting meetings from", now.isoformat(), "to", end.isoformat())

        params = {
            "startDateTime": now.isoformat() + "Z",
            "endDateTime": end.isoformat() + "Z",
            "$orderby": "start/dateTime"
        }
        print("Graph API params:", params)

        response = self.auth.make_request("GET", "me/calendarView", params=params)
        print("Raw Graph Response:", response)

        meetings = []
        for event in response.get("value", []):
            meeting_url = None
            if "onlineMeeting" in event and event["onlineMeeting"] is not None:
                meeting_url = event["onlineMeeting"].get("joinUrl")

            attendees = []
            if "attendees" in event:
                for attendee in event["attendees"]:
                    if "emailAddress" in attendee:
                        attendees.append(attendee["emailAddress"]["address"])

            start_time = datetime.datetime.fromisoformat(event["start"]["dateTime"].replace('Z', '+00:00'))
            end_time = datetime.datetime.fromisoformat(event["end"]["dateTime"].replace('Z', '+00:00'))

            meeting = MeetingDetails(
                subject=event["subject"],
                start_time=start_time,
                end_time=end_time,
                attendees=attendees,
                body=event.get("bodyPreview", ""),
                online_meeting_url=meeting_url
            )
            meetings.append(meeting)

        return meetings

    def join_meeting(self, meeting_url):
        return {
            "status": "ready_to_join",
            "meeting_url": meeting_url,
            "message": "Ready to join the meeting. Click the link or use the meeting client."
        }

    def save_meeting_notes(self, meeting_id, notes, action_items):
        meeting_notes = MeetingNotes(
            meeting_id=meeting_id,
            notes=notes,
            action_items=action_items
        )
        return meeting_notes

    def send_meeting_follow_up(self, meeting_id, meeting_notes):
        endpoint = f"me/events/{meeting_id}"
        meeting = self.auth.make_request("GET", endpoint)

        if not meeting:
            return {"error": "Meeting not found"}

        attendees = []
        for attendee in meeting.get("attendees", []):
            if "emailAddress" in attendee:
                attendees.append({
                    "emailAddress": {
                        "address": attendee["emailAddress"]["address"],
                        "name": attendee["emailAddress"].get("name", "")
                    }
                })

        subject = f"Follow-up: {meeting['subject']}"
        body = f"""
        <p>Hello,</p>
        <p>Thank you for attending the meeting. Here are the notes from our discussion:</p>
        <h3>Meeting Notes:</h3>
        <p>{meeting_notes.notes}</p>
        <h3>Action Items:</h3>
        <ul>
        """
        for item in meeting_notes.action_items:
            body += f"<li>{item}</li>"

        body += """
        </ul>
        <p>Please let me know if you have any questions or if anything needs clarification.</p>
        <p>Best regards,<br>Elysia Partners</p>
        """

        send_mail_endpoint = "me/sendMail"
        data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": attendees
            },
            "saveToSentItems": "true"
        }

        response = self.auth.make_request("POST", send_mail_endpoint, data=data)

        return {
            "status": "email_sent",
            "message": "Follow-up email sent to all attendees."
        }