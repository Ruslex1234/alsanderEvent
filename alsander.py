from operator import itemgetter
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import json
import re
import unicodedata
import asyncio
import aiohttp
import os
import time
import boto3
# To work with the .env file

html=""

whole_list = {}
total = {}
main = {}
maker = {}
filename = "/root/projects/alsander/tornamento.txt"

url ="https://api.tibiadata.com/v3/guild/{}"
guilds = ['true bastex']

guilds_web = []
for each in guilds:
    guilds_web.append(each.replace(" ","+"))

results = []    

start = time.time()

response = requests.get(url.format(each)).json()

def get_two_hundred(json_data,types):
	if types == 'guild':
		temp_list=[]
		for each in json_data['guilds']['guild']['members']:
			if each['level'] > 199:
				temp_list.append([each['name'],each['vocation']])
		return temp_list
	elif types == 'highscore':
		temp_list=[]
		for each in json_data['highscores']['highscore_list']:
			if each['level'] > 199:
				temp_list.append([each['name'],each['value']])
		return temp_list

def send_file_s3(data):
	bucket_name = "jokindude"
	file_name = "tournamento.html"
	my_acl = "public-read"
	content_type = "text/html"
	s3 = boto3.resource('s3')
	object = s3.Object(bucket_name,file_name)
	object.put(Body=data, ACL=my_acl, ContentType=content_type)

def write_to_file(data):
	tmpfile = open(filename,"w")
	tmpfile.write(json.dumps(data))
	tmpfile.close()

def data_from_file(filename):
	tmpfile = open(filename)
	data = json.load(tmpfile)
	tmpfile.close()
	return data

def get_highscore(world, category, vocation):
	full_highscore={}
	highscore_url = "https://api.tibiadata.com/v3/highscores/{}/{}/{}/{}"
	#for each in range(1,2):
	for each in range(1,21):
		results = requests.get(highscore_url.format(world,category,vocation,each)).json()
		for each in results['highscores']['highscore_list']:
			if each['level'] > 180:
				full_highscore[each['name']] = [each['name'],each['level'],each['value']]
				#full_highscore[each['name']] = {'name': each['name'],'level': each['level'],'experience': each['value']}
	return full_highscore

def divide_chunks(l, n):
        for i in range(0, len(l), n): 
            yield l[i:i + n]

def get_highscore_bs4(world, vocation):	
	full_highscore={}
	profession=0
	cat=6
	match vocation:
		case "druids": profession=5
		case "knights": profession=2
		case "sorcerers": profession=4
		case "paladins": profession=3
	highscore_url = "https://www.tibia.com/community/?subtopic=highscores&world={}&beprotection=-1&category={}&profession={}&currentpage={}"
	#for each in range(1,2):
	for each in range(1,21):
		fixed_url=highscore_url.format(world,cat,profession,each)
		test = requests.get(fixed_url)
		html_content = test.text
		soup = BeautifulSoup(html_content, "lxml").get_text(separator= '\n')
		text =  re.search("Level\nPoints(.|\n)*» Pages",soup).group(0).splitlines()
		#remove the first 2 lines and the last 3
		new_text = text[2:-3]
		x = list(divide_chunks(new_text, 6))
		for each in x:
			full_highscore[each[1]] = each[5]
	return full_highscore

def categorize(dictionary):
	categorized = {}
	categorized[400] = []
	categorized[600] = []
	categorized[2000] = []
	for key, each in dictionary.items():
		if each[1] >599:
			categorized[2000].append(each)
		elif each[1] > 399:
			categorized[600].append(each)
		else:
			categorized[400].append(each)
	return categorized

def sorting(dictionary):
	sorted_dict = {}
	sorted_dict[400] = []
	sorted_dict[600] = []
	sorted_dict[2000] = []
	for key, values in dictionary.items():
		some_list =sorted(values, key=itemgetter(2), reverse=True)
		sorted_dict[key] = some_list
	return sorted_dict

