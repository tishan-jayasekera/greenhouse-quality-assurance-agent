import os
import asana
token = "2/1211018402725019/1213427130249306:fac88adf082e6280a30f39694668c026"
task_gid = "1213184162194851"
try:
    client = asana.Client.access_token(token)
    client.headers = {"asana-enable": "new_memberships,new_goal_memberships"}
    res = client.tasks.add_comment(task_gid, {"text": "Test comment from agent"})
    print("SUCCESS", res)
except Exception as e:
    print("FAILED", type(e).__name__, str(e))
