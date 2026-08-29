import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Any, Optional
from config.settings import settings
from src.qa.circuit_breaker import circuit_breaker

logger = logging.getLogger(__name__)

class DailyReporter:
    def generate_report(
        self,
        concept_type: str,
        titles: List[Dict[str, Any]],
        script_data: Dict[str, Any],
        qa_summary: Dict[str, Any],
        youtube_video_id: Optional[str],
        output_dir: Optional[Path] = None
    ) -> str:
        """
        Generates HTML review email & free-tier usage dashboard.
        Saves report preview to output/report_preview.html.
        """
        out_dir = output_dir or settings.OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        qa_passed = qa_summary.get("overall_passed", False)
        status_color = "#2e7d32" if qa_passed else "#c62828"
        status_text = "PASSED — Video Ready / Uploaded (Private)" if qa_passed else "FAILED — Upload Blocked"

        checks_rows = []
        for c in qa_summary.get("itemized_checks", []):
            badge = '<span style="color:#2e7d32; font-weight:bold;">[PASS]</span>' if c["passed"] else '<span style="color:#c62828; font-weight:bold;">[FAIL]</span>'
            checks_rows.append(f"<tr><td style='padding:8px; border-bottom:1px solid #ddd;'>{c['name']}</td><td style='padding:8px; border-bottom:1px solid #ddd;'>{badge}</td><td style='padding:8px; border-bottom:1px solid #ddd;'>{c['reason']}</td></tr>")

        title_cards = []
        for t in titles:
            tmdb_link = f"https://www.themoviedb.org/{t.get('media_type', 'movie')}/{t.get('tmdb_id')}"
            title_cards.append(f"<li><b><a href='{tmdb_link}' target='_blank'>{t.get('title')}</a></b> ({t.get('year')}) — Rating: {t.get('rating')}/10 — Genres: {', '.join(t.get('genres', []))}</li>")

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family: Arial, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px; color: #333; }}
  .container {{ max-width: 700px; background: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 0 auto; }}
  .header {{ background-color: {status_color}; color: white; padding: 15px; border-radius: 6px; text-align: center; font-size: 20px; font-weight: bold; }}
  .section {{ margin-top: 20px; }}
  h3 {{ border-bottom: 2px solid #eeeeee; padding-bottom: 8px; color: #111; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }}
  th {{ background: #f0f4f8; padding: 10px; text-align: left; }}
  .dashboard-card {{ background: #eef2f5; padding: 15px; border-radius: 6px; font-size: 13px; line-height: 1.6; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">{status_text}</div>
  
  <div class="section">
    <h3>📌 Daily Run Summary</h3>
    <p><b>Concept Type:</b> {concept_type}</p>
    <p><b>YouTube Short Title:</b> {script_data.get('video_title')}</p>
    <p><b>YouTube Video ID:</b> {youtube_video_id or 'None (Not Uploaded)'}</p>
  </div>

  <div class="section">
    <h3>🎬 Featured TMDB Titles</h3>
    <ul>
      {''.join(title_cards)}
    </ul>
  </div>

  <div class="section">
    <h3>🛡️ Supervisor QA Gate Itemized Report ({qa_summary.get('passed_count')}/{qa_summary.get('total_checks')} Passed)</h3>
    <table>
      <thead>
        <tr><th>Check Name</th><th>Status</th><th>Reason / Details</th></tr>
      </thead>
      <tbody>
        {''.join(checks_rows)}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h3>💡 Free-Tier Safeguards Dashboard</h3>
    <div class="dashboard-card">
      <p><b>GitHub Actions Minutes:</b> Free & Unlimited (Public Repository)</p>
      <p><b>TMDB API Cost:</b> $0.00 (Free Non-Commercial Key)</p>
      <p><b>Edge-TTS Cost:</b> $0.00 (100% Free Neural Voice)</p>
      <p><b>LLM Circuit Breaker Status:</b> {'TRIPPED (Fallback Engine Used)' if circuit_breaker.is_tripped else 'Active / Healthy'}</p>
      <p><b>YouTube API Daily Quota Used:</b> ~1,600 units (Daily Free Limit: 10,000 units)</p>
    </div>
  </div>
</div>
</body>
</html>
"""

        # Save preview to output/report_preview.html
        preview_file = out_dir / "report_preview.html"
        with open(preview_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"Daily report HTML saved to {preview_file}")

        # Send email if configured
        if settings.SMTP_SERVER and settings.NOTIFICATION_EMAIL:
            self._send_email(html_content, status_text)

        return html_content

    def _send_email(self, html_content: str, subject_status: str):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[TMDB Shorts Bot] Daily Report — {subject_status}"
            msg["From"] = settings.SMTP_USERNAME
            msg["To"] = settings.NOTIFICATION_EMAIL
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USERNAME, [settings.NOTIFICATION_EMAIL], msg.as_string())
            logger.info(f"Daily report email sent to {settings.NOTIFICATION_EMAIL}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
