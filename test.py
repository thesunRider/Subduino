import json
import subprocess
import os

result = subprocess.run( ['arduino-cli','lib','list','--all','--format','json'], stdout=subprocess.PIPE,shell=True).stdout.decode('utf-8')
result = json.loads(result)

keywords = []
for  x in result:
	if "install_dir" in x["library"]:
		if os.path.exists(os.path.join(x["library"]["install_dir"],"keywords.txt")):
			print("YES" ,os.path.join(x["library"]["install_dir"],"keywords.txt"))
			
