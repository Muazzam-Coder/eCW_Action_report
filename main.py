from ecw_automation import ECWAutomation
from process_excel import export_filtered_excel
from logger import setup_logging
import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
import time
load_dotenv()
setup_logging()

NAMES = ['Dimachkie', 'Enakuaa', 'Patel, Gunjan Silky']

ecw = ECWAutomation()
ecw.start()

ecw.open(os.getenv("ECW_URL"))
ecw.sender('//*[@id="username"]', os.getenv('ECW_USERNAME'))
ecw.sender('//*[@id="password"]', os.getenv('ECW_USER_PASSWORD'))
ecw.clicker('//*[@id="loginButton"]')
print("Login Successful")
ecw.switch_to_iframe('/html/body/div[2]/div[2]/div[2]/div[2]/div/div[2]/iframe')
print("Switched to iframe")
ecw.clean('/html/body/form[1]/table/tbody/tr[2]/td/div/div/table/tbody/tr[2]/td/div/table/tbody/tr/td[1]/div[1]/table/tbody/tr[3]/td/div/div[1]/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]/input')
ecw.sender('/html/body/form[1]/table/tbody/tr[2]/td/div/div/table/tbody/tr[2]/td/div/table/tbody/tr/td[1]/div[1]/table/tbody/tr[3]/td/div/div[1]/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]/input', '01/01/2026')
ecw.clicker('/html/body/form[1]/table/tbody/tr[2]/td/div/div/table/tbody/tr[3]/td/table/tbody/tr/td[1]/div[1]/button')
ecw.switch_to_default()
ecw.clicker('/html/body/div[2]/div[2]/div[1]/div[1]/div[5]/button')
ecw.clicker('/html/body/div[7]/ul/li[4]/button/a')
print('download started')
ecw.start_download_monitor(on_complete=lambda f: export_filtered_excel(NAMES, source_path=f))

time.sleep(500)
ecw.close()
