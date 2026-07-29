import os
import random
import time
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from dotenv import load_dotenv

load_dotenv()

CHROME_PROFILE_DIR = os.path.join(
    os.path.expanduser("~"), "Documents", "ECW_Chrome_Profile"
)


class HumanTyper:
    def __init__(self, min_delay=0.05, max_delay=0.15):
        self.min_delay = min_delay
        self.max_delay = max_delay

    def random_delay(self):
        return random.uniform(self.min_delay, self.max_delay)

    def type(self, element, text):
        element.click()
        time.sleep(self.random_delay())
        for char in text:
            element.send_keys(char)
            time.sleep(self.random_delay())


class ECWAutomation:
    def __init__(self):
        self.driver = None
        self.typer = HumanTyper()
        self._stop_event = threading.Event()
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self._monitor_thread = None
        self._seen_files = set()

    def stop(self):
        self._stop_event.set()

    @property
    def should_stop(self):
        return self._stop_event.is_set()

    def start(self):
        options = webdriver.ChromeOptions()
        profile_path = os.path.abspath(CHROME_PROFILE_DIR)
        options.add_argument(f"--user-data-dir={os.path.dirname(profile_path)}")
        options.add_argument(f"--profile-directory={os.path.basename(profile_path)}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()

        url = os.getenv("ECW_URL")
        if url:
            self.driver.get(url)

        return self

    def close(self):
        self.stop_download_monitor()
        if self.driver:
            self.driver.quit()
            self.driver = None

    def open(self, url):
        self.driver.get(url)

    def waiter(self, xpath, timeout=None):
        start = time.time()
        attempt = 0
        while True:
            if self.should_stop:
                return None
            attempt += 1
            try:
                el = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if el.is_displayed():
                    elapsed = time.time() - start
                    if attempt > 1:
                        print(f"    Element appeared in {elapsed:.1f}s")
                    return el
            except Exception:
                pass
            if timeout is not None and time.time() - start > timeout:
                raise TimeoutException(
                    f"Element not found within {timeout}s: {xpath}"
                )
            if attempt % 10 == 0:
                print(f"    Waiting... (attempt {attempt}, {time.time()-start:.0f}s)")
            time.sleep(0.5)

    def sender(self, xpath, text, timeout=None):
        start = time.time()
        attempt = 0
        while True:
            if self.should_stop:
                return
            attempt += 1
            try:
                el = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", el
                )
                time.sleep(0.2)
                self.typer.type(el, text)
                elapsed = time.time() - start
                if attempt > 1:
                    print(f"    Typed after {elapsed:.1f}s (attempt {attempt})")
                return
            except Exception:
                pass
            if timeout is not None and time.time() - start > timeout:
                raise TimeoutException(
                    f"Could not type into element after {timeout}s: {xpath}"
                )
            if attempt % 5 == 0:
                elapsed = time.time() - start
                print(f"    Waiting for element... (attempt {attempt}, {elapsed:.0f}s)")
            time.sleep(1)

    def clicker(self, xpath, timeout=None):
        start = time.time()
        attempt = 0
        while True:
            if self.should_stop:
                return
            attempt += 1
            try:
                el = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", el
                )
                time.sleep(0.2)
                el.click()
                time.sleep(self.typer.random_delay())
                elapsed = time.time() - start
                if attempt > 1:
                    print(f"    Clicked after {elapsed:.1f}s (attempt {attempt})")
                return
            except Exception:
                pass
            if timeout is not None and time.time() - start > timeout:
                raise TimeoutException(
                    f"Could not click element after {timeout}s: {xpath}"
                )
            if attempt % 5 == 0:
                elapsed = time.time() - start
                print(f"    Waiting for element... (attempt {attempt}, {elapsed:.0f}s)")
            time.sleep(1)

    def checker(self, xpath, timeout=5):
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return el.is_displayed()
        except Exception:
            return False

    def hotkey(self, keys):
        actions = ActionChains(self.driver)
        for k in keys:
            key_name = k.upper()
            key = getattr(Keys, key_name, k)
            actions.key_down(key)
        for k in keys:
            key_name = k.upper()
            key = getattr(Keys, key_name, k)
            actions.key_up(key)
        actions.perform()
        time.sleep(self.typer.random_delay())

    def key(self, key):
        key_name = key.upper()
        k = getattr(Keys, key_name, key)
        actions = ActionChains(self.driver)
        actions.send_keys(k)
        actions.perform()
        time.sleep(self.typer.random_delay())

    def table_clicker(self, table_xpath, cell_xpath, match_text, timeout=None, row_cell=None, row_text=None):
        start = time.time()
        attempt = 0
        while True:
            if self.should_stop:
                return
            attempt += 1
            try:
                table = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, table_xpath))
                )
                rows = table.find_elements(By.XPATH, ".//tr")
                for row_idx, row in enumerate(rows, 1):
                    try:
                        cell = WebDriverWait(row, 1).until(
                            EC.presence_of_element_located((By.XPATH, cell_xpath))
                        )
                        cell_text = cell.text.strip()
                        if match_text is None or match_text in cell_text:
                            if row_cell and row_text:
                                try:
                                    rc = WebDriverWait(row, 0.5).until(
                                        EC.presence_of_element_located((By.XPATH, row_cell))
                                    )
                                    if row_text.lower() not in rc.text.strip().lower():
                                        continue
                                except Exception:
                                    continue
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});", row
                            )
                            time.sleep(0.3)
                            row.click()
                            elapsed = time.time() - start
                            if attempt > 1:
                                print(f"    Row {row_idx} clicked after {elapsed:.1f}s (attempt {attempt})")
                            return
                        if attempt == 1 and row_idx <= 5:
                            print(f"    Row {row_idx} cell: {repr(cell_text)}")
                    except Exception:
                        if attempt == 1 and row_idx <= 5:
                            print(f"    Row {row_idx}: cell not found at '{cell_xpath}'")
                        continue
            except Exception:
                pass
            if timeout is not None and time.time() - start > timeout:
                raise TimeoutException(
                    f"Table row with text '{match_text}' not found after {timeout}s: {table_xpath}"
                )
            if attempt == 1:
                print(f"    No match found in {len(rows)} rows. Retrying...")
            elif attempt % 5 == 0:
                elapsed = time.time() - start
                print(f"    Scanning table rows... (attempt {attempt}, {elapsed:.0f}s)")
            time.sleep(1)

    def fill_icd(self, codes, xpath):
        for code in codes:
            if self.should_stop:
                break
            import re
            code_clean = re.sub(r"[^A-Z0-9.]", "", code.upper())
            if not code_clean:
                continue
            el = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            self.typer.type(el, code_clean)
            time.sleep(random.uniform(0.3, 0.8))
            self.key("TAB")
            time.sleep(random.uniform(0.3, 0.6))

    def switch_to_iframe(self, xpath, timeout=None):
        start = time.time()
        attempt = 0
        while True:
            if self.should_stop:
                return
            attempt += 1
            try:
                el = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                self.driver.switch_to.frame(el)
                elapsed = time.time() - start
                if attempt > 1:
                    print(f"    Switched to iframe after {elapsed:.1f}s (attempt {attempt})")
                return
            except Exception:
                pass
            if timeout is not None and time.time() - start > timeout:
                raise TimeoutException(
                    f"Could not switch to iframe after {timeout}s: {xpath}"
                )
            if attempt % 5 == 0:
                elapsed = time.time() - start
                print(f"    Waiting for iframe... (attempt {attempt}, {elapsed:.0f}s)")
            time.sleep(1)

    def switch_to_default(self):
        self.driver.switch_to.default_content()

    def switch_to_parent(self):
        self.driver.switch_to.parent_frame()

    def clean(self, xpath, timeout=None):
        start = time.time()
        attempt = 0
        while True:
            if self.should_stop:
                return
            attempt += 1
            try:
                el = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", el
                )
                time.sleep(0.2)
                el.click()
                actions = ActionChains(self.driver)
                actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL)
                actions.send_keys(Keys.DELETE)
                actions.perform()
                time.sleep(self.typer.random_delay())
                elapsed = time.time() - start
                if attempt > 1:
                    print(f"    Cleaned after {elapsed:.1f}s (attempt {attempt})")
                return
            except Exception:
                pass
            if timeout is not None and time.time() - start > timeout:
                raise TimeoutException(
                    f"Could not clean element after {timeout}s: {xpath}"
                )
            if attempt % 5 == 0:
                elapsed = time.time() - start
                print(f"    Waiting to clean element... (attempt {attempt}, {elapsed:.0f}s)")
            time.sleep(1)

    def _poll_downloads(self, interval, on_complete):
        os.makedirs(self.download_dir, exist_ok=True)
        while not self.should_stop:
            try:
                current = set(os.listdir(self.download_dir))
                new_files = current - self._seen_files
                for f in new_files:
                    fpath = os.path.join(self.download_dir, f)
                    if not f.endswith(".crdownload") and os.path.isfile(fpath):
                        print(f"    Downloaded: {f}")
                        self._seen_files.add(f)
                        if on_complete:
                            on_complete(fpath)
                self._seen_files.update(new_files)
            except Exception:
                pass
            time.sleep(interval)

    def start_download_monitor(self, interval=0.5, on_complete=None):
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._seen_files = set()
        if os.path.isdir(self.download_dir):
            self._seen_files.update(os.listdir(self.download_dir))
        self._monitor_thread = threading.Thread(
            target=self._poll_downloads, args=(interval, on_complete), daemon=True
        )
        self._monitor_thread.start()
        print(f"    Download monitor started (dir: {self.download_dir})")

    def stop_download_monitor(self):
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)
            self._monitor_thread = None
            print("    Download monitor stopped")
