"""
Jenkins build status: one-shot checks and blocking monitor loop (no background tasks).
"""

from __future__ import annotations

from typing import Optional

from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp



def _format_check_body(job_name: str, build_number: int, status: dict) -> str:
    if "error" in status:
        return f"""❌ Jenkins error
Job: {job_name}
Build: #{build_number}
Error: {status['error']}
"""

    url = status.get("url", "")
    building = status.get("building", False)
    result = status.get("result")
    duration_ms = status.get("duration", 0) or 0
    duration_min = duration_ms / 1000 / 60

    if building:
        return f"""🔄 Build in progress
Job: {job_name}
Build: #{build_number}
URL: {url}
"""

    emoji = {
        "SUCCESS": "✅",
        "FAILURE": "❌",
        "ABORTED": "⚠️",
        "UNSTABLE": "⚠️",
    }.get(result or "", "❓")

    return f"""{emoji} Build finished: {result or "UNKNOWN"}
Job: {job_name}
Build: #{build_number}
Duration: {duration_min:.2f} minutes
URL: {url}
"""


@mcp.tool()
async def get_build_log(
    job_path: str,
    build_number: int,
) -> str:
    """
    Return the console output (log) of a Jenkins build.

    Args:
        job_path: Job path (e.g., cluster-as-a-service/provision_ocp_clusters).
        build_number: Jenkins build number.
    """
    jn = job_path.strip()
    try:
        log = JenkinsClient.getJenkinsClient().jenkins.get_build_console_output(jn, build_number)
        return log
    except Exception as e:
        return f"Error fetching logs for {jn} #{build_number}: {e}"

@mcp.tool()
async def check_build_status(
    job_path: Optional[str] = None,
    build_number: Optional[int] = None,
    build_url: Optional[str] = None,    # includes job path and build number (e.g., https://myjenkins.redhat.com/job/cluster-as-a-service/provision_ocp_clusters/8/)
) -> str:
    """
    Return the current status of a Jenkins build (one request, no polling).

    Args:
        build_number: Jenkins build number. If omitted, defaults to 8 (works when MCP sends no args).
        job_path: Optional job path (default: cluster-as-a-service/provision_ocp_clusters).
    """

    jn = (job_path or "").strip()
    info = JenkinsClient.getJenkinsClient().jenkins.get_build_info(jn, build_number)
    status = {
        "url": info.get("url", ""),
        "building": info.get("building", False),
        "result": info.get("result"),
        "duration": info.get("duration", 0) or 0,
    }
    return _format_check_body(jn, build_number, status)
