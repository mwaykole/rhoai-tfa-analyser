from collections import defaultdict
from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
import json

# jenkins_client = JenkinsClient.getJenkinsClient()


class ClusterOffering(BaseModel):
    """Configuration for cluster offering."""

    cluster_offerings: Literal["AWS", "AWS OSD", "GCP", "GCP OSD", "IBM", "AZURE", "ROSA Classic", "ROSA HCP", "PSI"] = Field(
        default="ROSA HCP",
        description="Offering type to provision the cluster on"
    )

    class Config:
        # Allow both snake_case and SCREAMING_SNAKE_CASE
        populate_by_name = True


@mcp.resource("cluster://offerings")
async def get_cluster_offerings() -> str:
    """
    Get all cluster offerings supported by the system.
    
    Returns:
        str: JSON-formatted cluster offerings
    """
    enum = ClusterOffering.model_json_schema()["properties"]["cluster_offerings"]["enum"]
    return json.dumps(enum, indent=2)


@mcp.tool()
async def run_test_matrix(rhoai_version: str, build_image_url: str, providers: dict, team: str, mode: str = "auto") -> list:
    """
    Run the test_matrix_run job on the given build image URL.
    Validate a RHOAI build against the given providers.

    Args:
        rhoai_version (str): The RHOAI version to validate.
        build_image_url (str): The URL of the build image to validate.
        mode (str): The mode to run the test matrix in.
        providers (dict): The providers to validate the build against.
        team (str): The team to run the test matrix for. Default to devtestops
    Returns:
        String: The jenkins job run URL.
    """
    # Trigger the Jenkins job with the image URL as a parameter
    job_name = "devops/test_matrix_run"
    # name,enabled,ocp,fips,sno@@@
    print(providers)
    prov_strs = ""
    if providers:
        for provider, config_dict in providers.items():
            config_dict = defaultdict(int, config_dict)
            prov_str = f"{provider},"
            prov_str += f"{config_dict.get('enabled', "true")},"
            prov_str += f"{config_dict.get('ocp', None)},"
            prov_str += f"{config_dict.get('fips', "false")},"
            prov_str += f"{config_dict.get('sno', "false")}"
            prov_str += "@@@"
            prov_strs += prov_str

    fetch = True if mode.lower() == "auto" else False
    params = {
        "OVERRIDE_ODS_BUILD_URL": build_image_url,
        "RHOAI_VERSION_XY": rhoai_version,
        "FETCH_TEST_MATRIX": fetch,
        "CLOUD_PROVIDERS_TABLE": prov_strs,
        "TEAM_NAME": team,
    }
    return JenkinsClient.getJenkinsClient().run_job(job_name, params)


@mcp.tool()
async def provision_cluster(
    cluster_offering: ClusterOffering = ClusterOffering(),
    ocp_version: str = None,
    sno: bool = False,
    fips: bool = False,
) -> str:
    """
    Provision a cluster for testing RHOAI.

    Args:
        cluster_offering: Cluster offering type (see ClusterOffering for all options)
        ocp_version: OpenShift version (optional)
        sno: SNO flag (optional)
        fips: FIPS flag (optional)

    Returns:
        Jenkins job run URL

    Note:
        Check cluster://offerings resource for cluster offerings.
    """

    job_name = "cluster-as-a-service/provision_ocp_clusters"

    # Handle OCP version format
    if not ocp_version:
        ocp_version = "4.20"
    # TODO: force ocp version formatting to be like x.y.z or x.y

    cluter_details = f"{cluster_offering},{ocp_version},{sno},{fips}"
    params = {
        "CLUSTER_DETAILS": cluter_details,
    }

    return JenkinsClient.getJenkinsClient().run_job(job_name, params)

#async def get_cluster_info_from_build(build_number: str) -> dict:
#    """
#    Get the cluster info from the given build number of provisioning job.
#    """
#    job_name = "devops/rhoai-test-flow"
#    build_info = JenkinsClient.getJenkinsClient().jenkins.get_build_info(job_name, build_number)
#    return build_info['cluster_info']

@mcp.tool()
async def get_provisioning_job_status(build_url: str) -> str:
    """
    Get the status of the provisioning job.
    """
    from jenkins_mcp.server.monitoring_tools import check_build_status
    return await check_build_status(build_url=build_url)
