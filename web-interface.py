import os
import subprocess
import json
import re
import remi.gui as gui
from remi import start, App

class MyApp(App):
    
    regExPattern = '^(?:[a-zA-Z]+,)*[a-zA-Z]+$'
    pathToStockTicker = os.path.abspath("led-stock-ticker/main.py")
    stockTickerStartCmd = 'sudo python3 ' + pathToStockTicker + '--led-rows 16 --led-cols 16 --led-gpio-mapping adafruit-hat'
    stockTickerStartCmd = stockTickerStartCmd.split(' ')
    pid = 0
    ledBrightness = 75
    firstRun = True

    def start_display(self, displayBrightness):
        self.bt_StopDisplay.set_enabled(True)
        startCmd = self.stockTickerStartCmd
        startCmd.extend(['--led-brightness', str(displayBrightness)])
        stockTickerProcess = subprocess.Popen(self.stockTickerStartCmd, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        self.pid = stockTickerProcess.pid
    
    def stop_display(self):
        os.system("sudo kill %s" % (self.pid, ))
        self.bt_StopDisplay.set_enabled(False)

    def update_display(self, tickerSymbols):
        with open('/home/pi/my-led-stock-ticker/led-stock-ticker/config/default_config.json', 'r') as file:
            data = json.load(file)
            data['tickers']['stocks'] = tickerSymbols.split(',')
        
        with open('/home/pi/my-led-stock-ticker/led-stock-ticker/config/config.json', 'w') as file:
            json.dump(data, file)

    def __init__(self, *args):
        super(MyApp, self).__init__(*args)
    
    def main(self):
        # define overall container
        VerticalContainer = gui.Container(width="400px", margin='0px auto', style={'display': 'block', 'overflow': 'hidden'})
        VerticalContainer.css_align_items = 'center'
        VerticalContainer.css_top = '20px'

        # define the Header
        HeaderViewbox = gui.VBox(width='100%', height='100%', margin='0px auto')
        self.headerLabel = gui.Label('Stock Ticker Control', width='auto', height='auto', style={'font-size':'30px', 'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'word-wrap': 'normal'})
        HeaderViewbox.append(self.headerLabel)

        #define the Main View
        MainViewBox = gui.VBox(width='100%', height='100%', margin='0px auto')

        #creating a text label, "white-space":"pre" preserves newline
        self.lbl_StaticInstructions = gui.Label('Enter Ticker Symbols as a Comma-Seperated List, followed by the enter/return key', width='75%', height='auto', style={'text-align': 'center'})
        self.lbl_StaticInstructions.css_flex_wrap = "wrap"

        # Ticker Input Box
        self.txt_TickerInput = gui.TextInput(width='75%', height=30, margin='10px')
        self.txt_TickerInput.set_text('GOOGL,AAPL,MSFT')
        self.txt_TickerInput.onchange.do(self.on_text_area_change)

        # User Info
        self.lbl_UserInfo = gui.Label('', width='75%', height=40, style={'text-align': 'center'})

        # Brightness Adjustment Slider
        self.lbl_BrightnessInstructions = gui.Label('Adjust LED Brightness (requires Display Update):', width='100%', height=30, style={'text-align': 'center'})
        self.slider_LedBrightness = gui.Slider(75, 0, 100, 5, width=200, height=40, margin='10px')
        self.slider_LedBrightness.onchange.do(self.slider_LedBrightness_changed)
        
        # Define buttons
        self.bt_DisplayUpdate = gui.Button('Update Display', width=200, height=30, margin='10px', color='green')
        self.bt_DisplayUpdate.onclick.do(self.bt_DisplayUpdate_Pressed)
        self.bt_StopDisplay = gui.Button('STOP the Display', width=150, height=30, margin='10px')
        self.bt_StopDisplay.css_background_color = "rgb(163,0,0)"
        self.bt_StopDisplay.onclick.do(self.bt_StopDisplay_Pressed)
        self.lbl_DisplayStatus = gui.Label('Display Status: Off', width='100%', height='10%', padding="20px", style={"white-space":"pre", 'text-align': 'center', 'word-wrap': 'normal'})

        #HeaderViewBox.append(self.headerLabel)

        if self.firstRun:
            self.bt_StopDisplay.set_enabled(False)
            self.bt_DisplayUpdate.set_enabled(False)
            self.firstRun = False

        MainViewBox.append(self.lbl_StaticInstructions)
        MainViewBox.append(self.txt_TickerInput)
        MainViewBox.append(self.lbl_UserInfo)
        MainViewBox.append(self.lbl_BrightnessInstructions)
        MainViewBox.append(self.slider_LedBrightness)
        MainViewBox.append(self.bt_DisplayUpdate)
        MainViewBox.append(self.lbl_DisplayStatus)
        MainViewBox.append(self.bt_StopDisplay)

        VerticalContainer.append([HeaderViewbox,MainViewBox])
        
        return VerticalContainer
    

    def bt_DisplayUpdate_Pressed(self, widget):
        widget.set_enabled(False)
        self.lbl_DisplayStatus.set_text('Updating Display...')
        if(self.pid != 0):
            self.stop_display()
        self.update_display(self.txt_TickerInput.text)
        self.start_display(self.ledBrightness)
        self.lbl_DisplayStatus.set_text('Displaying: ' + self.txt_TickerInput.text)
        widget.set_enabled(True)

    def bt_StopDisplay_Pressed(self, widget):
        self.lbl_DisplayStatus.set_text('Attemping to STOP Display...')
        self.stop_display()
        self.lbl_DisplayStatus.set_text('Display Status: Off')


    def on_text_area_change(self, widget, newValue):
        isCommaSeperatedList = re.match(self.regExPattern, newValue)
        if(isCommaSeperatedList):
            self.lbl_UserInfo.set_text('Press Update Display to show new values: ' + newValue)
            widget.css_border_color = "rgb(255,255,255)"
            self.bt_DisplayUpdate.set_enabled(True)
        else:
            self.lbl_UserInfo.set_text('Invalid Ticker Entry')
            widget.css_border_color = "rgb(255,0,0)"
            self.bt_DisplayUpdate.set_enabled(False)

    def slider_LedBrightness_changed(self, widget, newBrightnessValue):
        self.ledBrightness = newBrightnessValue

if __name__ == "__main__":
    # starts the webserver
    # optional parameters
    # start(MyApp,address='127.0.0.1', port=8081, multiple_instance=False,enable_file_cache=True, update_interval=0.1, start_browser=True)
    start(MyApp, debug=True, address='0.0.0.0', port=8081, start_browser=False, multiple_instance=False)