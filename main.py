import subprocess
import sys

print("Install required pachages...")
subprocess.call(["pip", "install", "--index-url", "http://10.17.52.41:8081/repository/pypi-proxy/simple", "--trusted-host","10.17.52.41", "-r","requirements.txt" ])

import gitlab
import json
import requests
import argparse
import distutils

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

parser = argparse.ArgumentParser()
parser.add_argument('-u','--url',dest='gitlab_url', type=str, help='URL of the gitlab site')
parser.add_argument('-t','--token',dest='token', type=str, help='Private token with administrator access to gitlab site.')
parser.add_argument('-o','--output',dest='show_output', type=lambda x:bool(distutils.util.strtobool(x.strip())), help='Show the output on the standard ouput (True, False(Default)).', default=False)
args = parser.parse_args()
if not args.gitlab_url:
    print("Please provide the gitlab's URL!")
    sys.exit(0)
else:
    gitlab_url = args.gitlab_url.strip()

if not args.token:
    print("Please provide your token in order to access the gitlab site")
    sys.exit(0)
else:
    token = args.token.strip()

show_output=args.show_output

access_level={50:'Owner',40:'Maintainer',30:'Developer',20:'Reporter',10:'Guest'}
gl = gitlab.Gitlab(gitlab_url, private_token=token, ssl_verify=False)
git_projects = gl.projects.list(iterator=True)
output_log = 'users.log'

mydic={}
members={}
groups={}
refined_members={}
print("Calculating the users and their permissions for projects....")
for git_project in git_projects:
    
    project_full_name = git_project.__getattr__('name_with_namespace')
    members[project_full_name] = git_project.members.list(iterator=True)._list._data
    groups[project_full_name] = git_project.groups.list(iterator=True)._list._data

    for group in groups[project_full_name]:
        group_url = gl.api_url+gl.groups.get(group['id']).members._computed_path
        response = requests.get(group_url,headers={'Authorization': 'Bearer {}'.format(token)},verify=False)
        parsed = response.json()
        members[project_full_name].append([{group['name']:parsed}])
    
    refined_members[project_full_name]={}
    membership=[]
    for mems in members[project_full_name]:
        if isinstance(mems, dict):
            membership.append([{mems['name']:access_level[mems['access_level']]}])
        else:
            for single_group in mems:
                for _,all_users in single_group.items():
                    for single_user in all_users:
                        membership.append([{single_user['name']:access_level[single_user['access_level']]}]) 

    refined_members[project_full_name]=membership
        
        
    # print(project_full_name)
    # members_url = git_project.attributes['_links']['members']
    # response = requests.get(members_url,headers={'Authorization': 'Bearer {}'.format(token)},verify=False)
    # parsed = response.json()
    # for user in parsed:
    #     find_it=False
    #     for theuser,_ in mydic.items():
    #         if theuser == user['username']:
    #             find_it=True
    #             break
    #     if find_it:
    #         mydic[user['username']]["project"] += [{project_full_name : user["access_level"]}]
    #     else:
    #         mydic[user['username']]={"name": user['name'], "project":[{project_full_name : user["access_level"]}]}

with open(output_log,'w') as thefile:
    for project,members in refined_members.items():
        thefile.writelines(str(project))
        thefile.writelines("\n")
        thefile.writelines(str(members))
        thefile.writelines("\n\n\n")
        if show_output:
            print(str(project))
            print("\n")
            print(str(members))
            print("\n\n")
    print("Check the "+output_log)