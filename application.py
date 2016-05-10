#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide import QtCore, QtGui, QtNetwork	
from PySide.QtCore import *
from PySide.QtGui import *

import sys
import socket
import time
import serial
import glob
import json
import urllib
import os

import design # This file holds our MainWindow and all design related things
			  # it also keeps events etc that we defined in Qt Designer

TCP_IP = '192.168.2.100'
TCP_PORT = 5250

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS # PyInstaller creates a temp folder and stores path in _MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class CasparCGController(QtGui.QMainWindow, design.Ui_MainWindow):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.setupUi(self)  # This is defined in design.py file automatically It sets up layout and widgets that are defined

		######## QSettings #########
		self.qsettings = QSettings(resource_path('settings.ini'), QSettings.IniFormat)
		self.qsettings.setIniCodec("UTF-8")		
		self.qsettings.setFallbacksEnabled(False)
		############################

		self.API_data = None # Holds data loaded from API after data formatting
		self.SERIAL_data = dict(
			home_score = '',
			home_fouls = '',
			away_score = '',
			away_fouls = '',
			quarter = '',
			game_clock = '',
			shot_clock = ''
		) # Holds dict() of serial data (with 0.1)

		self.ipaddress.setText(str(self.qsettings.value("TCP_IP", "192.168.2.100")))
		self.port.setText(str(self.qsettings.value("TCP_PORT", "5250")))
		self.game_key.setText(str(self.qsettings.value("GAME_KEY", "c3225a372e06cf0cf6ec")))

		self.connectCaspar.clicked.connect(self.init_tcpWorker)
		self.TLS.clicked.connect(lambda: self.tcpWorker.TLS())
		self.com_connect.clicked.connect(self.init_SerialWorker)
		self.com_rescan.clicked.connect(self.serial_scan)
		self.load_gamekey.clicked.connect(lambda: self.load_API(True))
		self.ipaddress.textEdited.connect(lambda: self.qsettings.setValue('TCP_IP', self.ipaddress.text()))
		self.port.textEdited.connect(lambda: self.qsettings.setValue('TCP_PORT', self.port.text()))
		self.game_key.textEdited.connect(lambda: self.qsettings.setValue('GAME_KEY', self.game_key.text()))

		self.serial_scan()
		self.load_API(True)
		self.indivstats_handler('LOAD STATISTICS')

		self.commentator_play.clicked.connect(lambda: self.commentator_handler('ADD'))
		self.commentator_stop.clicked.connect(lambda: self.commentator_handler('STOP'))
		self.commentator_update.clicked.connect(lambda: self.commentator_handler('UPDATE'))

		self.official_play.clicked.connect(lambda: self.official_handler('ADD'))
		self.official_stop.clicked.connect(lambda: self.official_handler('STOP'))
		self.official_update.clicked.connect(lambda: self.official_handler('UPDATE'))

		self.standings_play.clicked.connect(lambda: self.standings_handler('ADD'))
		self.standings_stop.clicked.connect(lambda: self.standings_handler('STOP'))
		self.standings_update.clicked.connect(lambda: self.standings_handler('UPDATE'))
		self.standings_ad_in.clicked.connect(lambda: self.standings_handler('AD ON'))
		self.standings_ad_out.clicked.connect(lambda: self.standings_handler('AD OFF'))
		self.standingsTable.currentCellChanged.connect(lambda: self.standings_handler('SAVE QSETTINGS'))
		self.standings_handler('INITIALIZE')

		self.scoreboard_play.clicked.connect(lambda: self.scoreboard_handler('ADD'))
		self.scoreboard_stop.clicked.connect(lambda: self.scoreboard_handler('STOP'))
		self.scoreboard_update.clicked.connect(lambda: self.scoreboard_handler('UPDATE'))
		self.scoreboard_ad_in.clicked.connect(lambda: self.scoreboard_handler('AD ON'))
		self.scoreboard_ad_out.clicked.connect(lambda: self.scoreboard_handler('AD OFF'))

		self.lineup_play.clicked.connect(lambda: self.lineup_handler('ADD'))
		self.lineup_stop.clicked.connect(lambda: self.lineup_handler('STOP'))
		self.lineup_update.clicked.connect(lambda: self.lineup_handler('UPDATE'))
		self.lineup_ad_in.clicked.connect(lambda: self.lineup_handler('AD ON'))
		self.lineup_ad_out.clicked.connect(lambda: self.lineup_handler('AD OFF'))

		self.lineup_play_2.clicked.connect(lambda: self.lineup_2_handler('ADD'))
		self.lineup_stop_2.clicked.connect(lambda: self.lineup_2_handler('STOP'))
		self.lineup_update_2.clicked.connect(lambda: self.lineup_2_handler('UPDATE'))
		self.lineup_ad_in_2.clicked.connect(lambda: self.lineup_2_handler('AD ON'))
		self.lineup_ad_out_2.clicked.connect(lambda: self.lineup_2_handler('AD OFF'))

		self.team_stats_play_2.clicked.connect(lambda: self.team_stats_2_handler('ADD'))
		self.team_stats_stop_2.clicked.connect(lambda: self.team_stats_2_handler('STOP'))
		self.team_stats_update_2.clicked.connect(lambda: self.team_stats_2_handler('UPDATE'))
		self.team_stats_auto_2.clicked.connect(lambda: self.team_stats_2_handler('ADD AUTO'))

		self.team_stats_play.clicked.connect(lambda: self.team_stats_handler('ADD'))
		self.team_stats_stop.clicked.connect(lambda: self.team_stats_handler('STOP'))
		self.team_stats_update.clicked.connect(lambda: self.team_stats_handler('UPDATE'))
		self.team_stats_ad_in.clicked.connect(lambda: self.team_stats_handler('AD ON'))
		self.team_stats_ad_out.clicked.connect(lambda: self.team_stats_handler('AD OFF'))
		self.tabWidget.currentChanged.connect(self.tabWidgetChanged)

		self._pcheckboxes = [self.game_2pt, self.game_3pt, self.game_ft, self.game_pts, self.game_reb, self.game_ast, self.game_stl, self.game_blk, self.game_fouls]
		self._scheckboxes = [self.season_2pt, self.season_3pt, self.season_pts, self.season_ft, self.season_reb, self.season_ast, self.season_stl, self.season_blk, self.season_fouls, self.season_gp, self.season_to, self.season_minutes]
		self._gcheckboxes = [self.gamelog_2pt, self.gamelog_3pt, self.gamelog_ft, self.gamelog_pts, self.gamelog_reb, self.gamelog_ast, self.gamelog_stl, self.gamelog_blk, self.gamelog_fouls, self.gamelog_minutes]
		for checkbox in (self._pcheckboxes + self._scheckboxes + self._gcheckboxes): # When checkboxes are toggled, update data 
			checkbox.toggled.connect(lambda: self.indivstats_handler('AUTOFILL'))

		self.indivstats_play.clicked.connect(lambda: self.indivstats_handler('ADD'))
		self.indivstats_stop.clicked.connect(lambda: self.indivstats_handler('STOP'))
		self.indivstats_update.clicked.connect(lambda: self.indivstats_handler('UPDATE'))
		self.indivstats_ad_in.clicked.connect(lambda: self.indivstats_handler('AD ON'))
		self.indivstats_ad_out.clicked.connect(lambda: self.indivstats_handler('AD OFF'))
		self.indivstats_player.currentIndexChanged.connect(lambda: self.indivstats_handler('LOAD STATISTICS TO VM THEN POPULATE'))
		self.indivstats_season.currentIndexChanged.connect(lambda: self.indivstats_handler('POPULATE SEASON STATISTICS'))
		self.indivstats_gamelogs.currentIndexChanged.connect(lambda: self.indivstats_handler('POPULATE GAMELOG STATISTICS'))
		self.indivstats2_auto.clicked.connect(lambda: self.indivstats2_handler('ADD AUTO'))
		self.indivstats2_play.clicked.connect(lambda: self.indivstats2_handler('ADD'))
		self.indivstats2_stop.clicked.connect(lambda: self.indivstats2_handler('STOP'))
		self.indivstats2_update.clicked.connect(lambda: self.indivstats2_handler('UPDATE'))
		self.indivstats_clear.clicked.connect(lambda: self.indivstats_handler('CLEAR STATISTICS'))
		self.auto_gamelog.toggled.connect(lambda: self.indivstats_handler('AUTOFILL'))
		self.auto_season.toggled.connect(lambda: self.indivstats_handler('AUTOFILL'))
		self.auto_game.toggled.connect(lambda: self.indivstats_handler('AUTOFILL'))
		self.auto_manual.toggled.connect(lambda: self.indivstats_handler('AUTOFILL'))


		self.gp_play.clicked.connect(lambda: self.gp_handler('ADD'))
		self.gp_stop.clicked.connect(lambda: self.gp_handler('STOP'))
		self.gp_update.clicked.connect(lambda: self.gp_handler('UPDATE'))

		self.gp2_play.clicked.connect(lambda: self.gp2_handler('ADD'))
		self.gp2_stop.clicked.connect(lambda: self.gp2_handler('STOP'))
		self.gp2_update.clicked.connect(lambda: self.gp2_handler('UPDATE'))

		self.qbyq_play.clicked.connect(lambda: self.qbyq_handler('ADD'))
		self.qbyq_stop.clicked.connect(lambda: self.qbyq_handler('STOP'))
		self.qbyq_update.clicked.connect(lambda: self.qbyq_handler('UPDATE'))
		self.qbyq_table.currentCellChanged.connect(lambda: self.qbyq_handler('FILL TOTAL'))

		self.score3_play.clicked.connect(lambda: self.score3_handler('ADD'))
		self.score3_stop.clicked.connect(lambda: self.score3_handler('STOP'))
		self.score3_update.clicked.connect(lambda: self.score3_handler('UPDATE'))

		self.score2_play.clicked.connect(lambda: self.score2_handler('ADD'))
		self.score2_stop.clicked.connect(lambda: self.score2_handler('STOP'))
		self.score2_update.clicked.connect(lambda: self.score2_handler('UPDATE'))

		#self.stop_all_except_scoreboard.clicked.connect(lambda: self.stop_all())


	def stat_percentage(self, statistic): # Sample input: '0 - 0', '2 - 10', sample output: '0%', '20%'
		try:
			numerator = float(statistic.split(' - ')[0])
			denominator = float(statistic.split(' - ')[1])
			quotient = (numerator / denominator) * 100
			_ret = str(quotient).split('.')[0] + '%' # return truncated percentage without decimals
			return _ret

		except ZeroDivisionError:
			return '0%'

	def player_by_ID(self, player_id): # Load player dict from API_data if it exists
		for player in (self.API_data['homestats'] + self.API_data['awaystats']):
			if player['player_id'] == player_id:
				return player

	def sendTCP(self, packet): # tcpWorker encapsulation and error handling, catches uninitialized errors
		try:
			self.tcpWorker.send(packet)
		except AttributeError:
			QtGui.QMessageBox.critical(self, "TCP Error", str("CasparCG connection error."), QtGui.QMessageBox.Abort)
		except socket.timeout:
			QtGui.QMessageBox.critical(self, "TCP Error", str("CasparCG connection timeout."), QtGui.QMessageBox.Abort)

	def tabWidgetChanged(self, index): # Called when window of tab widget changes
		if(index == 5 or index == 4):
			self.load_API(False)

	def load_API(self, refreshQObjects): # Load API data in appropriate QObjects
		url = 'http://www.choxue.com/zh-tw/livedash/%s/scoreboard.json' % self.game_key.text().strip()
		self.debug_console.setText(self.debug_console.toPlainText() + '\r\n' + url)
		response = urllib.urlopen(url)
		self.API_data = json.loads(response.read())

		self.API_data['home']['two'] 			+= '   (%s)' % self.stat_percentage(self.API_data['home']['two'])
		self.API_data['home']['trey'] 			+= '   (%s)' % self.stat_percentage(self.API_data['home']['trey'])
		self.API_data['home']['ft'] 			+= '   (%s)' % self.stat_percentage(self.API_data['home']['ft'])
		self.API_data['guest']['two'] 			+= '   (%s)' % self.stat_percentage(self.API_data['guest']['two'])
		self.API_data['guest']['trey'] 			+= '   (%s)' % self.stat_percentage(self.API_data['guest']['trey'])
		self.API_data['guest']['ft'] 			+= '   (%s)' % self.stat_percentage(self.API_data['guest']['ft'])
		self.API_data['home']['logo_src'] 		= 'teams/%s.png' % self.API_data['home']['name']
		self.API_data['guest']['logo_src']		= 'teams/%s.png' % self.API_data['guest']['name']
		self.API_data['home']['reb_tot'] 		= self.API_data['home']['reb_d'] + self.API_data['home']['reb_o']
		self.API_data['guest']['reb_tot'] 		= self.API_data['guest']['reb_d'] + self.API_data['guest']['reb_o']

		for p in self.API_data['homestats']:
			p['team'] = self.API_data['home']['name'] # Add team of player into dataset

		for p in self.API_data['awaystats']:
			p['team'] = self.API_data['guest']['name']

		for p in (self.API_data['homestats'] + self.API_data['awaystats']):
			p['reb_tot'] 		= p['reb_o'] + p['reb_d'] # Add team of player into dataset
			p['points_tot'] 	= (int(p['ft'].split(' - ')[0]) + (int(p['two'].split(' - ')[0]) * 2) + (int(p['trey'].split(' - ')[0]) * 3)) # Add team of player into dataset
			p['headshot_src'] 	= 'players/%s_%s.png' % (str(p['jersey']).encode('utf-8'), p['name'].encode('utf-8'))
			p['two'] 			= '%s (%s)' %(p['two'].replace(' - ', '/') ,self.stat_percentage(p['two']))
			p['trey'] 			= '%s (%s)' %(p['trey'].replace(' - ', '/') ,self.stat_percentage(p['trey']))
			p['ft'] 			= '%s (%s)' %(p['ft'].replace(' - ', '/') ,self.stat_percentage(p['ft']))
			p['logo_src'] 		= 'teams/%s.png' % p['team'].encode('utf-8')


		self.team_stats_table.setItem(0, 0, QTableWidgetItem(str(self.API_data['home']['fouls'])))
		self.team_stats_table.setItem(1, 0, QTableWidgetItem(str(self.API_data['home']['two'])))
		self.team_stats_table.setItem(2, 0, QTableWidgetItem(str(self.API_data['home']['trey'])))
		self.team_stats_table.setItem(3, 0, QTableWidgetItem(str(self.API_data['home']['ft'])))
		self.team_stats_table.setItem(4, 0, QTableWidgetItem(str(self.API_data['home']['reb_d'])))
		self.team_stats_table.setItem(5, 0, QTableWidgetItem(str(self.API_data['home']['reb_o'])))
		self.team_stats_table.setItem(6, 0, QTableWidgetItem(str(self.API_data['home']['reb_tot'])))
		self.team_stats_table.setItem(7, 0, QTableWidgetItem(str(self.API_data['home']['ast'])))
		self.team_stats_table.setItem(8, 0, QTableWidgetItem(str(self.API_data['home']['stl'])))
		self.team_stats_table.setItem(9, 0, QTableWidgetItem(str(self.API_data['home']['blk'])))
		self.team_stats_table.setItem(0, 1, QTableWidgetItem(str(self.API_data['guest']['fouls'])))
		self.team_stats_table.setItem(1, 1, QTableWidgetItem(str(self.API_data['guest']['two'])))
		self.team_stats_table.setItem(2, 1, QTableWidgetItem(str(self.API_data['guest']['trey'])))
		self.team_stats_table.setItem(3, 1, QTableWidgetItem(str(self.API_data['guest']['ft'])))
		self.team_stats_table.setItem(4, 1, QTableWidgetItem(str(self.API_data['guest']['reb_d'])))
		self.team_stats_table.setItem(5, 1, QTableWidgetItem(str(self.API_data['guest']['reb_o'])))
		self.team_stats_table.setItem(6, 1, QTableWidgetItem(str(self.API_data['guest']['reb_tot'])))
		self.team_stats_table.setItem(7, 1, QTableWidgetItem(str(self.API_data['guest']['ast'])))
		self.team_stats_table.setItem(8, 1, QTableWidgetItem(str(self.API_data['guest']['stl'])))
		self.team_stats_table.setItem(9, 1, QTableWidgetItem(str(self.API_data['guest']['blk'])))


		if(not refreshQObjects): # Load data to API_data only, QObject updates must come from BUTTON
			return

		#print json.dumps(self.player_by_ID(1387), sort_keys=True, indent=4)

		_lineup_comboBoxes_home = [self.lineup_player_1, self.lineup_player_2, self.lineup_player_3, self.lineup_player_4, self.lineup_player_5]
		_lineup_comboBoxes_away = [self.lineup_player_6, self.lineup_player_7, self.lineup_player_8, self.lineup_player_9, self.lineup_player_10]

		self.indivstats_player.clear()
		self.lineup_player_1.clear()
		self.lineup_player_2.clear()
		self.lineup_player_3.clear()
		self.lineup_player_4.clear()
		self.lineup_player_5.clear()
		self.lineup_player_6.clear()
		self.lineup_player_7.clear()
		self.lineup_player_8.clear()
		self.lineup_player_9.clear()
		self.lineup_player_10.clear()

		self.home_team.setText(self.API_data['home']['name'])
		self.away_team.setText(self.API_data['guest']['name'])
		self.lineup_title.setText(self.API_data['home']['name'])
		self.lineup_title_2.setText(self.API_data['guest']['name'])
		self.qbyq_home_team.setText(self.API_data['home']['name'])
		self.qbyq_away_team.setText(self.API_data['guest']['name'])
		self.score3_home_team.setText(self.API_data['home']['name'])
		self.score3_away_team.setText(self.API_data['guest']['name'])

		for p in self.API_data['homestats']: # Add to QComboBox
			self.indivstats_player.addItem('%s - #%d %s' % (p['team'], p['jersey'], p['name']), p['player_id'])
			self.lineup_player_1.addItem('#%d %s %d' % (p['jersey'], p['name'], p['player_id']), p['player_id'])
			self.lineup_player_2.addItem('#%d %s %d' % (p['jersey'], p['name'], p['player_id']), p['player_id'])
			self.lineup_player_3.addItem('#%d %s %d' % (p['jersey'], p['name'], p['player_id']), p['player_id'])
			self.lineup_player_4.addItem('#%d %s %d' % (p['jersey'], p['name'], p['player_id']), p['player_id'])
			self.lineup_player_5.addItem('#%d %s %d' % (p['jersey'], p['name'], p['player_id']), p['player_id'])


		for p in self.API_data['awaystats']: # Add to QComboBox
			self.indivstats_player.addItem('%s - #%d %s' % (p['team'], p['jersey'], p['name']), p['player_id'])
			self.lineup_player_6.addItem('#%d %s' % (p['jersey'], p['name']), p['player_id'])
			self.lineup_player_7.addItem('#%d %s' % (p['jersey'], p['name']), p['player_id'])
			self.lineup_player_8.addItem('#%d %s' % (p['jersey'], p['name']), p['player_id'])
			self.lineup_player_9.addItem('#%d %s' % (p['jersey'], p['name']), p['player_id'])
			self.lineup_player_10.addItem('#%d %s' % (p['jersey'], p['name']), p['player_id'])

	def loadPlayerDataToVM(self, player_id):
		url = 'http://www.choxue.com/zh-tw/players/%d/detailstats.json' % player_id
		self.debug_console.setText(self.debug_console.toPlainText() + '\r\n' + url)
		response = urllib.urlopen(url)
		_pdata = json.loads(response.read())

		self.indivstats_gamelogs.clear()
		self.indivstats_season.clear()

		for game in _pdata['gamelogs']:
			game['reb_tot'] 	= game['reb_o'] + game['reb_d']
			game['points_tot'] 	= (int(game['ft'].split(' - ')[0]) + (int(game['two'].split(' - ')[0]) * 2) + (int(game['trey'].split(' - ')[0]) * 3)) 
			game['two'] 		= '%s (%s)' %(game['two'].replace(' - ', '/'), self.stat_percentage(game['two']))
			game['trey'] 		= '%s (%s)' %(game['trey'].replace(' - ', '/'), self.stat_percentage(game['trey']))
			game['ft'] 			= '%s (%s)' %(game['ft'].replace(' - ', '/'), self.stat_percentage(game['ft']))
			self.indivstats_gamelogs.addItem('%s %s' % (game['date'], game['game']), game)

		for season in _pdata['seasons']:
			season['reb_total'] 	= season['reb_d_total'] + season['reb_o_total']
			season['reb_avg'] 		= season['reb_d_avg'] + season['reb_o_avg']
			season['trey_avg'] 		= '%s (%s)' %(season['trey_avg'].replace(' - ', '/'), self.stat_percentage(season['trey_avg']))
			season['two_avg'] 		= '%s (%s)' %(season['two_avg'].replace(' - ', '/'), self.stat_percentage(season['two_avg']))
			season['ft_avg'] 		= '%s (%s)' %(season['ft_avg'].replace(' - ', '/'), self.stat_percentage(season['ft_avg']))
			season['trey_total'] 	= '%s (%s)' %(season['trey_total'].replace(' - ', '/'), self.stat_percentage(season['trey_total']))
			season['two_total'] 	= '%s (%s)' %(season['two_total'].replace(' - ', '/'), self.stat_percentage(season['two_total']))
			season['ft_total'] 		= '%s (%s)' %(season['ft_total'].replace(' - ', '/'), self.stat_percentage(season['ft_total']))
			self.indivstats_season.addItem('%s - %s' % (season['year'], season['team']), season)

		player = self.player_by_ID(player_id)
		player['detailstats'] = _pdata
		#print json.dumps(_pdata, sort_keys=True, indent=4)
		#print json.dumps(self.API_data, sort_keys=True, indent=4)

	def indivstats2_handler(self, command):
		_pid = self.indivstats_player.itemData(self.indivstats_player.currentIndex())
		player = self.player_by_ID(_pid)

		_dict = dict(
			player_name = player['name'].encode('utf-8'),
			player_info = (str(player['jersey']) + ' | ' + str(player['position'])).encode('utf-8'),
			statistics = self.indivstats2_info.text().encode('utf-8'),
			period = self.indivstats2_period.text().encode('utf-8'),
			headshot_src = player['headshot_src'],
			logo_src = player['logo_src']
		)

		if(command == 'ADD' or command == 'ADD AUTO'):
			self.sendTCP('MIXER 1-120 FILL 0.084375 0.166667 0.85 0.85 0 Linear')
			self.sendTCP('CG 1-120 ADD 1 "_101 Scoreboard statistics" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'ADD AUTO'):
			QTimer.singleShot(10000, lambda: self.indivstats2_handler('STOP'))

		if(command == 'STOP'):
			self.sendTCP('CG 1-120 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-120 UPDATE 1 ' + self.dict_to_templateData(_dict))

	def indivstats_handler(self, command):
		_pid = self.indivstats_player.itemData(self.indivstats_player.currentIndex())
		player = self.player_by_ID(_pid)

		_dict = dict(
			player_name = player['name'].encode('utf-8'),
			info_1 = self.indivstats_info_1.text().encode('utf-8'),
			info_2 = self.indivstats_info_2.text().encode('utf-8'),
			info_3 = self.indivstats_info_3.text().encode('utf-8'),
			info_4 = self.indivstats_info_4.text().encode('utf-8'),
			headshot_src = player['headshot_src'],
			logo_src = player['logo_src'],
			ad_src = self.indivstats_ad.currentText().encode('utf-8')
		)

		if(command == 'CLEAR STATISTICS'):
			self.indivstats2_info.setText('')

		if(command == 'AUTOFILL'):
			_info = ''
			_period = ''

			if(self.auto_game.isChecked()):
				_period = 'TODAY'
				for statistic in self._pcheckboxes:
					if(statistic.isChecked()):
						_info += '    ' + statistic.text()

			if(self.auto_season.isChecked()):
				_period = 'SEASON'
				for statistic in self._scheckboxes:
					if(statistic.isChecked()):
						_info += '    ' + statistic.text()

			if(self.auto_gamelog.isChecked()):
				for statistic in self._gcheckboxes:
					if(statistic.isChecked()):
						_info += '    ' + statistic.text()

			if(self.auto_manual.isChecked()):
				_info = ''

			self.indivstats2_info.setText(_info.strip())
			self.indivstats2_period.setText(_period.strip())

		if(command == 'POPULATE GAME STATISTICS'):
			_pdata = self.player_by_ID(_pid) # Get selected player info from VM

			#print json.dumps(_pdata, sort_keys=True, indent=4)
			
			self.game_2pt.setText('2PT: %s' % _pdata['two'])
			self.game_3pt.setText('3PT: %s' % _pdata['trey'])
			self.game_ft.setText('FT: %s' % _pdata['ft'])
			self.game_pts.setText('%s PTS' % _pdata['points_tot'])
			self.game_reb.setText('%s REB' % _pdata['reb_tot'])
			self.game_ast.setText('%s AST' % _pdata['assists'])
			self.game_stl.setText('%s STL' % _pdata['stl'])
			self.game_blk.setText('%s BLK' % _pdata['blk'])
			self.game_fouls.setText('%s FOULS' % _pdata['fouls'])
			
		if(command == 'POPULATE SEASON STATISTICS'):
			_sdata = self.indivstats_season.itemData(self.indivstats_season.currentIndex())

			#print json.dumps(_sdata, sort_keys=True, indent=4)
						
			self.season_2pt.setText('2PT: %s' % _sdata['two_avg'])
			self.season_3pt.setText('3PT: %s' % _sdata['trey_avg'])
			self.season_pts.setText('PTS: %s' % _sdata['points_avg'])
			self.season_ft.setText('FT: %s' % _sdata['ft_avg'])
			self.season_reb.setText('%s REB' % _sdata['reb_avg'])
			self.season_ast.setText('%s AST' % _sdata['ast_avg'])
			self.season_stl.setText('%s STL' % _sdata['stl_avg'])
			self.season_blk.setText('%s BLK' % _sdata['blk_avg'])
			self.season_fouls.setText('%s FOULS' % _sdata['pfoul_avg'])
			self.season_gp.setText('%s GP' % _sdata['gp'])
			self.season_to.setText('%s TO' % _sdata['turnover_avg'])
			self.season_minutes.setText('%s MIN' % _sdata['minutes_avg'])

		if(command == 'POPULATE GAMELOG STATISTICS'):
			_gdata = self.indivstats_gamelogs.itemData(self.indivstats_gamelogs.currentIndex())

			#print json.dumps(_gdata, sort_keys=True, indent=4)
						
			self.gamelog_2pt.setText('2PT: %s' % _gdata['two'])
			self.gamelog_3pt.setText('3PT: %s' % _gdata['trey'])
			self.gamelog_ft.setText('FT: %s' % _gdata['ft'])
			self.gamelog_pts.setText('%s PTS' % _gdata['points_tot'])
			self.gamelog_reb.setText('%s REB' % _gdata['reb_tot'])
			self.gamelog_ast.setText('%s AST' % _gdata['ast'])
			self.gamelog_stl.setText('%s STL' % _gdata['stl'])
			self.gamelog_blk.setText('%s BLK' % _gdata['blk'])
			self.gamelog_fouls.setText('%s FOULS' % _gdata['pfoul'])
			self.gamelog_minutes.setText('%s MIN' % _gdata['minutes'])

		if(command == 'LOAD STATISTICS TO VM THEN POPULATE'): # Load indiv statistics from chosen player based on player_id
			self.indivstats_gamelogs.blockSignals(True)
			self.indivstats_season.blockSignals(True)

			self.load_API(False) # Load current game data into VM only
			self.loadPlayerDataToVM(_pid) # Load career data into VM

			self.indivstats_gamelogs.blockSignals(False)
			self.indivstats_season.blockSignals(False)

			self.indivstats_handler('POPULATE GAME STATISTICS')
			self.indivstats_handler('POPULATE SEASON STATISTICS')
			self.indivstats_handler('POPULATE GAMELOG STATISTICS')
			self.indivstats_handler('AUTOFILL')

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-70 FILL -0.015625 0.236111 0.85 0.85 0 Linear')
			self.sendTCP('CG 1-70 ADD 1 "_011 Player stats box-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-70 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-70 UPDATE 1 ' + self.dict_to_templateData(_dict))

		if(command == 'AD ON'):
			self.sendTCP('CG 1-70 UPDATE 1 ' + self.dict_to_templateData(dict(ad_src = _dict['ad_src'])))
			self.sendTCP('CG 1-70 INVOKE 1 "ad_in"')

		if(command == 'AD OFF'):
			self.sendTCP('CG 1-70 INVOKE 1 "ad_out"')

	def init_tcpWorker(self):
		self.tcpWorker = tcpWorker(self.ipaddress.text(), int(self.port.text()))
		self.tcpWorker.error.connect(lambda: QtGui.QMessageBox.critical(self, "TCP Error", str("CasparCG connection error."), QtGui.QMessageBox.Abort))
		self.tcpWorker.files.connect(self.filePopulator)
		self.tcpWorker.start()
		self.sendTCP('MIXER 1-40 FILL 0.084375 0.166667 0.85 0.85 0 Linear')
		self.sendTCP('MIXER 1-120 FILL 0.084375 0.166667 0.85 0.85 0 Linear')
		self.sendTCP('MIXER 1-130 FILL 0.084375 0.166667 0.85 0.85 0 Linear')
		self.sendTCP('MIXER 1-70 FILL -0.015625 0.236111 0.85 0.85 0 Linear')
		self.sendTCP('MIXER 1-100 FILL 0.075 0.138889 0.85 0.85 0 Linear')
		self.sendTCP('MIXER 1-10 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
		self.sendTCP('MIXER 1-80 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
		self.sendTCP('MIXER 1-90 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
		self.sendTCP('MIXER 1-20 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
		self.sendTCP('MIXER 1-110 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
		self.sendTCP('MIXER 1-50 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
		self.sendTCP('MIXER 1-51 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
		self.sendTCP('MIXER 1-60 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
		self.sendTCP('MIXER 1-30 FILL 0.05 0.305556 0.9 0.9 0 Linear')
		self.sendTCP('PLAY 1-1 "#ff00ff00" CUT 1 Linear RIGHT')
		self.tcpWorker.TLS()

	def init_SerialWorker(self):
		self.serialWorker = SerialWorker(self.com_comboBox.currentText(), "9600")
		self.serialWorker.error.connect(lambda: QtGui.QMessageBox.critical(self, "Serial Error", str("Serial connection error."), QtGui.QMessageBox.Abort))
		self.serialWorker.error.connect(lambda: self.serialWorker.port_close())
		self.serialWorker.to_caspar.connect(self.serial_handler)
		self.serialWorker.start()

	def serial_scan(self): #scan for available ports. return a list of tuples (num, name)
		available = []
		ports = glob.glob('/dev/tty.*')

		for index, port in enumerate(ports):
		        try:
		            s = serial.Serial(port)
		            s.close()
		            available.append((index, port))
		        except (OSError, serial.SerialException):
		            pass

		self.com_comboBox.clear()
		for n,s in available:
			self.com_comboBox.addItem(s, n)

	def serial_handler(self, _dict):
		self.SERIAL_data = _dict

		if(self.invert_teams.isChecked()):
			_home_score = self.SERIAL_data['home_score']
			_away_score = self.SERIAL_data['away_score']
			_home_fouls = self.SERIAL_data['home_fouls']
			_away_fouls = self.SERIAL_data['away_fouls']
			self.SERIAL_data['home_score'] = _away_score
			self.SERIAL_data['away_score'] = _home_score
			self.SERIAL_data['home_fouls'] = _away_fouls
			self.SERIAL_data['away_fouls'] = _home_fouls

		_dict = dict(
			home_score = 	self.SERIAL_data['home_score'].encode('utf-8'),
			away_score = 	self.SERIAL_data['away_score'].encode('utf-8'),
			home_fouls = 	self.SERIAL_data['home_fouls'].encode('utf-8'),
			away_fouls = 	self.SERIAL_data['away_fouls'].encode('utf-8'),
			game_clock = 	self.SERIAL_data['game_clock'].encode('utf-8'),
			shot_clock = 	self.SERIAL_data['shot_clock'].encode('utf-8'),
			quarter = 		self.SERIAL_data['quarter'].encode('utf-8')
		)

		self.sendTCP('CG 1-40 UPDATE 1 ' + self.dict_to_templateData(_dict))

	def score3_handler(self, command):
		_dict = dict(
			f0 = 			self.score3_title.text().encode('utf-8'),
			home_name = 	self.score3_home_team.text().encode('utf-8'),
			away_name = 	self.score3_away_team.text().encode('utf-8'),
			home_score = 	self.SERIAL_data['home_score'].encode('utf-8'),
			away_score = 	self.SERIAL_data['away_score'].encode('utf-8'),
			src_home = 		self.API_data['home']['logo_src'].encode('utf-8'),
			src_away = 		self.API_data['guest']['logo_src'].encode('utf-8')
		)

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-110 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-110 ADD 1 "_017 Score 3-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-110 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-110 UPDATE 1 ' + self.dict_to_templateData(_dict))
	
	def score2_handler(self, command):
		_dict = dict(
			home_score = 	self.SERIAL_data['home_score'].encode('utf-8'),
			away_score = 	self.SERIAL_data['away_score'].encode('utf-8'),
			status = 		self.SERIAL_data['quarter'].encode('utf-8'),
			game_time = 	self.SERIAL_data['game_clock'].encode('utf-8'),
			src_home = 		self.API_data['home']['logo_src'].encode('utf-8'),
			src_away = 		self.API_data['guest']['logo_src'].encode('utf-8')
		)

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-110 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-110 ADD 1 "_004 Score 2-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-110 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-110 UPDATE 1 ' + self.dict_to_templateData(_dict))

	def qbyq_handler(self, command):
		_dict = dict(
			f0 = self.qbyq_title.text().encode('utf-8'),
			home_name = self.qbyq_home_team.text().encode('utf-8'),
			away_name = self.qbyq_away_team.text().encode('utf-8'),
			home_q1 = self.qbyq_table.item(0, 0).text().encode('utf-8'),
			home_q2 = self.qbyq_table.item(0, 1).text().encode('utf-8'),
			home_q3 = self.qbyq_table.item(0, 2).text().encode('utf-8'),
			home_q4 = self.qbyq_table.item(0, 3).text().encode('utf-8'),
			away_q1 = self.qbyq_table.item(1, 0).text().encode('utf-8'),
			away_q2 = self.qbyq_table.item(1, 1).text().encode('utf-8'),
			away_q3 = self.qbyq_table.item(1, 2).text().encode('utf-8'),
			away_q4 = self.qbyq_table.item(1, 3).text().encode('utf-8'),
			home_score = self.qbyq_home_score.text().encode('utf-8'),
			away_score = self.qbyq_away_score.text().encode('utf-8'),
			src_home = self.API_data['home']['logo_src'].encode('utf-8'),
			src_away = self.API_data['guest']['logo_src'].encode('utf-8')
		)

		if(command == 'FILL TOTAL'): # Called on QTable exit
			_home = int('0' + self.qbyq_table.item(0, 0).text()) + int('0' + self.qbyq_table.item(0, 1).text()) + int('0' + self.qbyq_table.item(0, 2).text()) + int('0' + self.qbyq_table.item(0, 3).text())
			_away = int('0' + self.qbyq_table.item(1, 0).text()) + int('0' + self.qbyq_table.item(1, 1).text()) + int('0' + self.qbyq_table.item(1, 2).text()) + int('0' + self.qbyq_table.item(1, 3).text())
			self.qbyq_home_score.setText(str(_home))
			self.qbyq_away_score.setText(str(_away))

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-100 FILL 0.075 0.138889 0.85 0.85 0 Linear')
			self.sendTCP('CG 1-100 ADD 1 "_010 Score by quarter-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-100 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-100 UPDATE 1 ' + self.dict_to_templateData(_dict))

	def commentator_handler(self, command):
		_dict = dict(
		f0 = self.commentator_title.text().encode('utf-8'),
		f1 = self.commentator_left.text().encode('utf-8'),
		f2 = self.commentator_right.text().encode('utf-8')
		)

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-10 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-10 ADD 1 "_001 COMMENTATORS-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-10 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-10 UPDATE 1 ' + self.dict_to_templateData(_dict))

	def official_handler(self, command):
		_dict = dict(
		f0 = self.official_left.text().encode('utf-8'),
		f1 = self.official_center.text().encode('utf-8'),
		f2 = self.official_right.text().encode('utf-8')
		)

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-20 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-20 ADD 1 "_002 Officials-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-20 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-20 UPDATE 1 ' + self.dict_to_templateData(_dict))

	def standings_handler(self, command):
		_dict = dict(
			title = self.standings_title.text().encode('utf-8'),
			name_1 = self.standingsTable.item(0, 0).text().encode('utf-8'),
			w_1 = self.standingsTable.item(0, 1).text().encode('utf-8'),
			l_1 = self.standingsTable.item(0, 2).text().encode('utf-8'),
			gb_1 = self.standingsTable.item(0, 3).text().encode('utf-8'),
			name_2 = self.standingsTable.item(1, 0).text().encode('utf-8'),
			w_2 = self.standingsTable.item(1, 1).text().encode('utf-8'),
			l_2 = self.standingsTable.item(1, 2).text().encode('utf-8'),
			gb_2 = self.standingsTable.item(1, 3).text().encode('utf-8'),
			name_3 = self.standingsTable.item(2, 0).text().encode('utf-8'),
			w_3 = self.standingsTable.item(2, 1).text().encode('utf-8'),
			l_3 = self.standingsTable.item(2, 2).text().encode('utf-8'),
			gb_3 = self.standingsTable.item(2, 3).text().encode('utf-8'),
			name_4 = self.standingsTable.item(3, 0).text().encode('utf-8'),
			w_4 = self.standingsTable.item(3, 1).text().encode('utf-8'),
			l_4 = self.standingsTable.item(3, 2).text().encode('utf-8'),
			gb_4 = self.standingsTable.item(3, 3).text().encode('utf-8'),
			src_1 = self.first_comboBox.currentText().encode('utf-8'),
			src_2 = self.second_comboBox.currentText().encode('utf-8'),
			src_3 = self.third_comboBox.currentText().encode('utf-8'),
			src_4 = self.fourth_comboBox.currentText().encode('utf-8'),
			ad_src = self.standings_ad.currentText().encode('utf-8')
		)

		if(command == 'INITIALIZE'):
			_saved = self.qsettings.value("STANDINGS")
			self.standings_title.setText(_saved['title'])
			self.standingsTable.item(0, 0).setText(_saved['name_1'])
			self.standingsTable.item(0, 1).setText(_saved['w_1'])
			self.standingsTable.item(0, 2).setText(_saved['l_1'])
			self.standingsTable.item(0, 3).setText(_saved['gb_1'])
			self.standingsTable.item(1, 0).setText(_saved['name_2'])
			self.standingsTable.item(1, 1).setText(_saved['w_2'])
			self.standingsTable.item(1, 2).setText(_saved['l_2'])
			self.standingsTable.item(1, 3).setText(_saved['gb_2'])
			self.standingsTable.item(2, 0).setText(_saved['name_3'])
			self.standingsTable.item(2, 1).setText(_saved['w_3'])
			self.standingsTable.item(2, 2).setText(_saved['l_3'])
			self.standingsTable.item(2, 3).setText(_saved['gb_3'])
			self.standingsTable.item(3, 0).setText(_saved['name_4'])
			self.standingsTable.item(3, 1).setText(_saved['w_4'])
			self.standingsTable.item(3, 2).setText(_saved['l_4'])
			self.standingsTable.item(3, 3).setText(_saved['gb_4'])

		if(command == 'SAVE QSETTINGS'):
			_dict['name_1'] = _dict['name_1'].decode('utf-8') # Decode so QSettings reencodes in own encoding
			_dict['name_2'] = _dict['name_2'].decode('utf-8')
			_dict['name_3'] = _dict['name_3'].decode('utf-8')
			_dict['name_4'] = _dict['name_4'].decode('utf-8')
			self.qsettings.setValue('STANDINGS', _dict)

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-30 FILL 0.05 0.305556 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-30 ADD 1 "_009 Standings-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-30 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-30 UPDATE 1 ' + self.dict_to_templateData(_dict))

		if(command == 'AD ON'):
			self.sendTCP('CG 1-30 UPDATE 1 ' + self.dict_to_templateData(dict(ad_src = _dict['ad_src'])))
			self.sendTCP('CG 1-30 INVOKE 1 "ad_in"')

		if(command == 'AD OFF'):
			self.sendTCP('CG 1-30 INVOKE 1 "ad_out"')

	def scoreboard_handler(self, command):
		_dict = dict(
			home_score = 	self.SERIAL_data['home_score'].encode('utf-8'),
			away_score = 	self.SERIAL_data['away_score'].encode('utf-8'),
			home_fouls = 	self.SERIAL_data['home_fouls'].encode('utf-8'),
			away_fouls = 	self.SERIAL_data['away_fouls'].encode('utf-8'),
			game_clock = 	self.SERIAL_data['game_clock'].encode('utf-8'),
			shot_clock = 	self.SERIAL_data['shot_clock'].encode('utf-8'),
			quarter = 		self.SERIAL_data['quarter'].encode('utf-8'),
			home_name = 	self.home_team.text().encode('utf-8'),
			away_name = 	self.away_team.text().encode('utf-8'),
			home_src = 		self.API_data['home']['logo_src'].encode('utf-8'),
			away_src = 		self.API_data['guest']['logo_src'].encode('utf-8'),
			ad_src = 		self.scoreboard_ad.currentText().encode('utf-8')
		)

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-40 FILL 0.084375 0.166667 0.85 0.85 0 Linear')
			self.sendTCP('CG 1-40 ADD 1 "_003 Score line-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-40 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-40 UPDATE 1 ' + self.dict_to_templateData(_dict))

		if(command == 'AD ON'):
			self.sendTCP('CG 1-40 UPDATE 1 ' + self.dict_to_templateData(dict(ad_src = _dict['ad_src'])))
			self.sendTCP('CG 1-40 INVOKE 1 "ad_in"')

		if(command == 'AD OFF'):
			self.sendTCP('CG 1-40 INVOKE 1 "ad_out"')

	def lineup_handler(self, command):
		_pid = [self.lineup_player_1.itemData(self.lineup_player_1.currentIndex()), self.lineup_player_2.itemData(self.lineup_player_2.currentIndex()), self.lineup_player_3.itemData(self.lineup_player_3.currentIndex()), self.lineup_player_4.itemData(self.lineup_player_4.currentIndex()), self.lineup_player_5.itemData(self.lineup_player_5.currentIndex())]
		_players = [self.player_by_ID(_pid[0]), self.player_by_ID(_pid[1]), self.player_by_ID(_pid[2]), self.player_by_ID(_pid[3]), self.player_by_ID(_pid[4])]
		
		_dict = dict(
		f0 = self.lineup_title.text().encode('utf-8'),
		name_1 = _players[0]['name'].encode('utf-8'),
		name_2 = _players[1]['name'].encode('utf-8'),
		name_3 = _players[2]['name'].encode('utf-8'),
		name_4 = _players[3]['name'].encode('utf-8'),
		name_5 = _players[4]['name'].encode('utf-8'),
		info_1 = str(_players[0]['jersey']).encode('utf-8'),
		info_2 = str(_players[1]['jersey']).encode('utf-8'),
		info_3 = str(_players[2]['jersey']).encode('utf-8'),
		info_4 = str(_players[3]['jersey']).encode('utf-8'),
		info_5 = str(_players[4]['jersey']).encode('utf-8'),
		src_1 =	_players[0]['headshot_src'],
		src_2 =	_players[1]['headshot_src'],
		src_3 =	_players[2]['headshot_src'],
		src_4 =	_players[3]['headshot_src'],
		src_5 =	_players[4]['headshot_src'],
		ad_src = self.lineup_ad.currentText().encode('utf-8')
		)

		if(command == 'ADD'): 
			self.sendTCP('MIXER 1-50 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-50 ADD 1 "_015 Starting lineup faces-CG" 1 ' + self.dict_to_templateData(_dict))
		
		if(command == 'STOP'): 
			self.sendTCP('CG 1-50 STOP 1')
		
		if(command == 'UPDATE'): 
			self.sendTCP('CG 1-50 UPDATE 1 ' + self.dict_to_templateData(_dict))

		if(command == 'AD ON'):
			self.sendTCP('CG 1-50 UPDATE 1 ' + self.dict_to_templateData(dict(ad_src = _dict['ad_src'])))
			self.sendTCP('CG 1-50 INVOKE 1 "ad_in"')

		if(command == 'AD OFF'):
			self.sendTCP('CG 1-50 INVOKE 1 "ad_out"')

	def lineup_2_handler(self, command):
		_pid = [self.lineup_player_6.itemData(self.lineup_player_6.currentIndex()), self.lineup_player_7.itemData(self.lineup_player_7.currentIndex()), self.lineup_player_8.itemData(self.lineup_player_8.currentIndex()), self.lineup_player_9.itemData(self.lineup_player_9.currentIndex()), self.lineup_player_10.itemData(self.lineup_player_10.currentIndex())]
		_players = [self.player_by_ID(_pid[0]), self.player_by_ID(_pid[1]), self.player_by_ID(_pid[2]), self.player_by_ID(_pid[3]), self.player_by_ID(_pid[4])]

		_dict = dict(
		f0 = self.lineup_title_2.text().encode('utf-8'),
		name_1 = _players[0]['name'].encode('utf-8'),
		name_2 = _players[1]['name'].encode('utf-8'),
		name_3 = _players[2]['name'].encode('utf-8'),
		name_4 = _players[3]['name'].encode('utf-8'),
		name_5 = _players[4]['name'].encode('utf-8'),
		info_1 = str(_players[0]['jersey']).encode('utf-8'),
		info_2 = str(_players[1]['jersey']).encode('utf-8'),
		info_3 = str(_players[2]['jersey']).encode('utf-8'),
		info_4 = str(_players[3]['jersey']).encode('utf-8'),
		info_5 = str(_players[4]['jersey']).encode('utf-8'),
		src_1 =	_players[0]['headshot_src'],
		src_2 =	_players[1]['headshot_src'],
		src_3 =	_players[2]['headshot_src'],
		src_4 =	_players[3]['headshot_src'],
		src_5 =	_players[4]['headshot_src'],
		ad_src = self.lineup_ad.currentText().encode('utf-8')
		)

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-51 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-51 ADD 1 "_015 Starting lineup faces-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-51 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-51 UPDATE 1 ' + self.dict_to_templateData(_dict))

		if(command == 'AD ON'):
			self.sendTCP('CG 1-51 UPDATE 1 ' + self.dict_to_templateData(dict(ad_src = _dict['ad_src'])))
			self.sendTCP('CG 1-51 INVOKE 1 "ad_in"')

		if(command == 'AD OFF'):
			self.sendTCP('CG 1-51 INVOKE 1 "ad_out"')

	def team_stats_2_handler(self, command):
		try: 
			row = self.team_stats_table.selectionModel().selectedRows()[0].row()
		except: 
			QtGui.QMessageBox.critical(self, "Data error", str("Select a statistic."), QtGui.QMessageBox.Abort)
			return


		_statistic = ['FOULS', '2 POINT', '3 POINT', 'FREE THROWS', 'DEFENSIVE REBOUNDS', 'OFFENSIVE REBOUNDS', 'REBOUNDS', 'ASSISTS', 'STEALS', 'BLOCKS']

		_dict = dict(
			home = self.team_stats_table.item(row, 0).text().encode('utf-8'),
			away = self.team_stats_table.item(row, 1).text().encode('utf-8'),
			statistic = _statistic[row].encode('utf-8')
		)
		
		if(command == 'ADD' or command == 'ADD AUTO'):
			self.sendTCP('MIXER 1-130 FILL 0.084375 0.166667 0.85 0.85 0 Linear')
			self.sendTCP('CG 1-130 ADD 1 "_102 Scoreboard team statistics" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'ADD AUTO'):
			QTimer.singleShot(5000, lambda: self.team_stats_2_handler('STOP'))

		if(command == 'STOP'):
			self.sendTCP('CG 1-130 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-130 UPDATE 1 ' + self.dict_to_templateData(_dict))


	def team_stats_handler(self, command):
		_dict = dict(
			f0 = 			self.team_stats_flag.text().encode('utf-8'),
			stat_1 = 		'2-PT'.encode('utf-8'),
			stat_2 = 		'3-PT'.encode('utf-8'),
			stat_3 = 		'FT'.encode('utf-8'),
			stat_4 = 		'REBOUNDS (D/O)'.encode('utf-8'),
			stat_5 = 		'ASSISTS'.encode('utf-8'),
			stat_6 = 		'STEALS'.encode('utf-8'),
			stat_7 = 		'BLOCKS'.encode('utf-8'),
			home_score = 	str(self.API_data['home']['score']).encode('utf-8'),
			home_name = 	self.API_data['home']['name'].encode('utf-8'),
			away_name = 	self.API_data['guest']['name'].encode('utf-8'),
			home_src = 		self.API_data['home']['logo_src'].encode('utf-8'),
			away_src = 		self.API_data['guest']['logo_src'].encode('utf-8'),
			home_1 = 		str(self.API_data['home']['two']).encode('utf-8'),
			home_2 = 		str(self.API_data['home']['trey']).encode('utf-8'),
			home_3 = 		str(self.API_data['home']['ft']).encode('utf-8'),
			home_4 = 		('%d    (%d/%d)' % (self.API_data['home']['reb_tot'], self.API_data['home']['reb_d'], self.API_data['home']['reb_o'])).encode('utf-8'),
			home_5 = 		str(self.API_data['home']['ast']).encode('utf-8'),
			home_6 = 		str(self.API_data['home']['stl']).encode('utf-8'),
			home_7 = 		str(self.API_data['home']['blk']).encode('utf-8'),
			away_score = 	str(self.API_data['guest']['score']),
			away_1 = 		str(self.API_data['guest']['two']).encode('utf-8'),
			away_2 = 		str(self.API_data['guest']['trey']).encode('utf-8'),
			away_3 = 		str(self.API_data['guest']['ft']).encode('utf-8'),
			away_4 = 		('%d    (%d/%d)' % (self.API_data['guest']['reb_tot'], self.API_data['guest']['reb_d'], self.API_data['guest']['reb_o'])).encode('utf-8'),
			away_5 = 		str(self.API_data['guest']['ast']).encode('utf-8'),
			away_6 = 		str(self.API_data['guest']['stl']).encode('utf-8'),
			away_7 = 		str(self.API_data['guest']['blk']).encode('utf-8'),
			ad_src = 		self.team_stats_ad.currentText().encode('utf-8')
		)

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-60 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-60 ADD 1 "_012 Game stats-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-60 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-60 UPDATE 1 ' + self.dict_to_templateData(_dict))

		if(command == 'AD ON'):
			self.sendTCP('CG 1-60 UPDATE 1 ' + self.dict_to_templateData(dict(ad_src = _dict['ad_src'])))
			self.sendTCP('CG 1-60 INVOKE 1 "ad_in"')

		if(command == 'AD OFF'):
			self.sendTCP('CG 1-60 INVOKE 1 "ad_out"')

	def gp_handler(self, command):
		_dict = dict(
			f0 = self.gp_f0.text().encode('utf-8'),
			f1 = self.gp_f1.text().encode('utf-8')
		)		
		if(command == 'ADD'):
			self.sendTCP('MIXER 1-80 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-80 ADD 1 "_100 General purpose 1-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-80 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-80 UPDATE 1 ' + self.dict_to_templateData(_dict))
	
	def gp2_handler(self, command):
		_dict = dict(
			f0 = self.gp2_f0.text().encode('utf-8'),
			f1 = self.gp2_f1.text().encode('utf-8'),
			src_home = self.gp2_left.currentText().encode('utf-8'),
			src_away = self.gp2_right.currentText().encode('utf-8')
		)

		if(command == 'ADD'):
			self.sendTCP('MIXER 1-90 FILL 0.05 0.0972222 0.9 0.9 0 Linear')
			self.sendTCP('CG 1-90 ADD 1 "_100 General purpose 1-CG" 1 ' + self.dict_to_templateData(_dict))

		if(command == 'STOP'):
			self.sendTCP('CG 1-90 STOP 1')

		if(command == 'UPDATE'):
			self.sendTCP('CG 1-90 UPDATE 1 ' + self.dict_to_templateData(_dict))

	def stop_all(self):
		self.sendTCP('CG 1-120 STOP 1')
		self.sendTCP('CG 1-130 STOP 1')
		self.sendTCP('CG 1-70 STOP 1')
		self.sendTCP('CG 1-100 STOP 1')
		self.sendTCP('CG 1-10 STOP 1')
		self.sendTCP('CG 1-80 STOP 1')
		self.sendTCP('CG 1-90 STOP 1')
		self.sendTCP('CG 1-20 STOP 1')
		self.sendTCP('CG 1-110 STOP 1')
		self.sendTCP('CG 1-50 STOP 1')
		self.sendTCP('CG 1-51 STOP 1')
		self.sendTCP('CG 1-60 STOP 1')
		self.sendTCP('CG 1-30 STOP 1')



	def filePopulator(self, files): # Populate combo boxes after TLS call
		self.first_comboBox.clear() # STANDINGS
		self.first_comboBox.addItems(files)
		self.second_comboBox.clear()
		self.second_comboBox.addItems(files)
		self.third_comboBox.clear()
		self.third_comboBox.addItems(files)
		self.fourth_comboBox.clear()
		self.fourth_comboBox.addItems(files)
		self.standings_ad.clear()
		self.standings_ad.addItems(files)
		self.scoreboard_ad.clear()
		self.scoreboard_ad.addItems(files)
		self.team_stats_ad.clear()
		self.team_stats_ad.addItems(files)
		self.lineup_ad.clear()
		self.lineup_ad.addItems(files)
		self.indivstats_ad.clear()
		self.indivstats_ad.addItems(files)
		self.gp2_left.clear()
		self.gp2_right.clear()
		self.gp2_left.addItems(files)
		self.gp2_right.addItems(files)

	def dict_to_templateData(self, _dict):
		_out = '"<templateData>'
		for key, value in _dict.iteritems():
			_out += '<componentData id=\\"%s\\"><data id=\\"text\\" value=\\"%s\\"/></componentData>' %(key, value)
		_out += '</templateData>"'
		return _out









class tcpWorker(QtCore.QThread): # TCP sender
	files = QtCore.Signal(list)
	error = QtCore.Signal(str)
	success = QtCore.Signal(str)

	def __init__(self, ip, port):
		QtCore.QThread.__init__(self)
		self.tcp = None
		self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.tcp.settimeout(1)
		self.ip = ip
		self.port = port

	def run(self):
		try:
			self.tcp.connect((self.ip, self.port))
			self.success.emit
		except (socket.timeout, socket.error), e:
			self.error.emit(True)

		while True:
			pass

	def send(self, command):
		#print repr(command)
		print len(command)
		self.tcp.send(command + '\r\n')
		data = self.tcp.recv(1024)

	def TLS(self):
		self.tcp.send("CLS\r\n")
		data = self.tcp.recv(100000)
		data = data.splitlines() # Split by newline
		data = filter(None, data) # Remove empty elements

		_ret = []

		if(data[0] == '200 CLS OK'): # If CasparCG provides a valid response
			for x in data:
				_split = x.split()
				if(_split[1] == 'STILL'):
					_ret.append(_split[0][1:-1].decode('utf-8').replace('\\', '/') + ".png")

		self.files.emit(_ret)


class SerialWorker(QtCore.QThread):
	success = QtCore.Signal(int)
	to_browser = QtCore.Signal(str)
	to_caspar = QtCore.Signal(dict)
	error = QtCore.Signal(str)

	def __init__(self, port_num, port_baud, port_stopbits = serial.STOPBITS_ONE, port_parity = serial.PARITY_NONE):
		QtCore.QThread.__init__(self)

		self.serial_port = None
		self.serial_arg  = dict(port = port_num, baudrate = port_baud, stopbits = port_stopbits, parity = port_parity, timeout  = None)
		self.score_digits = [63, 6, 91, 79, 102, 109, 125, 7, 127, 103]
		self.score_digits_100s = [191, 134, 219, 207, 230, 237, 253, 135, 255, 231] # Indexes for >99 score
		self.offset = 1
		self._old_dict = None # Used to only emit() when data changes
		self._dict = None # Used to only emit() when data changes
		self._running = True

	def run(self):
		try: 
			self.serial_port = serial.Serial(**self.serial_arg) # Open serial port with given arguments
			self.success.emit(True)
			print "Successfully connected to COM port."
		except serial.SerialException, e:
			self.error.emit(True)
			print e.message
			return

		while self._running:
			try:
				line = self.serial_port.readline() # Emit error if cannot read from device anymore; means disconnection
				line = str(line.rstrip('\r\n')) # Remove newline, ensure string data type
			except: 
				self.error.emit(True)
				self._running = False
				
			if (len(line) == 28 + self.offset):
				ascii_to_int = [""] * 100 # Holds ord() of all incoming bytes
				for x, char in enumerate(line):
					ascii_to_int[x] = ord(char)

				self._dict = dict(
					home_score = self.returnTeamScore(ascii_to_int[10 + self.offset], ascii_to_int[9 + self.offset]),
					home_fouls = self.returnFouls(ascii_to_int[24 + self.offset]),
					away_score = self.returnTeamScore(ascii_to_int[8 + self.offset], ascii_to_int[7 + self.offset]),
					away_fouls = self.returnFouls(ascii_to_int[23 + self.offset]),
					quarter = self.returnQuarter(ascii_to_int[17 + self.offset], ascii_to_int[18 + self.offset]),
					game_clock = self.returnGameTime(ascii_to_int[11 + self.offset], ascii_to_int[12 + self.offset], ascii_to_int[13 + self.offset], ascii_to_int[14 + self.offset]),
					shot_clock = self.returnShotClock(ascii_to_int[26 + self.offset])
				)

				if(self._dict != self._old_dict): # Bandwidth limiting, avoid saturating network with repeating TCP requests
					print self._dict
					self.to_caspar.emit(self._dict)
					self._old_dict = self._dict



	def returnTeamScore(self, ord1, ord2):
		digit1, digit2, hundreds = "", "", ""
		try: digit1 = str(self.score_digits.index(ord1))
		except: pass
		try: digit2 = str(self.score_digits.index(ord2))
		except: pass

		try: # Do 100s anyway as it will escape out if its <99. <99 will pass both these statements
			digit1 = str(self.score_digits_100s.index(ord1))
			hundreds = "1" 
		except: pass
		try: digit2 = str(self.score_digits_100s.index(ord2))
		except: pass

		return hundreds + digit1 + digit2

	def returnFouls(self, ord1):
		return str(int(ord1) - 48) # Fouls are direct, if ASCII byte = 0 then fouls = 0

	def returnQuarter(self, ord1, ord2):
		_q = str(int(ord1) + int(ord2) - 48 - 48) # ord1 + ord2 is the current quarter
		if(_q == '1'):
			return "1ST"
		if(_q == '2'):
			return "2ND"
		if(_q == '3'):
			return "3RD"
		if(_q == '4'):
			return "4TH"
		if(_q == '5'):
			return "OT"
		return _q

	def returnPosession(self, ord1):
		if(ord1 == 50): return "HOME"
		if(ord1 == 52): return "GUEST"
		return ""

	def returnGameTime(self, seconds_ord, deciseconds_ord, minutes_ord, deciminutes_ord):
		seconds, deciseconds, minutes, deciminutes, colon = "", "", "", "", ":"
		try: seconds = str(self.score_digits.index(seconds_ord))
		except: pass
		try: deciseconds = str(self.score_digits_100s.index(deciseconds_ord))
		except: pass
		try: minutes = str(self.score_digits_100s.index(minutes_ord))
		except: pass
		try: deciminutes = str(self.score_digits.index(deciminutes_ord))
		except: pass
		try: 
			deciseconds = str(self.score_digits.index(deciseconds_ord))
			colon = '.'
			return ':' + deciminutes + minutes
		except: pass


		return deciminutes + minutes + colon + deciseconds + seconds

	def returnShotClock(self, seconds_ord):
		return str(seconds_ord)

	def port_write(self, command):
		self.serial_port.write(command.encode())

	def port_close(self):
		self.serial_port.close()




def main():
	app = QtGui.QApplication(sys.argv)  # A new instance of QApplication
	form = CasparCGController()			# We set the form to be our CasparCGController (design)
	form.show()							# Show the form
	app.exec_()							# and execute the app


if __name__ == '__main__':
	main()                              # run the main function