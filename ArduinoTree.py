#Reference https://gist.github.com/astrauka/c0c0c4269e5d94ca6b7090c84fa48cf6

import sublime
import sublime_plugin
import json
import subprocess
import os
import sys
import shutil
import threading
import sys


sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import cache_generate

from Default.exec import ExecCommand

cache_path = os.path.join(sublime.cache_path(), "ArduinoTree")
cache_file = os.path.join(cache_path, "cache.json")

boards_list = None
cache_read = None
if(os.path.exists(cache_file)):
	cache_read = open(cache_file,'r')
	boards_list = json.load(cache_read)


class settingspkg:
	last_tab = 0
	context = []

	address = ""
	write_count = 0
	fqbn = ""
	options = {}

	def __init__(self):
		self.context.append({"tab_id":-1,"fqbn":"","address":"","x_indx":"","y_indx":"","options":{}})
		super(settingspkg, self).__init__()

	def clear_platform_options(self):
		contxt = self.get_context()
		contxt['fqbn'] = ""
		contxt['options'].clear()

	def set_option(self,option,value):
		contxt = self.get_context()
		contxt['options'][option] = value

	def get_option(self,option):
		contxt = self.get_context()
		if option in contxt['options']:
			return contxt['options'][option]
		else:
			return None

	def set_fqbn(self,fqbn):
		contxt = self.get_context()
		contxt['fqbn'] = fqbn

	def get_fqbn(self):
		contxt = self.get_context()
		return contxt['fqbn']

	def set_address(self,address):
		contxt = self.get_context()
		contxt['address'] = address

	def get_address(self):
		contxt = self.get_context()
		return contxt['address']

	def all_option(self):
		contxt = self.get_context()
		return contxt['options']

	def get_context(self):
		for x in range(0,len(self.context)) :
			if 'tab_id' in self.context[x]:
				if self.context[x]['tab_id'] == self.last_tab:
					return self.context[x]

		return self.context[0]

	def set_indxy(self,x_indx,y_indx):
		contxt = self.get_context()
		contxt['x_indx'] = x_indx
		contxt['y_indx'] = y_indx

	def add_tab(self ,tab_id):
		for x in self.context:
			if 'tab_id' in x:
				if x['tab_id'] == tab_id:
					return x

		self.context.append({"tab_id":tab_id,"fqbn":"","address":"","options":{}})
		return self.context[-1]
		

	def del_tab(self,tab_id):
		for x in range(0,len(self.context)):
			if 'tab_id' in self.context[x]:
				if self.context[x]['tab_id'] == tab_id:
					del self.context[x]
		

settings_arduinotree = settingspkg()

def run_arduinocli(args,cache=True):
	args.append('--format')
	args.append('json') 
	ary = ['arduino-cli'] 
	ary.extend(args) 

	result = subprocess.run( ary, stdout=subprocess.PIPE,shell=True).stdout.decode('utf-8')
	return json.loads(result)



def file_name(file_name):
	return os.path.split(file_name)[0]


