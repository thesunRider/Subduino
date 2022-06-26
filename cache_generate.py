
import subprocess
import json
from threading import Thread
import queue
from time import sleep
import sublime
import logging
logging.basicConfig(level=logging.INFO)

def run_arduinocli(args):
	args.append('--format')
	args.append('json') 
	ary = ['arduino-cli'] 
	ary.extend(args) 

	result = subprocess.run( ary, stdout=subprocess.PIPE,shell=True).stdout.decode('utf-8')
	return json.loads(result)

def get_board_details(y,result,q):
	boards_details = {}
	board_info = {"fqbn":None,"name":None,"config_options":None}
	if "fqbn" in y:
		board_info["fqbn"] = y["fqbn"]
		board_info["name"] = json.dumps(y["name"])[1:-1]

		boards_details = run_arduinocli(['board','details','-b',board_info["fqbn"] ,'-f']) 

		if "config_options" in boards_details:
			board_info["config_options"] = boards_details["config_options"]

	result.extend([board_info])
	q.put(1)


def generate_cache(file):
	global menu_arduinotree

	q = queue.Queue()
	sublime.status_message('Generating Cache %03.2f %%' % 0) 

	boards_list = run_arduinocli(['core','search']) 
	sublime.status_message('Generating Cache %03.2f %%' % 10) 

	boards_info_list = []

	thread_array = []
	no_of_processes = 0
	for a in range(0,len(boards_list)):
		x = boards_list[a]
		category_name = x["name"]
		boards_info_list.append({"category_name":category_name,"details":[]})
		atleast_one_fqbn_found = False #if atleast one fqbn found push this to array

		for b in range(0,len(x["boards"])):
			thread_array.append(Thread(target=get_board_details, args=((x["boards"])[b],boards_info_list[-1]["details"],q,)))
			no_of_processes += 1
			thread_array[-1].start()

		#if atleast_one_fqbn_found:
		#	board_gen.append({"category_name":category_name,"boards":boards_info_list})
	

	sublime.status_message('Generating Cache %03.2f %%' % 20) 
	while True:
		if q.qsize() == no_of_processes:
			break;

		sleep(0.2)
		sublime.status_message('Generating Cache %03.2f %% (This may take some time ... )' % (20 + 70*q.qsize()/no_of_processes) )
		last_progress = q.qsize()/no_of_processes

	for t in thread_array:
		t.join()

	sublime.status_message('Generating Cache %03.2f %%' % 95) 

	main_pop_list =[]


	#process the details
	for x in range(0,len(boards_info_list)):
		fqbn_found = False
		pop_list  = []
		for y in range(0,len(boards_info_list[x]["details"])):
			if (boards_info_list[x]["details"][y]["fqbn"] == None):
				pop_list.append(y)

		#pop no fqbn devices
		for y in sorted(pop_list, reverse=True):
			boards_info_list[x]["details"].pop(y)

		if (len(boards_info_list[x]["details"]) == 0 ):
			main_pop_list.append(x)

	sublime.status_message('Generating Cache %03.2f %%' % 97) 

	#pop no fqbn devices
	for x in sorted(main_pop_list, reverse=True):
		boards_info_list.pop(x)

	#sort the data
	for x in range(0,len(boards_info_list)):
		if len(boards_info_list[x]["details"]) > 0:
			boards_info_list[x]["details"].sort(key = lambda json: json["name"], reverse=True)

	boards_info_list.sort(key = lambda json: json["category_name"], reverse=True)


	sublime.status_message('Generating Cache %03.2f %%' % 99 ) 
	json.dump(boards_info_list,file)

	sublime.status_message('Cache Generated') 
