import sys
import re

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableView,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

from bilibili import download_video, search_videos, sync
from utils import try_until_complete


class SearchResultWindow(QMainWindow):
    def __init__(self, results, path_callback=None):
        super().__init__()
        self.results = results
        self.path_callback = path_callback
        self.initUI()

    def initUI(self):
        self.setWindowTitle("搜索结果")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        self.model = QStandardItemModel()
        self.model.setColumnCount(2)
        self.model.setHorizontalHeaderLabels(["标题", "作者"])

        for result in self.results:
            title = re.sub("<[^>]+>", "", result["title"])
            title_item = QStandardItem(title)
            title_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # 禁止编辑
            author_item = QStandardItem(result["author"])
            author_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # 禁止编辑
            self.model.appendRow([title_item, author_item])

        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.verticalHeader().setVisible(False)  # 隐藏行号
        self.table_view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )  # 自动调整标题列宽度
        self.table_view.doubleClicked.connect(self.on_table_clicked)

        self.show()

    def on_table_clicked(self, index):
        selected_row = index.row()
        bvid = self.results[selected_row]["bvid"]
        video_path = try_until_complete(lambda: sync(download_video(bvid)))

        if self.path_callback is not None:
            self.path_callback(video_path)


if __name__ == "__main__":

    def print_path(path):
        print(path)

    # 搜索结果数据
    results = try_until_complete(lambda: sync(search_videos("原神")))
    app = QApplication(sys.argv)
    window = SearchResultWindow(results, path_callback=print_path)
    sys.exit(app.exec_())