class createsub_menu:
	menu_main = []

	def __init__(self):
		super(createsub_menu, self).__init__()
		self.menu_main = [{
			"mnemonic": "A",
			"caption": "ArduinoTree",
			"id": "arduinotree",
			"children": [{
					"caption": "Platform",
					"children":  [{"caption": "None","command":"arduinotree_nocommand"}]
				},
				{
					"caption": "Platform Option",
					"children": [{"caption": "None","command":"arduinotree_nocommand"}]
				},
				{
					"caption": "-"
				},{
					"caption": "Port",
					"children": [{"caption": "None","command":"arduinotree_nocommand"}]
				},{
					"caption": "Refresh Ports",
					"command":"arduinotree_refresh"
				},{
					"caption": "-"
				},{
					"caption": "Upload",
					"command":"arduinotree_compile",
					"args":{"kill":False,"mode":1}
				},{
					"caption": "Upload using Programmer",
					"command":"arduinotree_uploadprg"
				},{
					"caption": "Compile",
					"command": "arduinotree_compile",
					"args":{"kill":False,"mode":0}
				},{
					"caption": "Export Binaries",
					"command": "arduinotree_compile",
					"args":{"kill":False,"mode":2}
				},{
					"caption": "Cancel Operation",
					"command": "arduinotree_compile",
					"id":"arduinotree_cancel",
					"args":{"kill":True,"mode":0},
					"is_enabled":"is_enabled"
				},
				{
					"caption": "-"
				},{
					"caption": "Serial Monitor",
					"command": "arduinotree_serial"
				},{
					"caption": "Refresh Cache",
					"command": "arduinotree_cacherefresh"
				}]
		}] 

	def add_platform_options(self,x_indx,y_indx,mode = True):
		global settings_arduinotree
		global boards_list

		if mode:
			settings_arduinotree.clear_platform_options()

		#boards_details = run_arduinocli(['board','details','-b',fqbn,'-f']) 
		board_config = boards_list[x_indx]["details"][y_indx]
		if "config_options" in board_config:
			config_options = board_config["config_options"]
			platform_options = []
			for x in config_options:
				option_label = x["option_label"]
				options_avail = {"caption":option_label,"children":[]}
				for y in x["values"]:
					value_label = y["value_label"]

					if mode:

						if "selected" in y :
							checkbox = str(y["selected"]).lower()
							settings_arduinotree.set_option(x["option"], y["value"])
						else:
							checkbox = False
					else:
						if y["value"] == settings_arduinotree.get_option(x["option"]):
							checkbox = True
						else:
							checkbox = False

					options_avail["children"].append({"caption":value_label,"command":"arduinotree_setplatformoptions","args":{"option":x["option"],"value":y["value"]},"checkbox":checkbox})

				platform_options.append(options_avail)
		else:
			platform_options = [{"caption": "None","command":"arduinotree_nocommand"}]

		self.menu_main[0]["children"][1]["children"][:] = platform_options
		self.write()



	def add_platform(self):
		global boards_list

		index_platform = 0
		self.menu_main[0]["children"][index_platform]["children"].clear()
		sublime.status_message('%03.2f %%' % 20)
		#boards_list = run_arduinocli(['core','search']) 
		board_names = []

		if(os.path.exists(cache_file)):
			for x in range(0,len(boards_list)):
				board_values = {"caption":boards_list[x]["category_name"],"children":[]}
				for y in range(0,len(boards_list[x]["details"])):
					if "fqbn" in boards_list[x]["details"][y]:
						board_values["children"].append( {
							"caption" : json.dumps(boards_list[x]["details"][y]["name"])[1:-1],
							"command":"arduinotree_setplatform",
							"args":{"x_indx":x,'y_indx':y,'fqbn':boards_list[x]["details"][y]["fqbn"]},
							"checkbox":"false"
							})

				if(len(board_values["children"])>0):
					board_names.append(board_values)


			self.menu_main[0]["children"][0]["children"][:] = board_names
			self.write()
		
		else:
			sublime.run_command('arduinotree_cacherefresh')





	def add_ports(self):
		sublime.status_message('%03.2f %%' % 50)
		t1 = threading.Thread(target=self.thread_ports)
		t1.start();

	def thread_ports(self):
		boards_list = run_arduinocli(['board','list'],False)
		index_port = 3
		self.menu_main[0]["children"][index_port]["children"].clear()

		if(len(boards_list) == 0):
			boards_list.append({"caption": "None","command":"arduinotree_nocommand"})
			sublime.status_message('No Ports Found')
		else:
			sublime.status_message(str(len(boards_list)) + ' Ports Found')


		for x in boards_list:
			#change index here if rearranging stuff
			self.menu_main[0]["children"][index_port]["children"].append(
				{
				"caption":x["port"]["address"] +"(" +x["port"]["label"] +")",
				"command":"arduinotree_comport",
				"args":{"address":x["port"]["address"]},
				"checkbox": "false"
				}) 

		self.write()


	def writeMain(self):
		script_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Main.sublime-menu")
		with open(script_file, "w+") as cache:
			cache.write(sublime.encode_value(self.menu_main))


	def write(self):
		os.makedirs(cache_path, exist_ok=True)
		script_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Main.sublime-menu") 

		#doing this bcuz of some strange bug in sublime build 4126 
		if(os.path.exists(script_file)):
			shutil.move(script_file, os.path.join(os.path.dirname(os.path.realpath(__file__)), "Main.sublime-menu.backup") )
			


		# write the context menu item to the cache path
		if(os.path.exists(os.path.join(cache_path, "Main.sublime-menu"))):
			os.remove(os.path.join(cache_path, "Main.sublime-menu"))
		
		with open(os.path.join(cache_path, "Main.sublime-menu"), "w+") as cache:
			cache.write(sublime.encode_value(self.menu_main))


menu_arduinotree = createsub_menu()

