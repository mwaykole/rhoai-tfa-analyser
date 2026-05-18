#!/usr/bin/env python3
"""Jenkins API client for TFA plugin.

Fetches build logs, failed stages, and build metadata from Jenkins pipelines.
Used by TFA orchestrator to correlate Jenkins failures with ReportPortal data.

Environment variables:
    JENKINS_URL   - Jenkins server URL
    JENKINS_USER  - Jenkins username
    JENKINS_TOKEN - Jenkins API token
    JENKINS_JOB   - Default job name (optional)

Based on patterns from https://github.com/bdattoma/jenkins_monitor
"""

import json
import os
import re
import urllib3
from datetime import datetime
from typing import Any

import jenkins

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JenkinsClient:
    """Jenkins API client for build log extraction and failure analysis."""

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        token: str | None = None,
        job_name: str | None = None,
        verify_ssl: bool = False,
    ):
        self.url = (url or os.environ.get("JENKINS_URL", "")).rstrip("/")
        self.username = username or os.environ.get("JENKINS_USER", "")
        self.token = token or os.environ.get("JENKINS_TOKEN", "")
        self.job_name = job_name or os.environ.get("JENKINS_JOB", "")
        self.verify_ssl = verify_ssl
        self._server: jenkins.Jenkins | None = None

    def connect(self) -> None:
        """Establish connection to Jenkins server."""
        if not self.url:
            raise ValueError("JENKINS_URL is required")
        if not self.username or not self.token:
            raise ValueError("JENKINS_USER and JENKINS_TOKEN are required")

        self._server = jenkins.Jenkins(
            self.url, username=self.username, password=self.token
        )
        self._server._session.verify = self.verify_ssl

    @property
    def server(self) -> jenkins.Jenkins:
        if self._server is None:
            self.connect()
        return self._server

    def get_build_info(self, build_number: int, job_name: str | None = None) -> dict[str, Any]:
        """Get full build metadata including parameters and status."""
        job = job_name or self.job_name
        build_info = self.server.get_build_info(job, build_number)

        parameters = {}
        for action in build_info.get("actions", []):
            if action.get("_class") == "hudson.model.ParametersAction":
                for param in action.get("parameters", []):
                    name = param.get("name")
                    if name:
                        parameters[name] = param.get(
                            "value", param.get("defaultValue")
                        )

        return {
            "number": build_info["number"],
            "status": build_info.get("result") or "RUNNING",
            "building": build_info["building"],
            "timestamp": build_info["timestamp"],
            "duration": build_info["duration"],
            "url": build_info["url"],
            "parameters": parameters,
        }

    def get_console_log(self, build_number: int, job_name: str | None = None) -> str:
        """Get full console output for a build."""
        job = job_name or self.job_name
        return self.server.get_build_console_output(job, build_number)

    def get_failed_stages(self, build_number: int, job_name: str | None = None) -> list[str]:
        """Get list of failed stage names from a pipeline build.

        Uses wfapi/describe endpoint first, falls back to console log parsing.
        """
        job = job_name or self.job_name
        failed_stages = []

        # Method 1: wfapi/describe endpoint (structured data)
        try:
            base_url = self.server.server.rstrip("/")
            job_path = "/job/".join(job.split("/"))
            stages_url = f"{base_url}/job/{job_path}/{build_number}/wfapi/describe"
            response = self.server._session.get(stages_url)

            if response.status_code == 200:
                stages_data = response.json()
                for stage in stages_data.get("stages", []):
                    if stage.get("status") in ("FAILED", "FAILURE"):
                        failed_stages.append(stage["name"])
                if failed_stages:
                    return failed_stages
        except Exception:
            pass

        # Method 2: Parse console output for stage failures
        try:
            console = self.get_console_log(build_number, job)
            lines = console.split("\n")

            for i, line in enumerate(lines):
                if "[Pipeline] stage" in line or 'Stage "' in line:
                    for j in range(i, min(i + 20, len(lines))):
                        if any(kw in lines[j] for kw in ("ERROR", "FAILED", "failed")):
                            match = re.search(r"\[Pipeline\] stage.*?\((.*?)\)", line)
                            if match:
                                stage_name = match.group(1)
                                if stage_name not in failed_stages:
                                    failed_stages.append(stage_name)
                            break
        except Exception:
            pass

        return failed_stages

    def get_stage_log(self, build_number: int, stage_name: str, job_name: str | None = None) -> str | None:
        """Get log output for a specific stage using wfapi.

        Returns the log text for the named stage, or None if not found.
        """
        job = job_name or self.job_name

        try:
            base_url = self.server.server.rstrip("/")
            job_path = "/job/".join(job.split("/"))
            stages_url = f"{base_url}/job/{job_path}/{build_number}/wfapi/describe"
            response = self.server._session.get(stages_url)

            if response.status_code != 200:
                return None

            stages_data = response.json()
            for stage in stages_data.get("stages", []):
                if stage.get("name") == stage_name:
                    node_url = stage.get("_links", {}).get("self", {}).get("href")
                    if node_url:
                        log_url = f"{base_url}{node_url}log"
                        log_resp = self.server._session.get(log_url)
                        if log_resp.status_code == 200:
                            log_data = log_resp.json()
                            return log_data.get("text", "")
        except Exception:
            pass

        return None

    def get_failed_builds(
        self,
        limit: int = 10,
        job_name: str | None = None,
        filter_params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent failed builds with optional parameter filtering."""
        job = job_name or self.job_name
        job_info = self.server.get_job_info(job, depth=1)

        builds_to_check = job_info["builds"][:limit] if limit else job_info["builds"]
        failed_builds = []

        for build in builds_to_check:
            build_num = build["number"]
            try:
                info = self.get_build_info(build_num, job)

                if info["status"] != "FAILURE":
                    continue

                if filter_params:
                    match = all(
                        str(info["parameters"].get(k)) == str(v)
                        for k, v in filter_params.items()
                    )
                    if not match:
                        continue

                info["failed_stages"] = self.get_failed_stages(build_num, job)
                failed_builds.append(info)
            except Exception:
                continue

        return failed_builds

    def extract_error_context(
        self, console_log: str, context_lines: int = 10
    ) -> list[dict[str, Any]]:
        """Extract error sections from console log with surrounding context.

        Returns list of error blocks with line numbers and text.
        """
        lines = console_log.split("\n")
        error_patterns = [
            r"(?i)\bERROR\b",
            r"(?i)\bFAILED\b",
            r"(?i)\bFATAL\b",
            r"(?i)Exception:",
            r"(?i)Traceback \(most recent",
            r"FAILURE",
            r"AssertionError",
        ]

        error_blocks = []
        seen_ranges = set()

        for i, line in enumerate(lines):
            for pattern in error_patterns:
                if re.search(pattern, line):
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)

                    range_key = (start, end)
                    if range_key in seen_ranges:
                        break
                    seen_ranges.add(range_key)

                    error_blocks.append({
                        "line_number": i + 1,
                        "match": line.strip(),
                        "context": "\n".join(lines[start:end]),
                    })
                    break

        return error_blocks

    def get_build_artifacts(self, build_number: int, job_name: str | None = None) -> list[dict[str, str]]:
        """List build artifacts (filenames and relative paths)."""
        job = job_name or self.job_name
        build_info = self.server.get_build_info(job, build_number)
        artifacts = []
        for artifact in build_info.get("artifacts", []):
            artifacts.append({
                "filename": artifact.get("fileName", ""),
                "path": artifact.get("relativePath", ""),
            })
        return artifacts

    def download_artifact(self, build_number: int, artifact_path: str, job_name: str | None = None) -> bytes:
        """Download a specific build artifact by its relative path."""
        job = job_name or self.job_name
        base_url = self.server.server.rstrip("/")
        job_path = "/job/".join(job.split("/"))
        url = f"{base_url}/job/{job_path}/{build_number}/artifact/{artifact_path}"
        response = self.server._session.get(url)
        response.raise_for_status()
        return response.content


def main():
    """CLI entrypoint for quick log extraction."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract Jenkins build logs for TFA")
    parser.add_argument("--build", "-b", type=int, required=True, help="Build number")
    parser.add_argument("--job", "-j", help="Job name (overrides JENKINS_JOB env)")
    parser.add_argument("--failed-stages", action="store_true", help="List failed stages")
    parser.add_argument("--console", action="store_true", help="Print full console log")
    parser.add_argument("--errors", action="store_true", help="Extract error context blocks")
    parser.add_argument("--stage-log", help="Get log for a specific stage name")
    parser.add_argument("--artifacts", action="store_true", help="List build artifacts")
    parser.add_argument("--info", action="store_true", help="Print build metadata as JSON")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL verification")

    args = parser.parse_args()

    client = JenkinsClient(
        job_name=args.job,
        verify_ssl=not args.no_verify_ssl,
    )

    if args.info:
        info = client.get_build_info(args.build)
        print(json.dumps(info, indent=2, default=str))

    if args.failed_stages:
        stages = client.get_failed_stages(args.build)
        if stages:
            print("Failed stages:")
            for s in stages:
                print(f"  - {s}")
        else:
            print("No failed stages found.")

    if args.console:
        log = client.get_console_log(args.build)
        print(log)

    if args.errors:
        log = client.get_console_log(args.build)
        blocks = client.extract_error_context(log)
        for block in blocks:
            print(f"\n--- Error at line {block['line_number']} ---")
            print(block["context"])

    if args.stage_log:
        log = client.get_stage_log(args.build, args.stage_log)
        if log:
            print(log)
        else:
            print(f"No log found for stage: {args.stage_log}")

    if args.artifacts:
        artifacts = client.get_build_artifacts(args.build)
        if artifacts:
            print("Build artifacts:")
            for a in artifacts:
                print(f"  - {a['path']}")
        else:
            print("No artifacts found.")


if __name__ == "__main__":
    main()