def compare(filedict,newdatadict):
	new_dict = {}
	# key = level category, values = a list of list of characters
	for key, values in filedict.items():
		for eachline in values:
			if eachline[0] in newdatadict:
				#print("newdatadict",newdatadict)
				new_exp = newdatadict[eachline[0]][2] - eachline[2]
				#print("new_exp",new_exp)
				new_dict[eachline[0]] = [eachline[0],newdatadict[eachline[0]][1],new_exp]
	return new_dict

test ={}
#vocations = ["druids"]
vocations = ["druids","knights","paladins","sorcerers"]
for each in vocations:
	test = {**get_highscore('Mykera','experience',each), **test}
#qualified list contains [[Rodney,Elder Druid]]
#print(test)
#test contains {Rodney = [Name,Level,Experience]}
qualified_list = get_two_hundred(response,"guild")
unsorted_dict = {}
for nameVocation in qualified_list:
	if nameVocation[0] in test:
		#print("test[nameVocation[0]]", test[nameVocation[0]])
		unsorted_dict[test[nameVocation[0]][0]] = test[nameVocation[0]]
		
if os.path.exists(filename):
	unsorted_dict = compare(data_from_file(filename),test)
	#print(unsorted_dict)
		
one_time_categorized = categorize(unsorted_dict)
final_product = sorting(one_time_categorized)
#for key,values in final_product.items():
#	print(key, values)

html+="<!DOCTYPE html><html>"
html+='<head>'
html+='<meta http-equiv="refresh" content="3600">'
html+='<style>body {color: #eee;background-color:#2f3136;}a{color: #1CB0F4;} h1, h2, h3 { margin: 0; }</style>'
html+='</head>'
html+="<body>"
html+="<center><h1>Evento de Mykera</h1></center>"
now = datetime.now()
html+=" <center><h4>Last Updated: "+now.strftime("%m/%d/%Y %H:%M:%S")+"</h4></center>\n"
html+='<table style="border:1px solid black; margin-left:auto;margin-right:auto;"><tr>'
for key, values in final_product.items():
	#print("values",values)
	#html+='<td style="width: 300px; vertical-align:top">\n'
	html+='<td style="vertical-align:top">\n'
	#html+="============================\n"
	html+="<center><h2>"+str(key)+"</h2></center>\n"
	html+="<p line-height: 0.2>\n"
	#html+="============================<br>"
	html+="<table>"
	color = "white"
	color2= "white"
	player = ""
	if not os.path.exists(filename):
		for member in values:
			player = member[0]
			html+='<tr><td><font color="'+color+'">['+str(member[1])+']</font></td><td><a href="https://www.tibia.com/community/?name='+member[0]+'" target="_blank" rel="noopener noreferrer"> '+player+'</a></td></tr>'
	else:
		for member in values:
			player = member[0]
			# we can color green when they reach required EXP for the month
			print(player)
			if member[2] > 170000000 and member[1] <400:
				color2 = "#5DE23C"
			elif member[2] > 320000000 and member[1] <600:
				color2 = "#5DE23C"
			elif member[2] > 400000000 and member[1] >599:
				color2 = "#5DE23C"
			else:
				color2 = "white"
			html+='<tr><td><font color="'+color+'">['+str(member[1])+']</font></td><td><a href="https://www.tibia.com/community/?name='+member[0]+'" target="_blank" rel="noopener noreferrer"> '+player+'</a> <font color="'+color2+'">'+str(member[2])+'</font></td></tr>'
	html+="</table></p></td>"
html+="</tr></table>"
html+="<center>=====================================</center>"
html+="<center>=====================================</center>"
html+="</body>"
html+="</html>"
if not os.path.exists(filename):
	print("writing new file locally")
	write_to_file(final_product)	
	print("wrote new file locally")
print("sending file to html page")
send_file_s3(html)
print("sent file to html page")
#send_file_s3(json.dumps(file_content))
#categorized_dict=sort_and_categorize(unsorted_dict)
#send_file_s3(sorted_dict)





end = time.time()
total_time = end - start
print("It took {} seconds to make {} API calls".format(total_time, len(guilds)))
print('You did it!')

