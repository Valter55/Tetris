from tkinter import *
from tkinter import messagebox
import sys, random
from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor
import sqlite3

conn = sqlite3.connect('my.db')
c = conn.cursor()

root = Tk()
root.geometry("400x400")
root.title("Тетрис")

def menu():
    text = Label(width=50, height=2, font='Arial 12', text="Добро пожаловать в игру Тетрис, хотите сыграть?")
    button1 = Button(width=20, height=5, text= "Начать игру", font='Arial 12', command=lambda: start(), fg="black")
    button2 = Button(width=20, height=5, text= "Рекорды", fg="black", font='Arial 12', command=lambda: recorder())
    button3 = Button(width=20, height=5, text= "Выход", fg="black", command=lambda: on_closing(), font='Arial 12')
    text.pack(side=TOP)
    button1.pack(side=TOP)
    button2.pack(side=TOP)
    button3.pack(side=TOP)

    def on_closing():
        if messagebox.askokcancel("Выход", "Вы действительно хотите выйти?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    def recorder():
        root.destroy()
        rec = Tk()
        rec.geometry("400x300")
        rec.title("Таблица рекордов")
        text1 = Label(width=50, height=2, font='Arial 12', text="Топ-5 лучших игроков:")
        text1.pack()
        c.execute('SELECT * FROM records ORDER BY score DESC LIMIT 5')
        rows = c.fetchall()
        for row in rows:
            text2 = Label(width=50, height=2, font='Arial 12', text="-"+" Логин: " + str(row[1]) + ", Очки: " + str(row[2]))
            text2.pack()
        rec.mainloop()

        c.close()
        conn.close()
        sys.exit()
        
    def start():
        root.destroy()
        class Tetris(QMainWindow):

            def __init__(self):
                super().__init__()

                self.initUI()

            def initUI(self):
                self.tboard = Board(self)
                self.setCentralWidget(self.tboard)

                self.statusbar = self.statusBar()
                self.tboard.msg2Statusbar[str].connect(self.statusbar.showMessage)

                self.tboard.start()

                self.resize(280, 580)
                self.center()
                self.setWindowTitle('Тетрис')
                self.show()

            def center(self):
                screen = QDesktopWidget().screenGeometry()
                size = self.geometry()
                self.move((screen.width() - size.width()) / 2,
                          (screen.height() - size.height()) / 2)

        class Board(QFrame):

            msg2Statusbar = pyqtSignal(str)

            BoardWidth = 10
            BoardHeight = 22
            Speed = 300

            def __init__(self, parent):
                super().__init__(parent)

                self.initBoard()

            def initBoard(self):

                self.timer = QBasicTimer()
                self.isWaitingAfterLine = False

                self.curX = 0
                self.curY = 0
                self.numLinesRemoved = 0
                self.board = []

                self.setFocusPolicy(Qt.StrongFocus)
                self.isStarted = False
                self.isPaused = False
                self.clearBoard()

            def shapeAt(self, x, y):
                return self.board[(y * Board.BoardWidth) + x]

            def setShapeAt(self, x, y, shape):
                self.board[(y * Board.BoardWidth) + x] = shape

            def squareWidth(self):
                return self.contentsRect().width() // Board.BoardWidth

            def squareHeight(self):
                return self.contentsRect().height() // Board.BoardHeight

            def start(self):

                if self.isPaused:
                    return

                self.isStarted = True
                self.isWaitingAfterLine = False
                self.numLinesRemoved = 0
                self.clearBoard()

                self.msg2Statusbar.emit(str(self.numLinesRemoved))

                self.newPiece()
                self.timer.start(Board.Speed, self)

            def pause(self):

                if not self.isStarted:
                    return

                self.isPaused = not self.isPaused

                if self.isPaused:
                    self.timer.stop()
                    self.msg2Statusbar.emit("paused")

                else:
                    self.timer.start(Board.Speed, self)
                    self.msg2Statusbar.emit(str(self.numLinesRemoved))

                self.update()

            def paintEvent(self, event):

                painter = QPainter(self)
                rect = self.contentsRect()

                boardTop = rect.bottom() - Board.BoardHeight * self.squareHeight()

                for i in range(Board.BoardHeight):
                    for j in range(Board.BoardWidth):
                        shape = self.shapeAt(j, Board.BoardHeight - i - 1)

                        if shape != Tetrominoe.NoShape:
                            self.drawSquare(painter,
                                            rect.left() + j * self.squareWidth(),
                                            boardTop + i * self.squareHeight(), shape)

                if self.curPiece.shape() != Tetrominoe.NoShape:

                    for i in range(4):
                        x = self.curX + self.curPiece.x(i)
                        y = self.curY - self.curPiece.y(i)
                        self.drawSquare(painter, rect.left() + x * self.squareWidth(),
                                        boardTop + (Board.BoardHeight - y - 1) * self.squareHeight(),
                                        self.curPiece.shape())

            def keyPressEvent(self, event):

                if not self.isStarted or self.curPiece.shape() == Tetrominoe.NoShape:
                    super(Board, self).keyPressEvent(event)
                    return

                key = event.key()

                if key == Qt.Key_P:
                    self.pause()
                    return

                if self.isPaused:
                    return

                elif key == Qt.Key_Left:
                    self.tryMove(self.curPiece, self.curX - 1, self.curY)

                elif key == Qt.Key_Right:
                    self.tryMove(self.curPiece, self.curX + 1, self.curY)

                elif key == Qt.Key_Down:
                    self.tryMove(self.curPiece.rotateRight(), self.curX, self.curY)

                elif key == Qt.Key_Up:
                    self.tryMove(self.curPiece.rotateLeft(), self.curX, self.curY)

                elif key == Qt.Key_Space:
                    self.dropDown()

                elif key == Qt.Key_D:
                    self.oneLineDown()

                else:
                    super(Board, self).keyPressEvent(event)

            def timerEvent(self, event):

                if event.timerId() == self.timer.timerId():

                    if self.isWaitingAfterLine:
                        self.isWaitingAfterLine = False
                        self.newPiece()
                    else:
                        self.oneLineDown()

                else:
                    super(Board, self).timerEvent(event)

            def clearBoard(self):

                for i in range(Board.BoardHeight * Board.BoardWidth):
                    self.board.append(Tetrominoe.NoShape)

            def dropDown(self):

                newY = self.curY

                while newY > 0:

                    if not self.tryMove(self.curPiece, self.curX, newY - 1):
                        break

                    newY -= 1

                self.pieceDropped()

            def oneLineDown(self):

                if not self.tryMove(self.curPiece, self.curX, self.curY - 1):
                    self.pieceDropped()

            def pieceDropped(self):

                for i in range(4):
                    x = self.curX + self.curPiece.x(i)
                    y = self.curY - self.curPiece.y(i)
                    self.setShapeAt(x, y, self.curPiece.shape())

                self.removeFullLines()

                if not self.isWaitingAfterLine:
                    self.newPiece()

            def removeFullLines(self):

                numFullLines = 0
                rowsToRemove = []

                for i in range(Board.BoardHeight):

                    n = 0
                    for j in range(Board.BoardWidth):
                        if not self.shapeAt(j, i) == Tetrominoe.NoShape:
                            n = n + 1

                    if n == 10:
                        rowsToRemove.append(i)

                rowsToRemove.reverse()

                for m in rowsToRemove:

                    for k in range(m, Board.BoardHeight):
                        for l in range(Board.BoardWidth):
                            self.setShapeAt(l, k, self.shapeAt(l, k + 1))

                numFullLines = numFullLines + len(rowsToRemove)

                if numFullLines >= 0:
                    self.numLinesRemoved = self.numLinesRemoved + numFullLines
                    self.ourScore = self.numLinesRemoved * 100
                    self.msg2Statusbar.emit(str(self.ourScore))
                    self.isWaitingAfterLine = True
                    self.curPiece.setShape(Tetrominoe.NoShape)
                    self.update()



            def newPiece(self):

                self.curPiece = Shape()
                self.curPiece.setRandomShape()
                self.curX = Board.BoardWidth // 2 + 1
                self.curY = Board.BoardHeight - 1 + self.curPiece.minY()
                if not self.tryMove(self.curPiece, self.curX, self.curY):
                    self.curPiece.setShape(Tetrominoe.NoShape)
                    self.timer.stop()
                    self.isStarted = False
                    self.msg2Statusbar.emit("Игра окончена")

                    root = Tk()
                    root.geometry("400x400")
                    root.title("Игра окончена")
                    v = StringVar()
                    text1 = Label(width=50, height=2, font='Arial 12', text="Игра окончена, вы заработали "+str(self.ourScore)+" очков.")
                    text2 = Label(width=50, height=2, font='Arial 12', text="Пожалуйста укажите свое имя:")
                    mylogin = Entry(textvariable=v, width=30)
                    button1 = Button(width=30, height=5, text="Сохранить результат", font='Arial 12', command=lambda: login(mylogin.get(),self.ourScore))
                    button2 = Button(width=30, height=5, text="Выйти без сохранения", font='Arial 12', command=lambda: closing())
                    text1.pack(side=TOP)
                    text2.pack(side=TOP)
                    mylogin.pack(side=TOP)
                    button1.pack(side=TOP)
                    button2.pack(side=TOP)

                    def login(username,userscore):
                        c.execute("INSERT INTO records (name,score) VALUES ('%s','%s')" % (str(username), userscore))
                        conn.commit()
                        messagebox.showinfo("Сохранение", "Ваш результат успешно сохранен.")
                        c.close()
                        conn.close()
                        sys.exit()

                    def closing():
                        if messagebox.askokcancel("Выход", "Вы действительно хотите выйти?"):
                            root.destroy()
                            sys.exit()

                    root.protocol("WM_DELETE_WINDOW", closing)

                    root.mainloop()

            def tryMove(self, newPiece, newX, newY):

                for i in range(4):

                    x = newX + newPiece.x(i)
                    y = newY - newPiece.y(i)

                    if x < 0 or x >= Board.BoardWidth or y < 0 or y >= Board.BoardHeight:
                        return False

                    if self.shapeAt(x, y) != Tetrominoe.NoShape:
                        return False

                self.curPiece = newPiece
                self.curX = newX
                self.curY = newY
                self.update()

                return True

            def drawSquare(self, painter, x, y, shape):

                colorTable = [0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                              0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]

                color = QColor(colorTable[shape])
                painter.fillRect(x + 1, y + 1, self.squareWidth() - 2,
                                 self.squareHeight() - 2, color)

                painter.setPen(color.lighter())
                painter.drawLine(x, y + self.squareHeight() - 1, x, y)
                painter.drawLine(x, y, x + self.squareWidth() - 1, y)

                painter.setPen(color.darker())
                painter.drawLine(x + 1, y + self.squareHeight() - 1,
                                 x + self.squareWidth() - 1, y + self.squareHeight() - 1)
                painter.drawLine(x + self.squareWidth() - 1,
                                 y + self.squareHeight() - 1, x + self.squareWidth() - 1, y + 1)

        class Tetrominoe(object):

            NoShape = 0
            ZShape = 1
            SShape = 2
            LineShape = 3
            TShape = 4
            SquareShape = 5
            LShape = 6
            MirroredLShape = 7

        class Shape(object):

            coordsTable = (
                ((0, 0), (0, 0), (0, 0), (0, 0)),
                ((0, -1), (0, 0), (-1, 0), (-1, 1)),
                ((0, -1), (0, 0), (1, 0), (1, 1)),
                ((0, -1), (0, 0), (0, 1), (0, 2)),
                ((-1, 0), (0, 0), (1, 0), (0, 1)),
                ((0, 0), (1, 0), (0, 1), (1, 1)),
                ((-1, -1), (0, -1), (0, 0), (0, 1)),
                ((1, -1), (0, -1), (0, 0), (0, 1))
            )

            def __init__(self):

                self.coords = [[0, 0] for i in range(4)]
                self.pieceShape = Tetrominoe.NoShape

                self.setShape(Tetrominoe.NoShape)

            def shape(self):
                return self.pieceShape

            def setShape(self, shape):

                table = Shape.coordsTable[shape]

                for i in range(4):
                    for j in range(2):
                        self.coords[i][j] = table[i][j]

                self.pieceShape = shape

            def setRandomShape(self):
                self.setShape(random.randint(1, 7))

            def x(self, index):
                return self.coords[index][0]

            def y(self, index):
                return self.coords[index][1]

            def setX(self, index, x):
                self.coords[index][0] = x

            def setY(self, index, y):
                self.coords[index][1] = y

            def minX(self):

                m = self.coords[0][0]
                for i in range(4):
                    m = min(m, self.coords[i][0])

                return m

            def maxX(self):

                m = self.coords[0][0]
                for i in range(4):
                    m = max(m, self.coords[i][0])

                return m

            def minY(self):

                m = self.coords[0][1]
                for i in range(4):
                    m = min(m, self.coords[i][1])

                return m

            def maxY(self):

                m = self.coords[0][1]
                for i in range(4):
                    m = max(m, self.coords[i][1])

                return m

            def rotateLeft(self):

                if self.pieceShape == Tetrominoe.SquareShape:
                    return self

                result = Shape()
                result.pieceShape = self.pieceShape

                for i in range(4):
                    result.setX(i, self.y(i))
                    result.setY(i, -self.x(i))

                return result

            def rotateRight(self):

                if self.pieceShape == Tetrominoe.SquareShape:
                    return self

                result = Shape()
                result.pieceShape = self.pieceShape

                for i in range(4):
                    result.setX(i, -self.y(i))
                    result.setY(i, self.x(i))

                return result

        if __name__ == '__main__':
            app = QApplication([])
            tetris = Tetris()
            sys.exit(app.exec_())

menu()
root.mainloop()