from __future__ import print_function
import ctypes, sys
import os
import time
import win32api
import win32con
import win32gui
import threading

from midi.midifiles.midifiles import MidiFile
from midi.helpers import tuner

letter = {'0': 48, '1': 49, '2': 50, '3': 51, '4': 52, '5': 53, '6': 54, '7': 55, '8': 56, '9': 57, 'a': 65, 'b': 66, 'c': 67, 'd': 68, 'e': 69, 'f': 70, 'g': 71, 'h': 72, 'i': 73, 'j': 74, 'k': 75, 'l': 76, 'm': 77, 'n': 78, 'o': 79, 'p': 80, 'q': 81, 'r': 82, 's': 83, 't': 84, 'u': 85, 'v': 86, 'w': 87, 'x': 88, 'y': 89, 'z': 90, ',': 188, '.': 190, '/': 191, ';': 186, 'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117, 'F7': 118, 'F8': 119, 'F9': 120, 'F10': 121, 'b0': 96, 'b.': 110, 'b2': 98, 'b3': 99, 'b5': 101, 'b6': 102, 'b8': 104, 'b9': 105, 'b/': 111, 'b*': 106}
mapping = {'36': 'z', '37': ',', '38': 'x', '39': '.', '40': 'c', '41': 'v', '42': '/', '43': 'b', '44': 'b0', '45': 'n', '46': 'b.', '47': 'm', '48': 'a', '49': 'k', '50': 's', '51': 'l', '52': 'd', '53': 'f', '54': ';', '55': 'g', '56': 'b2', '57': 'h', '58': 'b3', '59': 'j', '60': 'q', '61': 'i', '62': 'w', '63': 'o', '64': 'e', '65': 'r', '66': 'p', '67': 't', '68': 'b5', '69': 'y', '70': 'b6', '71': 'u', '72': '1', '73': '8', '74': '2', '75': '9', '76': '3', '77': '4', '78': '0', '79': '5', '80': 'b8', '81': '6', '82': 'b9', '83': '7', '84': 'F1', '85': 'F8', '86': 'F2', '87': 'F9', '88': 'F3', '89': 'F4', '90': 'F10', '91': 'F5', '92': 'b/', '93': 'F6', '94': 'b*', '95': 'F7'}

def dinput():
	a = {}
	count = 36
	while count <= 84:
		a[str(count)] = int(input())
		count += 1
	return a

def find(arr, time):
	result = []
	for i in arr:
		if i["time"] == time:
			result.append(i["note"])
	return result

def press(note):#48 83
	if note in mapping.keys():
		win32api.keybd_event(letter[mapping[note]], 0, 0, 0)
		#print("Press: ", letter[mapping[note]])
	return

def unpress(note):#48 83
	if note in mapping.keys():
		win32api.keybd_event(letter[mapping[note]], 0, win32con.KEYEVENTF_KEYUP, 0)
	return

def make_map():
	s = "zxcvbnmasdfghjqwertyu"
	for i, k in enumerate(mapping.keys()):
		mapping[k] = s[i]
	print(mapping)

def pop_window(name):
	handle = win32gui.FindWindow(0, name)
	if handle == 0:
		return False
	else:
		win32gui.SendMessage(handle, win32con.WM_SYSCOMMAND,
								win32con.SC_RESTORE, 0)
		win32gui.SetForegroundWindow(handle)
		while (win32gui.IsIconic(handle)):
			continue
		return True

def watch_dog(name):
	while True:
		if win32gui.GetWindowText(win32gui.GetForegroundWindow())!=name:
			os._exit(0)

def is_admin():
	try:
		return ctypes.windll.shell32.IsUserAnAdmin()
	except:
		return False
if is_admin():
	pass
else:
	ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
	exit(0)

song_list = os.listdir("./songs/")
for song_count in range(0,len(song_list)):
	print(str(song_count) + "：" + song_list[song_count])

midi_file = song_list[int(input("输入您要弹奏的midi编号并按回车："))][:-4]
print("您将要弹奏的是：" + midi_file)

try:
	midi_object = MidiFile("./songs/" + midi_file + ".mid")
except:
	print("文件损坏或不存在。")
	quit()
tick_accuracy = 0
print("尝试计算播放速度......")
try:
	flag = False
	for i in midi_object.tracks:
		for j in i :
			if j.dict()["type"] == "set_tempo":
				flag = True
				tempo = j.tempo
				break
		if flag:
			break
	bpm = 60000000 / tempo
	tick_accuracy = bpm / 3		#这里可以手动修改播放速度，除数越大曲速越慢
	print("计算成功。")
except:
	tick_accuracy = int(input("计算失败，请检查文件是否完整，或者手动输入播放速度：（7）"))
type = ['note_on','note_off']
tracks = []
end_track = []
print("开始读取音轨。")
for i,track in enumerate(midi_object.tracks):
	print(f'track{i}')
	last_time = 0
	last_on = 0
	for msg in track:
		info = msg.dict()
		info['pertime'] = info['time']
		info['time'] += last_time
		last_time = info['time']
		if (info['type'] in type):
			del info['channel']
			del info['velocity']
			info['time'] = round(info['time'] / tick_accuracy)
			if info['type'] == 'note_on':
				del info['type']
				del info['pertime']
				last_on = info['time']
				tracks.append(info)
			else:
				del info['type']
				del info['pertime']
				last_on = info['time']
				end_track.append(info)
mmax = 0
for i in tracks:
	mmax = max(mmax, i['time'] + 1)
start = {}
print("开始转换乐谱...")
for i in range(mmax):
	start[str(i)] = find(tracks, i)

stime = int(input("沉睡时间（秒）："))
print("播放将于" + str(stime) + "秒后开始，请做好准备。")
time.sleep(stime) 

for i in range(mmax):
	if i != 0:
		for note in start[str(i - 1)]:
			unpress(str(note))
	for note in start[str(i)]:
		press(str(note))
	time.sleep(0.025)
print("播放结束。")
