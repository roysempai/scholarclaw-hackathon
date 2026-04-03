"""
ScholarClaw — Reminder Agent
Schedules and sends deadline reminders via SendGrid.
Runs every 24h via APScheduler to check for upcoming deadlines.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from dataclasses import dataclass

from config import settings
from db import prisma

logger = logging.getLogger("agents.reminder")

# Reminder thresholds in days
REMINDER_THRESHOLDS = [30, 7, 1]


@dataclass
class ReminderResult:
    """Result of a reminder check/send operation."""
    student_id: str
    scheme_id: str
    days_until_deadline: int
    sent: bool
    message: str


class ReminderAgent:
    """
    Agent responsible for scheduling and sending deadline reminders.

    Runs on a 24-hour schedule to check all student-scheme matches
    and sends email reminders at 30, 7, and 1 day(s) before deadline.
    """

    def __init__(self):
        self._sendgrid_available = bool(settings.SENDGRID_API_KEY)
        if not self._sendgrid_available:
            logger.warning("SENDGRID_API_KEY not set — email reminders will be skipped")

    async def schedule_reminders(self) -> list[ReminderResult]:
        """
        Main scheduled job: check all students and their matched schemes.

        For each student-scheme pair:
        1. Calculate days until deadline
        2. Check if reminder should be sent (30, 7, 1 days)
        3. Send email if not already sent for this threshold
        4. Update ReminderStatus table

        Returns:
            List of ReminderResult for each processed match.
        """
        results: list[ReminderResult] = []
        today = datetime.now(timezone.utc).date()

        try:
            # Get all active student profiles with their matched schemes
            profiles = await prisma.studentprofile.find_many(
                include={"user": True}
            )

            for profile in profiles:
                # Get schemes matched to this student
                # In production, this would query a MatchedSchemes table
                # For now, we query all schemes and check eligibility
                matched_schemes = await self._get_matched_schemes(profile.userId)

                for scheme in matched_schemes:
                    result = await self._process_scheme_reminder(
                        student_id=profile.userId,
                        student_email=profile.user.email if profile.user else None,
                        student_name=profile.user.fullName if profile.user else "Student",
                        scheme_id=scheme["id"],
                        scheme_name=scheme["name"],
                        deadline=scheme["deadline"],
                        today=today,
                    )
                    if result:
                        results.append(result)

            logger.info(
                "Reminder job completed: processed %d student-scheme pairs, sent %d reminders",
                len(results),
                sum(1 for r in results if r.sent),
            )

        except Exception as exc:
            logger.error("Reminder job failed: %s", exc)

        return results

    async def _get_matched_schemes(self, student_id: str) -> list[dict]:
        """
        Get schemes matched to a student.

        In a full implementation, this would query a MatchedSchemes junction table.
        For now, returns all active schemes with deadlines.
        """
        try:
            schemes = await prisma.scholarshipscheme.find_many(
                where={
                    "deadline": {"gte": datetime.now(timezone.utc)},
                }
            )
            return [
                {
                    "id": s.id,
                    "name": s.name,
                    "deadline": s.deadline,
                }
                for s in schemes
            ]
        except Exception as exc:
            logger.warning("Failed to get matched schemes for %s: %s", student_id, exc)
            return []

    async def _process_scheme_reminder(
        self,
        student_id: str,
        student_email: Optional[str],
        student_name: str,
        scheme_id: str,
        scheme_name: str,
        deadline: datetime,
        today,
    ) -> Optional[ReminderResult]:
        """
        Process a single student-scheme pair for reminder eligibility.
        """
        if not deadline:
            return None

        deadline_date = deadline.date() if isinstance(deadline, datetime) else deadline
        days_until = (deadline_date - today).days

        # Check if this matches a reminder threshold
        matching_threshold = None
        for threshold in REMINDER_THRESHOLDS:
            if days_until == threshold:
                matching_threshold = threshold
                break

        if matching_threshold is None:
            return None  # Not a reminder day

        # Check if reminder was already sent for this threshold
        already_sent = await self._check_reminder_sent(
            student_id=student_id,
            scheme_id=scheme_id,
            threshold_days=matching_threshold,
        )

        if already_sent:
            return ReminderResult(
                student_id=student_id,
                scheme_id=scheme_id,
                days_until_deadline=days_until,
                sent=False,
                message=f"Reminder for {matching_threshold} days already sent",
            )

        # Send the reminder
        sent = await self.send_reminder_email(
            student_email=student_email,
            student_name=student_name,
            scheme_name=scheme_name,
            days_until_deadline=days_until,
            deadline=deadline_date,
        )

        # Record the reminder status
        if sent:
            await self._record_reminder_sent(
                student_id=student_id,
                scheme_id=scheme_id,
                threshold_days=matching_threshold,
                deadline=deadline,
            )

        return ReminderResult(
            student_id=student_id,
            scheme_id=scheme_id,
            days_until_deadline=days_until,
            sent=sent,
            message=f"Reminder {'sent' if sent else 'failed'} for {matching_threshold}-day threshold",
        )

    async def _check_reminder_sent(
        self,
        student_id: str,
        scheme_id: str,
        threshold_days: int,
    ) -> bool:
        """Check if a reminder was already sent for this threshold."""
        try:
            status = await prisma.reminderstatus.find_first(
                where={
                    "studentId": student_id,
                    "schemeId": scheme_id,
                    "thresholdDays": threshold_days,
                    "sent": True,
                }
            )
            return status is not None
        except Exception as exc:
            logger.warning("Failed to check reminder status: %s", exc)
            return False  # Assume not sent if check fails

    async def _record_reminder_sent(
        self,
        student_id: str,
        scheme_id: str,
        threshold_days: int,
        deadline: datetime,
    ) -> None:
        """Record that a reminder was sent."""
        try:
            await prisma.reminderstatus.create(
                data={
                    "studentId": student_id,
                    "schemeId": scheme_id,
                    "thresholdDays": threshold_days,
                    "deadlineDate": deadline,
                    "sent": True,
                    "sentAt": datetime.now(timezone.utc),
                }
            )
        except Exception as exc:
            logger.error("Failed to record reminder status: %s", exc)

    async def send_reminder_email(
        self,
        student_email: Optional[str],
        student_name: str,
        scheme_name: str,
        days_until_deadline: int,
        deadline,
    ) -> bool:
        """
        Send a reminder email via SendGrid.

        Gracefully skips if SENDGRID_API_KEY is not set.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        if not self._sendgrid_available:
            logger.debug("SendGrid not configured — skipping email for %s", student_email)
            return True  # Return True to record as "handled" but not sent

        if not student_email:
            logger.warning("No email address for student — cannot send reminder")
            return False

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            # Format the deadline
            deadline_str = deadline.strftime("%B %d, %Y") if hasattr(deadline, "strftime") else str(deadline)

            # Build urgency text
            if days_until_deadline == 1:
                urgency = "URGENT: Tomorrow is the deadline!"
            elif days_until_deadline == 7:
                urgency = "Reminder: One week left!"
            else:
                urgency = f"Reminder: {days_until_deadline} days remaining"

            # Create email content
            subject = f"[ScholarClaw] {urgency} - {scheme_name}"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Scholarship Deadline Reminder</h2>
                <p>Dear {student_name},</p>
                <p>This is a reminder that the deadline for <strong>{scheme_name}</strong> is approaching.</p>
                <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
                    <p style="margin: 0;"><strong>Deadline:</strong> {deadline_str}</p>
                    <p style="margin: 8px 0 0 0;"><strong>Days remaining:</strong> {days_until_deadline}</p>
                </div>
                <p>Make sure to complete your application before the deadline!</p>
                <p>
                    <a href="{settings.FRONTEND_URL}/dashboard"
                       style="background: #2563eb; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Application
                    </a>
                </p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
                <p style="color: #6b7280; font-size: 12px;">
                    This is an automated reminder from ScholarClaw.
                    You received this because you matched with this scholarship scheme.
                </p>
            </body>
            </html>
            """

            message = Mail(
                from_email="noreply@scholarclaw.com",
                to_emails=student_email,
                subject=subject,
                html_content=html_content,
            )

            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)

            if response.status_code in (200, 201, 202):
                logger.info(
                    "Reminder email sent to %s for scheme %s (%d days)",
                    student_email,
                    scheme_name,
                    days_until_deadline,
                )
                return True
            else:
                logger.warning(
                    "SendGrid returned status %d for %s",
                    response.status_code,
                    student_email,
                )
                return False

        except ImportError:
            logger.warning("sendgrid package not installed — cannot send email")
            return False
        except Exception as exc:
            logger.error("Failed to send reminder email: %s", exc)
            return False


# ── Module-level singleton ───────────────────────────────────────
reminder_agent = ReminderAgent()


async def run_reminder_job() -> None:
    """
    Entry point for the APScheduler job.
    Called every 24 hours to process reminders.
    """
    logger.info("Starting scheduled reminder job...")
    await reminder_agent.schedule_reminders()
