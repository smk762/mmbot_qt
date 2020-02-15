
def colorize_row(self, table, row, bgcol):
    for col in range(table.columnCount()):
        table.item(row,col).setForeground(bgcol)

def get_cell_val(self, table, row='', column=''):
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

def find_in_table(self, table, text):
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