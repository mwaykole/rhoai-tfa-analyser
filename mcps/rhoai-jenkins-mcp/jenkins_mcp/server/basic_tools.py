from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp

#jenkins_client = JenkinsClient.getJenkinsClient()

@mcp.tool()
async def get_all_jobs() -> list:
    """
    Get all jobs from Jenkins

    Returns:
        list]: A list of all jobs names
    """
    return JenkinsClient.getJenkinsClient().get_jobs()
