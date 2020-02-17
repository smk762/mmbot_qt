from PyQt5.QtWidgets import QTableWidget

class TableModel(QTableWidget):
    def __init__(self, table_data):
        super(TableModel,self).__init__()
        self.table_data = []

    def rowCount(self,QModelIndex):
        return self.rowCount()

    def colCount(self,QModelIndex):
        if len(self.table_data) > 0:
            return self.columnCount()
        else:
            return 0

    def getHeaders(self):
        if len(self.table_data) > 0:
            return list(self.table_data[0].keys())
        else:
            return []

    def getRow_list(self, row_num):
        if len(self.table_data) > row_num:
            return list(self.table_data[row_num].values())
        else:
            return []

    def getRow_dict(self, row_num):
        if len(self.table_data) > row_num:
            return self.table_data[row_num]
        else:
            return {}

    def addRow(self, row_list, align='', bgcol='', fgcol=''):
        row = self.rowCount()
        col = 0
        for cell_data in row_list:
            cell = QTableWidgetItem(str(cell_data))
            self.setItem(row,col,cell)
            if align == '':
                cell.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)  
            elif align == 'left':
                cell.setTextAlignment(Qt.AlignLeft|Qt.AlignVCenter)  
            elif align == 'right':
                cell.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)  
            if bgcol != '':
                self.item(row,col).setBackground(bgcol)
            if fgcol != '':
                self.item(row,col).setForeground(fgcol)
            col += 1

    def addData(self, align='', bgcol='', fgcol=''):
        for i in range(self.table_data):
            row_list = self.getRow_list(i)
            self.addRow(row_list, align='', bgcol='', fgcol='')