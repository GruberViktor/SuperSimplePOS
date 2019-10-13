# -*- Encoding: UTF-8 -*-

from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration

import os.path
import sys
import cups
import json
import kivy
import re
import csv
from datetime import datetime
from kivy.properties import NumericProperty
from kivy.app import App

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from functools import partial
from kivy.core.window import Window


conn = cups.Connection()

font_config = FontConfiguration()

global produktliste
produktliste = [
    {
    "name": "Helles Miso",
    "preis": 9.90
    },
    {
    "name": "Helle Sojasauce",
    "preis": 9.90
    },
    {
    "name": "Kürbiskernmiso",
    "preis": 9.60
    },
    {"name": "Mohnmiso",
    "preis": 9.90
    },
    {
    "name": "Kürbiskernshoyu",
    "preis": 9.90
    }]

class produktbuttons(GridLayout):
    total = NumericProperty()
    def __init__(self, **kwargs):
        super(produktbuttons, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.keybindings = {}

        self.cols = len(produktliste)
        for i in range(len(produktliste)):
            self.button = Button(text="{0}\n{1}".format(i+1,produktliste[i]["name"]),
                font_size=28, 
                halign='center',
                on_press=partial(self.add_to_cart, produktliste[i]["name"], produktliste[i]["preis"]))
            self.add_widget(self.button)

            self.keybindings[i+49] = {}
        print(self.keybindings)

        self.warenkorb = []

        self.warenliste = []
        self.warenlistelabel = Label(font_size=28)
        self.add_widget(self.warenlistelabel)

        self.total = 0
        self.Summe = Label(text="Total: {:.2f}".format(self.total),font_size=28)
        self.add_widget(self.Summe)

        self.finalizebutton = Button(text="Finalize", on_press=self.finalize,font_size=28,background_color=[23/255,180/255,9/255,0.5],background_normal='')
        self.add_widget(self.finalizebutton)

        self.cancel = Button(text="Cancel", on_press=self.resetsession,font_size=28,background_color=[242/255,59/255,59/255,0.5],background_normal='')
        self.add_widget(self.cancel)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print('The key', keycode, 'have been pressed')
        print(' - text is %r' % text)
        print(' - modifiers are %r' % modifiers)
        if keycode[0] in self.keybindings:
            self.add_to_cart(produktliste[keycode[0]-49]["name"], produktliste[keycode[0]-49]["preis"],"???")
        if text == 'c':
            self.resetsession("???")
        if keycode[0] == 13:
            self.finalize("???")
        if keycode[0] == 113 and modifiers[0] == 'ctrl':
            quit()
        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        #if keycode[1] == 'escape':
        #    keyboard.release()

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True
    def _keyboard_closed(self):
        print('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def proceeds_writer(self):
        proceeds_csv = open('proceeds.csv', 'a')
        proceeds_writer = csv.writer(proceeds_csv)
        product_list_for_csv = []
        for i in range(len(self.warenkorb)):
            product_list_for_csv.append("{0}x {1}".format(self.warenkorb[i]["count"],self.warenkorb[i]["name"]))
        proceeds_writer.writerow(["pos-{}".format(self.rechnungsnummer),self.now,', '.join(product_list_for_csv),"{:.2f}".format(self.total),"{:.2f}".format(self.netto)])
        proceeds_csv.close()

    def resetsession(self,button):
        self.warenkorb = []
        self.totalize()
        self.update()

    def update(self):
        self.warenliste = []
        for i in range(len(self.warenkorb)):
                item = "{0}x {1}\n".format(self.warenkorb[i]["count"],self.warenkorb[i]["name"])
                self.warenliste.append(item)
        self.warenlistelabel.text="{}".format(''.join(self.warenliste))
        self.Summe.text="Total: {:.2f}".format(self.total)

    def add_to_cart(self,name,preis,button):
        if not any(d['name'] == name for d in self.warenkorb):
            self.warenkorb.append({"name" : name, "preis": preis, "count": 1})
            print(self.warenkorb)
        else:
            for i, dic in enumerate(self.warenkorb):
                if dic["name"] == name:
                    nummer = i
            self.warenkorb[nummer]["count"] += 1
        self.totalize()
        self.update()

    def totalize(self):
        self.total = 0
        for i in range(len(self.warenkorb)):
            self.total += self.warenkorb[i]["preis"]*self.warenkorb[i]["count"]
        print(self.total)
        self.netto = self.total/1.1


    def finalize(self,button):
        if len(self.warenkorb) > 0:
            def countParagraphs(input):
                linecount = 0
                for i in input:
                    if "\n" in i:
                        linecount += 1
                return linecount

            files = os.listdir("rechnungen")
            self.rechnungsnummer = len(files)
            self.now = datetime.now().strftime("%d.%m.%Y %H:%M")

            liste = []

            for i in range(len(self.warenkorb)):
                item = "{0}x {1} <span class='rechts'>{2:.2f}€</span><br>\n".format(self.warenkorb[i]["count"],self.warenkorb[i]["name"],self.warenkorb[i]["preis"] * self.warenkorb[i]["count"])
                liste.append(item)
            print(''.join(liste))

            beleg = """<html><body> <center><img src="{0}" style="height:100px;margin:0px 0px -5px 0;transform:translateY(-5px)" ></center>
                <center>LUVI Fermente KG
                <strong>www.luvifermente.eu</strong><br>
                <span class="kleineschrift">Gallabergerstr. 28, 4860 Lenzing<br>UID: ATU74182939</span></center><p>
                {1}
                <div style="height:2px; width:100%; background-color:#000; margin-top: -10px;margin-bottom:2px;"></div>
                Gesamt: <span class="rechts">{2:.2f}€</span><br>
                <span class="kleineschrift">Netto: {3:.2f}€</span> <span class="rechts kleineschrift">10% MWSt.: {4:.2f}€</span>
                <br>
                <span class="kleineschrift rechts" style="margin-top:5px">{5}<br>Belegnr.: pos-{6}</span>

                </body></html>""".format(os.path.abspath("logo.png"),''.join(liste),self.total,self.netto,self.total - self.netto, self.now, self.rechnungsnummer)

            laenge = 27 + ( countParagraphs(beleg) -1 ) * 5 + 5

            sourceCSS = CSS(string="""
                @page { size: 57.86mm %smm; margin: 0mm 3.5mm 0mm 3.5mm; } 
                body {
                    font-family: Verdana;
                    font-size: 12px;
                    }
                hr {
                    border-top: 2px solid black;
                    margin: -11px 0px 0px 0px;
                }
                .kleineschrift {
                    margin-top: 3px;
                    font-size: 9px;
                }
                .rechts {
                    float: right;
                }

                """ % laenge, font_config=font_config)
            doc = HTML(string=beleg, base_url=".")
            
            doc.write_pdf('rechnungen/pos-{}.pdf'.format(self.rechnungsnummer), stylesheets=[sourceCSS], font_config=font_config)

            file = os.path.abspath("rechnungen/pos-{}.pdf".format(self.rechnungsnummer))

            #conn.printFile("pos",file,"Test",{"media":"57.86x%smm" % laenge})
            #print(json.dumps(conn.getPrinterAttributes("pos"),sort_keys=True, indent=4))
            self.proceeds_writer()
            self.resetsession("???")
        else:
            print("Warenkorb ist leer")

class interface(App):
    def build(self):
        return produktbuttons()


if __name__ == '__main__':
    interface().run()