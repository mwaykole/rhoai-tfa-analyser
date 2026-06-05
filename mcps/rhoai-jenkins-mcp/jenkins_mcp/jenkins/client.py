# from jenkinsapi import jenkins
import jenkins
import os
import requests
import urllib3
from io import BytesIO

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JenkinsClient:
    instance = None
    myattrib = ""


    def __new__(cls, url=None, username=None, password=None):
        if not cls.instance:
            cls.instance = super(JenkinsClient, cls).__new__(cls)
            cls.instance.url = url
            cls.instance.username = username
            cls.instance.password = password
            j = jenkins.Jenkins(url, username, password)
            j._session.verify = False
            cls.instance.jenkins = j
            print(f"Jenkins Client created for {url}")
        else:
            print(f"Re-using existant Jenkins Client for {cls.instance.url}")
        return cls.instance
    
    def get_jobs(self):
        names = []
        for job in self.jenkins.get_jobs():
            names.append(job['name'])
        return names
    
    def get_job_info(self, job_name):
        return self.jenkins.get_job_config(job_name)

    def getJenkinsClient():
        return JenkinsClient()

    def run_job(self, job_name, params):
        queue_number = self.jenkins.build_job(job_name, parameters=params)
        queue_item = self.jenkins.get_queue_item(queue_number)
        if queue_item and queue_item.get('executable', {}).get('url', None):
            build_url = queue_item['executable']['url']
            msg = f"{job_name} triggered. Build URL: {build_url}"
        else:
            build_url = None
            msg = f"{job_name} waiting to be scheduled. Queue number: {queue_number}"
        return msg

    def run_job_with_file_param(self, job_name, params, file_param_name="EXTERNAL_KUBECONFIG_FILE"):
        """
        Trigger a Jenkins job that has a File Parameter.
        """
        # Build URL for the job
        build_url = f"{self.url}/job/{job_name.replace('/', '/job/')}/buildWithParameters"
        
        # Prepare multipart form data
        files = {}
        data = {}
        
        for key, value in params.items():
            data[key] = str(value)
        
        # Add empty file for the file parameter
        files[file_param_name] = ('', BytesIO(b''), 'application/octet-stream')
        
        # Make the request with auth
        response = requests.post(
            build_url,
            data=data,
            files=files,
            auth=(self.username, self.password),
            verify=False,
        )
        
        if response.status_code == 201:
            # Job was queued successfully
            queue_url = response.headers.get('Location', '')
            if queue_url:
                # Extract queue number and get build info
                queue_number = int(queue_url.rstrip('/').split('/')[-1])
                queue_item = self.jenkins.get_queue_item(queue_number)
                if queue_item and queue_item.get('executable', {}).get('url', None):
                    build_url = queue_item['executable']['url']
                    msg = f"{job_name} triggered. Build URL: {build_url}"
                else:
                    msg = f"{job_name} waiting to be scheduled. Queue number: {queue_number}"
            else:
                msg = f"{job_name} triggered successfully."
            return msg
        else:
            raise Exception(f"Failed to trigger job: {response.status_code} - {response.text}")