def plugin_loaded():
	global menu_arduinotree

	menu_arduinotree.writeMain()

	if(os.path.exists(os.path.join(cache_path, "Main.sublime-menu"))):
		os.remove(os.path.join(cache_path, "Main.sublime-menu"))


	script_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Main.sublime-menu.backup") 
	if(os.path.exists(script_file)):
		shutil.move(script_file ,os.path.join(os.path.dirname(os.path.realpath(__file__)), "Main.sublime-menu") )


	menu_arduinotree.add_platform()

class arduinotree_cacherefresh(sublime_plugin.WindowCommand):
	def run(self):
		global cache_file
		script_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Main.sublime-menu.backup") 
		f = open(cache_file,"w")
		t1 = threading.Thread(target=cache_generate.generate_cache,args=(f,))
		t1.start();


class arduinotree_comport(sublime_plugin.WindowCommand):
	def run(self, address):
		global settings_arduinotree
		settings_arduinotree.set_address(address)

	def is_checked(self,address):
		global settings_arduinotree
		if address == settings_arduinotree.get_address():
			return True
		else:
			return False
		

class arduinotree_refresh(sublime_plugin.WindowCommand):
	def run(self, length=8):
		global menu_arduinotree
		menu_arduinotree.add_ports()

class arduinotree_setplatform(sublime_plugin.WindowCommand):
	def run(self, x_indx,y_indx,fqbn):
		global settings_arduinotree

		menu_arduinotree.add_platform_options(x_indx,y_indx)
		settings_arduinotree.set_fqbn(fqbn)


	def is_checked(self,x_indx,y_indx,fqbn):
		global settings_arduinotree

		if fqbn == settings_arduinotree.get_fqbn():
			return True
		else:
			return False

class arduinotree_setplatformoptions(sublime_plugin.WindowCommand):
	def run(self, option,value):
		global settings_arduinotree
		settings_arduinotree.set_option(option,value)

	def is_checked(self, option,value):
		global settings_arduinotree

		if value == settings_arduinotree.get_option(option):
			return True
		else:
			return False


class arduinotree_compile(ExecCommand):
	encoding = 'utf-8'

	#0 - compile
	#1 - upload
	#2 - export
	def run(self, kill=False,mode=0,working_dir="",**kwargs):
		global settings_arduinotree

		if kill :
			if self.proc :
				self.killed = True
				self.proc.kill()
			return

		fqbn = settings_arduinotree.get_fqbn()
		address = settings_arduinotree.get_address()
		compile_tags = ""
		for key, value in settings_arduinotree.all_option().items():
			compile_tags += key +"="+value +","

		#current_file = self.view.window().active_view().file_name()
		vars = self.window.extract_variables()
		working_dir = vars['file_path']

		if mode == 0:
			execution_args = ['arduino-cli','compile','-b',fqbn,'--board-options',compile_tags[:-1],working_dir,'--no-color','-v']
		elif mode == 1:
			#compile before uploading
			args_used = {"kill":kill,"mode":0,"working_dir":working_dir}
			args_used.update(kwargs)
			self.window.run_command('arduinotree_compile',args=args_used)

			execution_args = ['arduino-cli','upload','-b',fqbn,'--board-options',compile_tags[:-1],'-p',address,working_dir,'--no-color','-v']
		elif mode == 2:
			execution_args = ['arduino-cli','compile','-b',fqbn,'--board-options',compile_tags[:-1],'-p',address,working_dir,'--no-color','-e','-v']

		kwargs["cmd"] = execution_args
		#kwargs = sublime.expand_variables(kwargs, variables)
		super().run(**kwargs)

class tabListener(sublime_plugin.ViewEventListener):
	def on_load(self):
		global settings_arduinotree
		file = self.view.file_name()
		if file:
			if (os.path.split(file)[1])[-4:] == ".ino":
				settings_arduinotree.add_tab(self.view.id())


	def on_close(self):
		settings_arduinotree.del_tab(self.view.id())

	def on_activated(self):
		global settings_arduinotree
		file = self.view.file_name()
		if file:
			if (os.path.split(file)[1])[-4:] == ".ino":
				settings_arduinotree.add_tab(self.view.id())
				settings_arduinotree.last_tab = self.view.id()
				contxt = settings_arduinotree.get_context()
				if contxt:
					if contxt['fqbn'] != "":
						menu_arduinotree.add_platform_options(contxt["x_indx"],contxt["y_indx"],contxt['fqbn'],False)
		

class ArduinoTreeCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.insert(edit, 0, "Hello, World!")
