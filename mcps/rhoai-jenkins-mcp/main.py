import argparse
import os
from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp

def main():
    print("Connecting to Jenkins MCP Server")
    parser=argparse.ArgumentParser(description="Jenkins Server Parameters")
    parser.add_argument("--jenkins-url", help="Jenkins Server URL", required=False, dest="jenkins_url", default=os.environ.get("JENKINS_URL"))
    parser.add_argument("--jenkins-user", help="Jenkins Server User", required=False, dest="jenkins_user", default=os.environ.get("JENKINS_USER"))
    parser.add_argument("--jenkins-password", help="Jenkins Server Password", required=False, dest="jenkins_password", default=os.environ.get("JENKINS_TOKEN", os.environ.get("JENKINS_PASSWORD")))
    args=parser.parse_args()

    if args.jenkins_url is None or args.jenkins_user is None or args.jenkins_password is None:
        print("Jenkins Server Parameters are not set")
        return

    print(args)
    print(f"Jenkins Server URL: {args.jenkins_url}")
    print(f"Jenkins Server User: {args.jenkins_user}")
    print(f"Jenkins Server Password: {args.jenkins_password}")

    jenkins_client = JenkinsClient(args.jenkins_url, args.jenkins_user, args.jenkins_password)
    
    print("Starting MCP Server")
    # from jenkins_mcp.server import mcp
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
