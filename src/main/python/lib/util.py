from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from lib import pallete
import requests
import logging
from . import binance_api
import random

logger = logging.getLogger(__name__)

old_data = {}

def colorize_row(table, row, bgcol):
    for col in range(table.columnCount()):
        table.item(row,col).setForeground(bgcol)

def get_cell_val(table, row='', column=''):
    if row == '':
       row = table.currentRow() 
    if column == '':
       column = table.currentColumn() 
    if table.currentRow() != -1:
        if table.item(row,column).text() != '':
            return float(table.item(row,column).text())
        else:
            return 0
    else:
        return 0

def find_in_table(table, text):
    for i in range(table.rowCount()):
        for j in range(table.columnCount()):
            if table.item(i,j) is not None:
                if text == table.item(i,j).text():
                    return i,j
    return -1, -1

## File operations
def saveFileDialog(self):
    filename = ''
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getSaveFileName(self,"Save Table data to CSV","","Text Files (*.csv)", options=options)
    return fileName

# Table operations
def export_table(self, table, headers_list):
    #TODO: add sender, get headers dynamically
    table_csv = ','.join(headers_list) + '\r\n'
    for i in range(table.rowCount()):
        row_list = []
        for j in range(table.columnCount()):
            try:
                row_list.append(table.item(i,j).text())
            except:
                pass
        table_csv += ','.join(row_list)+'\r\n'
    now = datetime.datetime.now()
    timestamp = datetime.datetime.timestamp(now)
    filename = self.saveFileDialog()
    if filename != '':
        with open(filename, 'w') as f:
            f.write(table_csv)

def get_time_str():
    return str(datetime.datetime.fromtimestamp(int(time.time())))

def format_num_10f(val):
    if val != 0:
        try:
            val = "{:.10f}".format(round(float(val),10))
        except:
            pass
    return val

def row_bg(table, bgcolor, condition_col=0, condition_match=None, condition_type='include'):
    if condition_match is None:
        condition_match = []
    if condition_type == 'include':
        for row in range(table.rowCount()):
            if table.item(row,condition_col) is not None:
                if table.item(row,condition_col).text() in condition_match:
                    for col in range(table.columnCount()):
                        table.item(row,col).setBackground(bgcolor)
    else:
        for row in range(table.rowCount()):
            if table.item(row,condition_col) is not None:
                if table.item(row,condition_col).text() not in condition_match:
                    for col in range(table.columnCount()):
                        table.item(row,col).setBackground(bgcolor)

def row_fg(table, fgcolor, condition_col=0, condition_match=None, condition_type='include'):
    if condition_match is None:
        condition_match = []
    if condition_type == 'include':
        for row in range(table.rowCount()):
            if table.item(row,condition_col) is not None:
                if table.item(row,condition_col).text() in condition_match:
                    for col in range(table.columnCount()):
                        table.item(row,col).setForeground(fgcolor)
    else:
        for row in range(table.rowCount()):
            if table.item(row,condition_col) is not None:
                if table.item(row,condition_col).text() not in condition_match:
                    for col in range(table.columnCount()):
                        table.item(row,col).setForeground(fgcolor)

def add_row(row, row_data, table, bgcol='', align=''):
    col = 0
    for cell_data in row_data:
        cell = QTableWidgetItem(str(cell_data))
        table.setItem(row,col,cell)
        if align == '':
            cell.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)  
        elif align == 'left':
            cell.setTextAlignment(Qt.AlignLeft|Qt.AlignVCenter)  
        elif align == 'right':
            cell.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)  
        if bgcol != '' :
            table.item(row,col).setBackground(bgcol)
        col += 1

