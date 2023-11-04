import json
import os
import re
import numpy as np
import openai
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from PyQt5.QtWidgets import QFontComboBox, QSpinBox, QApplication, QSizePolicy, QMainWindow, QPlainTextEdit, QAction, QFileDialog, QPushButton, QVBoxLayout, QWidget, QLineEdit, QLabel, QDialog, QFormLayout, QComboBox, QTextEdit, QHBoxLayout, QDialogButtonBox, QSplitter, QMenu, QMessageBox, QGridLayout, QFrame,QTabWidget
from PyQt5.QtGui import QIcon, QColor, QTextCharFormat, QFont, QSyntaxHighlighter, QPainter, QTextCursor
from PyQt5.QtCore import Qt, QRegularExpression, pyqtSignal
import sys
import subprocess
import tempfile
import pickle
from collections import deque

# Définir le style personnalisé
custom_style = HtmlFormatter(style='emacs', full=True).get_style_defs('.highlight')

            
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.blue)

        function_format = QTextCharFormat()
        function_format.setForeground(QColor(128, 0, 128))

        class_format = QTextCharFormat()
        class_format.setForeground(QColor(128, 0, 128))
        class_format.setFontWeight(QFont.Bold)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(0, 128, 0))

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(0, 128, 0))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(Qt.red)

        self.highlighting_rules = []
        keywords = ["break", "continue", "if", "else", "for", "while", "not", "and", "or", "as", "False", "True", "from", "else", "def", "class", "import", "return"]

        for keyword in keywords:
            pattern = r"\b" + keyword + r"\b"
            regex = QRegularExpression(pattern)
            self.highlighting_rules.append((regex, keyword_format))

        self.highlighting_rules.append((QRegularExpression(r'\bdef\b\s*(\w+)\s*\('), function_format, 1))
        self.highlighting_rules.append((QRegularExpression(r'\bclass\b\s*(\w+)\s*'), class_format, 1))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), self.string_format))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), self.string_format))
        self.highlighting_rules.append((QRegularExpression(r"\b\d+\b"), self.number_format))
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*"), self.comment_format))

    def highlightBlock(self, text):
        for pattern, format, *group in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                if group:
                    self.setFormat(match.capturedStart(group[0]), match.capturedLength(group[0]), format)
                else:
                    self.setFormat(match.capturedStart(), match.capturedLength(), format)

        self.setCurrentBlockState(0)

        
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Définir la police et la taille pour tout le texte dans le QPlainTextEdit
        font = QFont()
        font.setFamily("Courier")  # Vous pouvez choisir la famille de police que vous préférez
        font.setPointSize(10)  # Définir la taille de la police en points
        if os.path.exists("config.json"):
            with open("config.json", "r") as file:
                self.config = json.load(file)
                font.setFamily(self.config.get("font_family", "Courier"))
                font.setPointSize(int(self.config.get("font_size", 10)))
        self.setFont(font)
        
        self.setWindowTitle("Configuration GPT")
        self.api_key_input = QLineEdit(self)
        self.model_selector = QComboBox(self)
        self.model_selector.addItems(["gpt-4", "gpt-4-32k", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"])

        layout = QFormLayout()
        layout.addRow(QLabel("Clé API:"), self.api_key_input)
        layout.addRow(QLabel("Modèle GPT:"), self.model_selector)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.save_config)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)

        self.setLayout(layout)
        self.load_config()

    def load_config(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as file:
                self.config = json.load(file)
                self.api_key_input.setText(self.config.get("api_key", ""))
                self.model_selector.setCurrentText(self.config.get("model", ""))
             

    def save_config(self):
        config = {
            "api_key": self.api_key_input.text(),
            "model": self.model_selector.currentText(),
            "font_family": self.config.get("font_family"),
            "font_size": self.config.get("font_size")
        }
        with open("config.json", "w") as file:
            json.dump(config, file)
        self.accept()
            
class GeneralConfigDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Définir la police et la taille pour tout le texte dans le QPlainTextEdit
        font = QFont()
        font.setFamily("Courier")  # Vous pouvez choisir la famille de police que vous préférez
        font.setPointSize(10)  # Définir la taille de la police en points
        if os.path.exists("config.json"):
            with open("config.json", "r") as file:
                self.config = json.load(file)
                font.setFamily(self.config.get("font_family", "Courier"))
                font.setPointSize(int(self.config.get("font_size", 10)))
        self.setFont(font)
        
        self.setWindowTitle("Configuration Générale")

        self.font_combo = QFontComboBox(self)
        self.font_size_spinbox = QSpinBox(self)
        self.font_size_spinbox.setRange(5, 72)

        layout = QFormLayout()
        layout.addRow(QLabel("Police:"), self.font_combo)
        layout.addRow(QLabel("Taille de la police:"), self.font_size_spinbox)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.save_config)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)

        self.setLayout(layout)
        self.load_config()

    def load_config(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as file:
                self.config = json.load(file)
                self.font_combo.setCurrentFont(QFont(self.config.get("font_family", "Courier")))
                self.font_size_spinbox.setValue(int(self.config.get("font_size", 10)))
             
    def save_config(self):
        config = {
            "api_key": self.config.get("api_key", ""),
            "model": self.config.get("model", ""),
            "font_family": self.font_combo.currentFont().family(),
            "font_size": self.font_size_spinbox.value()
        }
        with open("config.json", "w") as file:
            json.dump(config, file)
        self.accept()

class EditorConfigDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ident_space=4 
        if os.path.exists("config.json"):
            with open("config.json", "r") as file:
                self.config = json.load(file)
                self.ident_space=self.config.get("ident_space", 4)

        
        
        self.setWindowTitle("Configuration Editeur")

        
        self.ident_space = QSpinBox(self)
        self.ident_space.setRange(1, 10)

        layout = QFormLayout()
        
        layout.addRow(QLabel("Indentation:"), self.ident_space)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.save_config)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)

        self.setLayout(layout)
        self.load_config()

    def load_config(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as file:
                self.config = json.load(file)
                self.ident_space.setValue(int(self.config.get("ident_space", 4)))
             
    def save_config(self):
        config = {
            "api_key": self.config.get("api_key", ""),
            "model": self.config.get("model", ""),
            "font_family": self.config.get("font_family"),
            "font_size": self.config.get("font_size"),
            "ident_space": self.ident_space.value()   
        }
        with open("config.json", "w") as file:
            json.dump(config, file)
        self.accept()

class SearchDialog(QDialog):
    def __init__(self, editor, parent=None):
        super(SearchDialog, self).__init__(parent)
        self.setWindowTitle("Rechercher")
        self.editor = editor    # store the editor
        layout = QGridLayout(self)

        # Label and input field for the search term
        self.label = QLabel("Texte à Rechercher", self)
        layout.addWidget(self.label, 0, 0)
        self.le = QLineEdit(self)
        layout.addWidget(self.le, 0, 1)

        # Next and Cancel buttons
        self.pbNext = QPushButton("Suivant", self)
        layout.addWidget(self.pbNext, 1, 0)

        self.bb = QDialogButtonBox(QDialogButtonBox.Cancel, self)
        layout.addWidget(self.bb, 1, 1)

        # Wire up the next button
        self.pbNext.clicked.connect(self.searchNext)

        # Wire up the Cancel button
        self.bb.rejected.connect(self.reject)

    def searchNext(self):
        textToSearch = self.le.text()
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()

        found = self.editor.find(textToSearch)
        if found:
            cursor.endEditBlock()
        else:
            cursor.endEditBlock()
            QMessageBox.information(
                self,
                "Information",
                "Le texte n'a pas été trouvé",
            )
        
class ReplaceDialog(QDialog):
    def __init__(self, editor, parent=None):
        super(ReplaceDialog, self).__init__(parent)
        self.setWindowTitle("Remplacer")
        self.editor = editor
        layout = QGridLayout(self)

        # Label and input field for the search term
        self.label = QLabel("Texte à remplacer", self)
        layout.addWidget(self.label, 0, 0)
        self.le = QLineEdit(self)
        layout.addWidget(self.le, 0, 1)

        # Label and input field for the replacement
        self.replace_label = QLabel("Remplacer par", self)
        layout.addWidget(self.replace_label, 1, 0)
        self.replace_le = QLineEdit(self)
        layout.addWidget(self.replace_le, 1, 1)

        # Find, Replace, Replace All and Cancel buttons
        self.pbFind = QPushButton("Rechercher", self)
        layout.addWidget(self.pbFind, 2, 0)
        self.pbReplace = QPushButton("Remplacer", self)
        layout.addWidget(self.pbReplace, 2, 1)
        self.pbReplaceAll = QPushButton("Remplacer tout", self)
        layout.addWidget(self.pbReplaceAll, 2, 2)
        self.bb = QPushButton("Cancel", self)
        layout.addWidget(self.bb, 2, 3)

        # Wire up the buttons
        self.pbFind.clicked.connect(self.findText)
        self.pbReplace.clicked.connect(self.replaceText)
        self.pbReplaceAll.clicked.connect(self.replaceAllText)
        self.bb.clicked.connect(self.reject)

    def findText(self):
        textToSearch = self.le.text()
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()

        found = self.editor.find(textToSearch)
        if found:
            cursor.endEditBlock()
        else:
            cursor.endEditBlock()
            QMessageBox.information(
                self,
                "Information",
                "Le texte n'a pas été trouvé",
            ) 

    def replaceText(self):
        textToSearch = self.le.text()  # Fetch text to search
        replacementText = self.replace_le.text()
    
        # Check if there is any text selected
        if self.editor.textCursor().hasSelection():
            # Get the selected text
            selectedText = self.editor.textCursor().selectedText()
    
            # Replace the selected text if it matches the search text
            if selectedText == textToSearch:
                # Create a new text cursor with the same selection as the current one
                newCursor = self.editor.textCursor()
    
                # Replace the selected text with the replacement text
                newCursor.insertText(replacementText)
    
                # Set the editor's text cursor to the new one
                self.editor.setTextCursor(newCursor)
                
    def replaceAllText(self):
        textToSearch = self.le.text()
        replacementText = self.replace_le.text()

        content = self.editor.toPlainText()  # Fetch the editor's content 
        newContent = content.replace(textToSearch, replacementText)  # Replace text
        self.editor.setPlainText(newContent)  # Apply new content
                   
class PythonEditor(QPlainTextEdit):
    sendToPromptSignal = pyqtSignal(str) 
    
    def __init__(self):
        super().__init__()
        
        # Définir la police et la taille pour tout le texte dans le QPlainTextEdit
        font = QFont()
        font.setFamily("Courier")  # Vous pouvez choisir la famille de police que vous préférez
        font.setPointSize(10)  # Définir la taille de la police en points
        if os.path.exists("config.json"):
            with open("config.json", "r") as file:
                self.config = json.load(file)
                font.setFamily(self.config.get("font_family", "Courier"))
                font.setPointSize(int(self.config.get("font_size", 10)))
        self.setFont(font)
        
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_area_width(0)

    def line_number_area_width(self):
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count //= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(), self.line_number_area_width(), cr.height())

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("lightgray"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("blue"))
                painter.drawText(0, top, self.line_number_area.width(), self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
    
    def contextMenuEvent(self, event):
        context_menu = self.createStandardContextMenu()

        # Ajout d'une action personnalisée
        send_to_prompt_action = QAction('Envoyer dans le Prompt', self)
        send_to_prompt_action.triggered.connect(self.send_to_prompt)
        context_menu.addAction(send_to_prompt_action)

        context_menu.exec_(event.globalPos())

    def send_to_prompt(self):
        selected_text = self.textCursor().selectedText()
        # Signal pour envoyer le texte sélectionné au prompt
        self.sendToPromptSignal.emit(selected_text)

class CustomTextEdit(PythonEditor):
    
    INDENT_SPACES = 4  # Définition de la variable pour le nombre d'espaces d'indentation
    if os.path.exists("config.json"):
        with open("config.json", "r") as file:
            config = json.load(file)
            INDENT_SPACES = config.get("ident_space", 4)
    

    def keyPressEvent(self, event):
        cursor = self.textCursor()

        if event.key() == Qt.Key_Tab and not event.modifiers() & Qt.ShiftModifier:
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                cursor.setPosition(start)
                cursor.movePosition(QTextCursor.StartOfBlock)
                start_block = cursor.block().blockNumber()
                cursor.setPosition(end)
                cursor.movePosition(QTextCursor.StartOfBlock)
                end_block = cursor.block().blockNumber()

                for block_num in range(start_block, end_block + 1):
                    cursor.setPosition(cursor.document().findBlockByNumber(block_num).position())
                    cursor.insertText(" " * self.INDENT_SPACES)  # Utilisation de la variable
            else:
                cursor.insertText(" " * self.INDENT_SPACES)  # Utilisation de la variable

        elif event.key() == Qt.Key_Backtab or (event.key() == Qt.Key_Tab and event.modifiers() & Qt.ShiftModifier):
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                cursor.setPosition(start)
                cursor.movePosition(QTextCursor.StartOfBlock)
                start_block = cursor.block().blockNumber()
                cursor.setPosition(end)
                cursor.movePosition(QTextCursor.StartOfBlock)
                end_block = cursor.block().blockNumber()

                for block_num in range(start_block, end_block + 1):
                    cursor.setPosition(cursor.document().findBlockByNumber(block_num).position())
                    cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, self.INDENT_SPACES)  # Utilisation de la variable
                    if cursor.selectedText() == " " * self.INDENT_SPACES:  # Utilisation de la variable
                        cursor.removeSelectedText()
            else:
                cur_line = cursor.block().text()
                start = cursor.position() - cursor.block().position()
                num_to_remove = self.INDENT_SPACES if start >= self.INDENT_SPACES else start  # Utilisation de la variable
                cursor.setPosition(cursor.position() - num_to_remove, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()

        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            cur_line = cursor.block().text()
            indentation = len(cur_line) - len(cur_line.lstrip())
            
            super().keyPressEvent(event)
            
            if cur_line.strip().endswith(":"):
                indentation += self.INDENT_SPACES  # Utilisation de la variable
            
            cursor = self.textCursor()
            cursor.insertText(" " * indentation)

        else:
            super().keyPressEvent(event)
             
class SimpleIDE(QMainWindow):
    RECENT_FILES_MAX = 10
    FILENAME_RECENT_FILES="recent_files.pkl"
    
    def __init__(self):
        super(SimpleIDE, self).__init__()
    
        # Définir la police et la taille pour tout le texte dans le QPlainTextEdit
        font = QFont()
        font.setFamily("Courier")  # Vous pouvez choisir la famille de police que vous préférez
        font.setPointSize(10)  # Définir la taille de la police en points
        if os.path.exists("config.json"):
            with open("config.json", "r") as file:
                self.config = json.load(file)
                font.setFamily(self.config.get("font_family", "Courier"))
                font.setPointSize(int(self.config.get("font_size", 10)))
        self.setFont(font)
        
        self.reponses_history = []
        self.questions_history = []
        self.fichier_courant = {} 
        
        self.text_edit = CustomTextEdit()
        self.textArea = self.text_edit  # Si text_edit est défini avant __init__
        
        
        # Init tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.closeTab)
        
        self.highlighter = PythonHighlighter(self.text_edit.document())

        self.run_button = QPushButton("Run Code", self)
        self.run_button.clicked.connect(self.run_code)
        self.searchDialog = None

        
        # Colonne pour GPT
        self.prompt_input = QTextEdit(self)
        self.prompt_input_button = QPushButton('Envoyer')
        self.history_button = QPushButton('Historique')
        self.history_menu = QMenu()
        self.clear_history_button = QPushButton('Nouveau')
        button_layout = QHBoxLayout()
        self.gpt_output = QTextEdit(self)
        self.gpt_output.setReadOnly(True)
        self.gpt_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.copy_code_button = QPushButton("Copy Code")        
        self.copy_code_button.clicked.connect(self.copy_code)
        
        self.gpt_output.setContextMenuPolicy(Qt.CustomContextMenu)
        self.gpt_output.customContextMenuRequested.connect(self.customContextMenuRequested)

        
        # Ajuster la politique de taille pour self.prompt_input
        prompt_input_size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        prompt_input_size_policy.setVerticalStretch(1)  # Prend 1/3 de l'espace vertical
        self.prompt_input.setSizePolicy(prompt_input_size_policy)

        # Ajuster la politique de taille pour self.gpt_output
        gpt_output_size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        gpt_output_size_policy.setVerticalStretch(2)  # Prend 2/3 de l'espace vertical
        self.gpt_output.setSizePolicy(gpt_output_size_policy)

        parent_layout = QVBoxLayout()  # Layout parent
        gpt_layout = QFormLayout()
        gpt_layout.addWidget(QLabel("Prompt:"))
        gpt_layout.addRow(self.prompt_input)
        button_layout.addWidget(self.prompt_input_button)
        button_layout.addWidget(self.clear_history_button)
        button_layout.addWidget(self.history_button)
        
        gpt_layout.addRow(button_layout)

        gpt_layout.addRow(QLabel("Réponse GPT:"))
        gpt_layout.addRow(self.gpt_output)
        gpt_layout.addRow(self.copy_code_button)
        
        gpt_column = QWidget()
        gpt_column.setLayout(gpt_layout)

        # Ajout des widgets au splitter
        self.splitter = QSplitter(Qt.Horizontal)
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.text_edit)
        editor_layout.addWidget(self.run_button)
        
        # Ajout des widgets au splitter
        self.splitter = QSplitter(Qt.Horizontal)
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.tab_widget)  # Ajouter tab_widget au layout
        editor_layout.addWidget(self.run_button)

        editor_column = QWidget()
        editor_column.setLayout(editor_layout)

        self.splitter.addWidget(editor_column)
        self.splitter.addWidget(gpt_column)
        self.splitter.setSizes([self.width()*2//3, self.width()//3])

        self.setCentralWidget(self.splitter)
        
        self.prompt_input_button.clicked.connect(self.show_answer)
        self.clear_history_button.clicked.connect(self.clear_history)
        self.history_button.clicked.connect(self.show_history_menu)
        
        self.fichiers_recents = deque(maxlen=5)
        #self.fichier_courant = None
        self.loadRecentFiles()
        
        self.init_ui()
        self.text_edit.sendToPromptSignal.connect(self.update_prompt_from_editor)
        self.create_new_tab()

    def init_ui(self):
        menubar = self.menuBar()
        fichierMenu = menubar.addMenu('Fichier')
        editMenu = menubar.addMenu('Edition')
        config_menu = menubar.addMenu("Configuration")
        
        nouveauAction = QAction('Nouveau', self)
        nouveauAction.setShortcut('Ctrl+N')
        nouveauAction.triggered.connect(self.nouveauFichier)
        fichierMenu.addAction(nouveauAction)
        
        fichierMenu.addSeparator()
        
        ouvrirAction = QAction('Ouvrir', self)
        ouvrirAction.setShortcut('Ctrl+O')
        ouvrirAction.triggered.connect(self.ouvrirFichier)
        fichierMenu.addAction(ouvrirAction)
        
        self.recentsMenu = QMenu('Fichiers Récents', self)
        fichierMenu.addMenu(self.recentsMenu)
        self.recentsMenu.aboutToShow.connect(self.afficherFichiersRecents)
        
        fichierMenu.addSeparator()
        
        enregistrerAction = QAction('Enregistrer', self)
        enregistrerAction.setShortcut('Ctrl+S')
        enregistrerAction.triggered.connect(self.enregistrerFichier)
        fichierMenu.addAction(enregistrerAction)
        
        enregistrerSousAction = QAction('Enregistrer sous', self)
        enregistrerSousAction.triggered.connect(self.enregistrerFichierSous)
        fichierMenu.addAction(enregistrerSousAction)
        
        fichierMenu.addSeparator()
        
        quitterAction = QAction('Quitter', self)
        quitterAction.setShortcut('Ctrl+Q')
        quitterAction.triggered.connect(self.close)
        fichierMenu.addAction(quitterAction)
        
        searchAction = QAction('Rechercher', self)
        searchAction.setShortcut('Ctrl+F')
        searchAction.triggered.connect(self.searchTextInEditor)

        replaceAction = QAction('Remplacer', self)
        replaceAction.setShortcut('Ctrl+H')
        replaceAction.triggered.connect(self.replaceTextInEditor)

        editMenu.addAction(searchAction)
        editMenu.addAction(replaceAction)
   
        general_config_action = QAction('Générale', self)
        general_config_action.triggered.connect(self.show_general_config_dialog)
        config_menu.addAction(general_config_action)
        editor_config_action = QAction("Editeur", self)
        editor_config_action.triggered.connect(self.show_editor_config_dialog)
        config_menu.addAction(editor_config_action)
        config_action = QAction("GPT", self)
        config_action.triggered.connect(self.show_config_dialog)
        config_menu.addAction(config_action)


        self.setWindowTitle("PyIDE")
        self.setGeometry(100, 100, 1000, 600)
        self.show()  # Affiche la fenêtre
        self.splitter.setSizes([self.width()*2//3, self.width()//3])  # Défini les tailles après que la fenêtre soit visible

    def customContextMenuRequested(self, location):
        menu = QMenu()
        send_to_editor_action = menu.addAction("Envoyer dans l'Éditeur")
        send_to_editor_action.triggered.connect(self.copyToEditor)
        menu.exec_(self.gpt_output.mapToGlobal(location))
        
    def copyToEditor(self):
        selected_text = self.gpt_output.textCursor().selectedText()
        
        current_tab = self.tab_widget.currentWidget()
        
        if current_tab:
            current_text_edit = current_tab.findChild(QPlainTextEdit)
            
            # Sauvegarde de la position actuelle du curseur
            cursor = current_text_edit.textCursor()
            pos_before_insert = cursor.position()
            
            # Insertion du texte à la position actuelle du curseur
            cursor.insertText(selected_text)
            pos_after_insert = cursor.position()
            
            # Sélection du texte ajouté
            cursor.setPosition(pos_before_insert, QTextCursor.MoveAnchor)
            cursor.setPosition(pos_after_insert, QTextCursor.KeepAnchor)
            
            # Mise à jour du curseur dans l'éditeur
            current_text_edit.setTextCursor(cursor)
            
            # Mise en focus de l'éditeur
            current_text_edit.setFocus()
        
    def update_prompt_from_editor(self, selected_text):
        existing_text = self.prompt_input.toPlainText()
        updated_text = existing_text + selected_text
        self.prompt_input.setPlainText(updated_text)

    def create_new_tab(self):
            # Créer un nouvel éditeur de texte
            new_text_edit = CustomTextEdit()
            
            # Créer une nouvelle instance de PythonHighlighter pour cet éditeur
            self.highlighter = PythonHighlighter(new_text_edit.document())
            
            # Lier le signal à la méthode update_prompt_from_editor
            new_text_edit.sendToPromptSignal.connect(self.update_prompt_from_editor)
    
            # Créer un layout pour l'éditeur de code
            layout = QVBoxLayout()
            layout.addWidget(new_text_edit)
            
            # Créer un widget et définir son layout
            widget = QWidget()
            widget.setLayout(layout)
            
            # Ajouter le widget au widget d'onglets
            self.tab_widget.addTab(widget, "Nouvel Onglet")
             
    def nouveauFichier(self):
        self.create_new_tab()
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

        
    def ouvrirFichier(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self,"Ouvrir", "", "Python Files (*.py);;Text Files (*.txt);;All Files (*)", options=options)
        if fileName:
            if self.tab_widget.count() == 0:  # Vérifier s'il n'y a pas d'onglet ouvert
                self.create_new_tab()  # Créer un nouvel onglet
            
            # Get the currently selected tab
            currentIndex = self.tab_widget.currentIndex()
            current_widget = self.tab_widget.currentWidget()
            text_edit = current_widget.layout().itemAt(0).widget()
    
            with open(fileName, 'r', encoding='utf-8') as file:
                text_edit.setPlainText(file.read())
            self.fichiers_recents.append(fileName)
    
            self.saveRecentFiles()
            self.fichier_courant[currentIndex] = fileName
    
            # Change the tab name to the name of the file
            baseName = os.path.basename(fileName)  # Get file name without directory
            self.tab_widget.setTabText(currentIndex, baseName)

    
    def enregistrerFichier(self, all_files=False):
        start = 0
        end = self.tab_widget.count()
    
        if not all_files:
            start = self.tab_widget.currentIndex()
            end = start + 1
    
        for index in range(start, end):
            # Get the current tab
            current_widget = self.tab_widget.widget(index)
    
            # Get its QTextEdit
            text_edit = current_widget.layout().itemAt(0).widget()
    
            current_file = self.fichier_courant.get(index)
    
            if current_file:
                with open(current_file, 'w', encoding='utf-8') as f:
                    f.write(text_edit.toPlainText())
            else:
                options = QFileDialog.Options()
                fichier, _ = QFileDialog.getSaveFileName(self, "Enregistrer le fichier", "", "Python Files (*.py);;Text Files (*.txt);;All Files (*)", options=options)
                if fichier:
                    with open(fichier, 'w', encoding='utf-8') as f:
                        f.write(text_edit.toPlainText())
                    self.fichier_courant[index] = fichier
                    self.fichiers_recents.append(fichier)
                
    def enregistrerFichierSous(self):
        # Get the currently selected tab
        currentIndex = self.tab_widget.currentIndex()
        current_widget = self.tab_widget.currentWidget()
    
        # Get its QTextEdit
        text_edit = current_widget.layout().itemAt(0).widget()
    
        options = QFileDialog.Options()
        fichier, _ = QFileDialog.getSaveFileName(self, "Enregistrer sous", "", "Python Files (*.py);;Text Files (*.txt);;All Files (*)", options=options)
        if fichier:
            with open(fichier, 'w', encoding='utf-8') as f:
                f.write(text_edit.toPlainText())
            self.fichier_courant[self.tab_widget.currentIndex()] = fichier
            self.fichiers_recents.append(fichier)
            self.saveRecentFiles()
            
            # Change the tab name to the name of the file
            baseName = os.path.basename(fichier)  # Get file name without directory
            self.tab_widget.setTabText(currentIndex, baseName)
            
    def closeEvent(self, event):
        # Check if the file has been modified since the last save
        if self.textHasBeenModified():  
            reply = QMessageBox.question(self, 'Message', "Les fichiers n'ont pas été sauvegardés !\nVoulez-vous le sauvegarder ?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
    
            if reply == QMessageBox.Yes:
                # Save all files before closing
                self.enregistrerFichier(all_files=True)
                event.accept()
            elif reply == QMessageBox.No:
                # Refuse to save and close the program
                event.accept()
            else:
                # Cancel and return to the program
                event.ignore()

    def closeTab(self, index):
        # Check if the text has been modified since the last save
        if self.textHasBeenModified():  
            reply = QMessageBox.question(self, 'Message',
                                         "Le fichier n'a pas été sauvegardé !\nVoulez-vous le sauvegarder ?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                # Save and close the tab
                self.enregistrerFichier()
                self.tab_widget.removeTab(index)
            elif reply == QMessageBox.No:
                # Close the tab without saving
                self.tab_widget.removeTab(index)
            else:
                # Cancel closing the tab
                return
        else:
            # If the text hasn't been modified, just close the tab
            self.tab_widget.removeTab(index)    
            
    def loadRecentFiles(self):
        if os.path.exists(self.FILENAME_RECENT_FILES):
            with open(self.FILENAME_RECENT_FILES, 'rb') as f:
                self.fichiers_recents = list(deque(pickle.load(f), maxlen=5))
    
    def saveRecentFiles(self):
        with open(self.FILENAME_RECENT_FILES, 'wb') as f:
            pickle.dump(list(self.fichiers_recents), f)
    
    def afficherFichiersRecents(self):
        self.recentsMenu.clear()
        def create_open_action(fichier):
            return lambda: self.ouvrirFichierRecent(fichier)
    
        for fichier in self.fichiers_recents:
            recentAction = QAction(fichier, self)
            recentAction.triggered.connect(create_open_action(fichier))
            self.recentsMenu.addAction(recentAction)
    
    def ouvrirFichierRecent(self, fileName):
        if self.tab_widget.count() == 0:  # Vérifier s'il n'y a pas d'onglet ouvert
            self.create_new_tab()  # Créer un nouvel onglet
        
        # Get the currently selected tab
        currentIndex = self.tab_widget.currentIndex()
        current_widget = self.tab_widget.currentWidget()
        text_edit = current_widget.layout().itemAt(0).widget()
    
        with open(fileName, 'r', encoding='utf-8') as file:
            self.fichier_courant[currentIndex] = fileName
            text_edit.setPlainText(file.read())
    
        # Supprime le fichier s'il existe déjà dans la liste
        if fileName in self.fichiers_recents:
            self.fichiers_recents.remove(fileName)
    
        # Ajoute le fichier au début de la liste
        self.fichiers_recents.insert(0, fileName)
        self.saveRecentFiles()
    
        # Change the tab name to the name of the file
        baseName = os.path.basename(fileName)  # Get file name without directory
        self.tab_widget.setTabText(currentIndex, baseName)

    def textHasBeenModified(self):
        # Get the currently selected tab
        current_widget = self.tab_widget.currentWidget()
    
        # Get the QTextEdit of that tab
        text_edit = current_widget.layout().itemAt(0).widget()
    
        return text_edit.document().isModified()

    def searchTextInEditor(self):
       current_widget = self.tab_widget.currentWidget()       
       self.searchDialog = SearchDialog(current_widget.layout().itemAt(0).widget(), self)  # passing parent as 'self'
       self.searchDialog.show()  # using show instead of open 

    def replaceTextInEditor(self):
        current_widget = self.tab_widget.currentWidget()
        replaceDialog = ReplaceDialog(current_widget.layout().itemAt(0).widget(), self)  
        replaceDialog.show()  
             
    def show_editor_config_dialog(self):
        editor = EditorConfigDialog()
        result = editor.exec_()
        if result == QDialog.Accepted:
            editor.save_config()     
        
    def show_config_dialog(self):
        dialog = ConfigDialog()
        result = dialog.exec_()
        if result == QDialog.Accepted:
            dialog.save_config()

    def show_general_config_dialog(self):
        dialog = GeneralConfigDialog()
        result = dialog.exec_()
        if result == QDialog.Accepted:
            dialog.save_config()
            
    def show_answer(self):
        question = self.prompt_input.toPlainText()
        
        if not question.strip():
            return
 
        response = self.run_gpt(question)  # Notez que run_gpt retourne une valeur maintenant
         
        code_blocks = re.split(r'\n\n```(?:python)?\s*\n((?:.*\n)*?)```', response)

        formatted_code_blocks = []
        for i in range(len(code_blocks)):
            if i % 2 == 0:
                code_blocks[i] = code_blocks[i].replace("\n", "<br>")
                formatted_code_blocks.append(code_blocks[i])
            else:
                code = code_blocks[i]
                formatted_code = highlight(code, PythonLexer(), HtmlFormatter(style='emacs', full=True, cssstyles=custom_style))
                formatted_code_blocks.append(f'{formatted_code}')

        response = "".join(formatted_code_blocks)
        html = f"<style>{custom_style}</style>{response}<br><br>"
        self.gpt_output.append(html)

    def build_messages(self):
        messages = [{"role": "system", "content": "Vous êtes un logiciel d'aide à la programmation en python."}]
        for q, r in zip(self.questions_history, self.reponses_history):
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": r})
        return messages

    def run_gpt(self, question):
        if not os.path.exists("config.json"):
            return "Configuration manquante."

        with open("config.json", "r") as file:
            config = json.load(file)
            api_key = config.get("api_key")
            model = config.get("model")

        openai.api_key = api_key

        self.questions_history.append(question)
        self.history_menu.addAction(question)
        
        messages = self.build_messages()
        messages.append({"role": "user", "content": question})

        completion = openai.ChatCompletion.create(
            model=model,
            messages=messages
        )

        reponse = completion.choices[0].message["content"]
        self.reponses_history.append(reponse)
        
        self.prompt_input.clear()
        self.prompt_input.setFocus()
        
        return reponse
    
    def copy_code(self):
        if not self.reponses_history:
            return
        # Copier le code Python dans le presse-papiers
        answer = self.reponses_history[-1]
        code_blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', answer, re.DOTALL)
        code_to_copy = ""
        for code in code_blocks:
            code_to_copy += f'{code}\n'
        QApplication.clipboard().set
        
    def run_code(self):
        # Obtenir le widget actuel (qui est le widget que vous ajoutez lors de la création d'un nouvel onglet)
        current_widget = self.tab_widget.currentWidget()
    
        # Trouver le QPlainTextEdit dans ce widget 
        # (en supposant que QPlainTextEdit soit le premier widget ajouté à la disposition du widget)
        text_edit = current_widget.layout().itemAt(0).widget()
        code = text_edit.toPlainText()
    
        # Création d'un fichier temporaire pour stocker le code
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp:
            temp.write(code.encode('utf-8'))
            temp_file_name = temp.name
    
        # Récupérer le chemin du fichier enregistré actuellement
        current_file_path = self.fichier_courant.get(self.tab_widget.currentIndex())
    
        # Obtenir le répertoire de ce fichier
        # Si aucun fichier n'a encore été sauvegardé pour cet onglet, se diriger vers le répertoire temporaire
        if current_file_path:
            current_directory = os.path.dirname(current_file_path)
        else:
            current_directory = os.path.dirname(temp_file_name)
        # Lancement du terminal pour exécuter le code
        subprocess.Popen(f"start cmd /k python {temp_file_name}", shell=True, cwd=current_directory)
    
    def show_history_menu(self):
        action = self.history_menu.exec_(self.history_button.mapToGlobal(self.history_button.rect().bottomLeft()))
        if action is not None:
            question = action.text()
            self.prompt_input.setText(question)
            self.prompt_input.setFocus()
            
    def clear_history(self):
        self.reponses_history = []
        self.questions_history = []
        self.gpt_output.clear()
        self.prompt_input.clear()
        self.history_menu.clear()
        self.prompt_input.setFocus()
                              
if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = SimpleIDE()
    editor.show()
    sys.exit(app.exec_()) 