def populate_table(r, table, msg_lbl='', msg='', row_filter='', endpoint=''):
    if r == '':
        # dont thread
        url = "http://127.0.0.1:8000/"+endpoint
        r = requests.get(url)
    if r.status_code == 200:
        if 'table_data' in r.json():
            table_name = endpoint.replace('/','_')
            if table_name not in old_data:
                old_data[table_name] = []
            data = r.json()['table_data']
            if data != old_data[table_name]:
                logger.info("Updating "+table_name)
                table.setSortingEnabled(False)
                table.clearContents()
                table.setRowCount(len(data))
                row = 0
                max_col_str = {}
                if len(data) > 0:
                    headers = list(data[0].keys())
                    table.setColumnCount(len(headers))
                    table.setHorizontalHeaderLabels(headers)
                    for i in range(len(headers)):
                        max_col_str[i] = str(headers[i])
                    for item in data:
                        row_data = list(item.values())
                        col_num = 0
                        for cell in row_data:
                            if len(str(cell)) > len(str(max_col_str[col_num])):
                                max_col_str[col_num] = str(cell)
                            col_num += 1
                        if row_filter == '':
                            add_row(row, row_data, table)
                            row += 1
                        else:
                            filter_param = row_filter.split('|')
                            filter_col_num = filter_param[0]
                            filter_col_text = filter_param[1]
                            filter_type = filter_param[2]
                            if str(row_data[int(filter_col_num)]) == str(filter_col_text):
                                if filter_type == 'INCLUDE':
                                    add_row(row, row_data, table)
                                    row += 1
                            else:
                                if filter_type == 'EXCLUDE':
                                    add_row(row, row_data, table)
                                    row += 1
                    
                table.setRowCount(row)
                table.setSortingEnabled(True)
                fontinfo = QFontInfo(table.font())
                for i in max_col_str:
                    fm = QFontMetrics(QFont(fontinfo.family(), fontinfo.pointSize()))
                    str_width = fm.width(max_col_str[i])
                    table.setColumnWidth(i, str_width+10)
                if msg_lbl != '':
                    if len(data) == 0:
                        msg = "No results in table..."
                    msg_lbl.setText(msg)
                old_data[table_name] = data
            else:
                logger.info("Not updating "+table_name+", no new data")
        # apply BG color to binance depth tables (in this func due to request delay, probably better elsewhere...?)
        row_bg(table, pallete.dk_green, 3, ['Ask'], 'include')
        row_bg(table, pallete.dk_red, 3, ['Bid'], 'include')
    else:
        logger.info(r)
        logger.info(r.text)

# Selection menu operations
def update_combo(combo, options, selected):
    source=combo.sender().objectName()
    #logger.info("update combo sender:"+str(source))
    combo.clear()
    options.sort()
    print(options)
    combo.addItems(options)
    if selected in options:
        for i in range(combo.count()):
            if combo.itemText(i) == selected:
                combo.setCurrentIndex(i)
    elif 'KMD' in options:
            for i in range(combo.count()):
                if combo.itemText(i) == 'KMD':
                    combo.setCurrentIndex(i)
    else:
        combo.setCurrentIndex(0)
        selected = combo.itemText(combo.currentIndex())
    return selected

def combo_selected(combo):
    return combo.itemText(combo.currentIndex())
    
def adjust_cols(table, data):
    max_col_str = {}
    if len(data) > 0:
        headers = list(data[0].keys())
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        for i in range(len(headers)):
            max_col_str[i] = str(headers[i])
        for item in data:
            row_data = list(item.values())
            for i in range(len(row_data)):
                if len(str(row_data[i])) > len(str(max_col_str[i])):
                    max_col_str[i] = str(row_data[i])
    fontinfo = QFontInfo(table.font())
    print(max_col_str)
    for i in max_col_str:
        fm = QFontMetrics(QFont(fontinfo.family(), fontinfo.pointSize()))
        str_width = fm.width(max_col_str[i])
        table.setColumnWidth(i, str_width+10)

def clear_labels(label_list):
    for label in label_list:
        label.setText('')

def get_seed():
    seed_words_list = []
    while len(seed_words_list) < 24:
        word = random.choice(wordlist.wordlist)
        if word not in seed_words_list:
            seed_words_list.append(word)
    seed_phrase = " ".join(seed_words_list)

def get_base_rel_from_combos(base_combo, rel_combo, active_coins, api='mm2'):
    base = ''
    base_index = base_combo.currentIndex()
    if base_index != -1:
        base = base_combo.itemText(base_index)
    rel = ''
    rel_index = rel_combo.currentIndex()
    if rel_index != -1:
        rel = rel_combo.itemText(rel_index)
    if api == 'mm2':
        active_coins_selection = active_coins
        if len(active_coins_selection) > 0:
            if rel == '':
                rel = 'KMD'
            rel = update_combo(rel_combo,active_coins_selection,rel)
            active_coins_selection.remove(rel)
            base = update_combo(base_combo,active_coins_selection,base)
    elif api == "Binance":
        base_coins_selection = list(binance_api.base_asset_info.keys())
        if base == '':
            base = 'KMD'
        if len(base_coins_selection) > 0:
            base = update_combo(base_combo,base_coins_selection,base)
            rel_coins_selection = binance_api.base_asset_info[base]['quote_assets']
            rel = update_combo(rel_combo,rel_coins_selection,rel)
    return base, rel

def async_populate_bid_depth_table(resp):
    if resp.status_code == 200:
        table_data = resp.json()['table_data']
        self.bid_tbl_model = bn_bid_TableModel(table_data)
        self.binance_depth_table_bid.setModel(self.bid_tbl_model)

def async_populate_ask_depth_table(resp):
    if resp.status_code == 200:
        table_data = resp.json()['table_data']
        self.ask_tbl_model = bn_ask_TableModel(table_data)
        self.binance_depth_table_ask.setModel(self.ask_tbl_model)

