# bot.py
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from utils import log_message, resource_path

class Bot:
    def __init__(self, app, log_callback):
        """
        app: reference to App instance (so bot dapat update stats)
        log_callback: function untuk log (contoh: utils.log_message)
        """
        self.app = app
        self.log = log_callback
        self.driver = None
        self.running = False

    def setup_bot(self):
        try:
            self.log(self.app, "Setting up bot (install chrome driver + launch browser)...")
            chromedriver_autoinstaller.install()
            chrome_options = Options()
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--window-size=1280,800")
            # minimal stealth flags (you can expand)
            chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            # optional allow insecure origin if needed
            chrome_options.add_argument('--allow-running-insecure-content')

            self.driver = webdriver.Chrome(options=chrome_options)

            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        try { Object.defineProperty(navigator, 'platform', { get: () => 'Win32' }); } catch(e){}
                    """
                })
            except Exception as e:
                self.log(self.app, f"Stealth injection warning: {e}")

            # clear session state
            try:
                self.driver.delete_all_cookies()
            except:
                pass

            # Open target page (LET THE USER SOLVE CAPTCHA MANUALLY)
            self.driver.get("https://nreer.com")
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self.log(self.app, "Browser opened. Silakan selesaikan CAPTCHA secara manual di browser yang muncul.")
            self.log(self.app, "Setelah selesai CAPTCHA, tekan tombol START di aplikasi untuk menjalankan bot.")
        except Exception as e:
            self.log(self.app, f"Error setup_bot: {e}")

    def human_move_and_click(self, element):
        try:
            self.driver.execute_script("""
                const el = arguments[0];
                const r = el.getBoundingClientRect();
                const x = r.left + r.width * (0.25 + Math.random()*0.5);
                const y = r.top + r.height * (0.25 + Math.random()*0.5);
                el.dispatchEvent(new MouseEvent('mousemove', {bubbles:true, clientX: x, clientY: y}));
                setTimeout(()=>{ el.click(); }, 80 + Math.random()*120);
            """, element)
            time.sleep(0.12 + random.random()*0.25)
        except Exception:
            try:
                element.click()
            except Exception as e:
                self.log(self.app, f"click fallback error: {e}")

    def safe_find_click(self, xpath, timeout=10):
        """Find clickable element by xpath and click it; return True if clicked."""
        try:
            btn = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            self.human_move_and_click(btn)
            return True
        except Exception:
            return False

    def read_countdown_seconds(self):
        """Try read <span id='min'> and <span id='sec'>. Return total seconds or 0."""
        try:
            min_t = int(self.driver.find_element(By.XPATH, "//span[@id='min']").text)
            sec_t = int(self.driver.find_element(By.XPATH, "//span[@id='sec']").text)
            return min_t * 60 + sec_t
        except Exception:
            return 0

    def wait_countdown_if_present(self, max_wait=900):
        """
        If countdown elements present and >0, wait until they expire (with safety cap).
        Returns True if waited, False if not present.
        """
        try:
            # quick check presence
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//span[@id='min' or @id='sec']"))
            )
        except:
            return False

        total = self.read_countdown_seconds()
        if total <= 0:
            return False

        wait_time = min(total + 2, max_wait)
        self.log(self.app, f"Detected countdown — waiting {wait_time} seconds...")
        time.sleep(wait_time)
        return True

    def loop(self, vidUrl, mode, amount):
        """
        Main loop. This function WILL ONLY START AFTER user menekan Start di app.
        It follows the flow:
          - At beginning of each iter: if countdown present => wait
          - If no countdown and input visible => insert URL -> Search -> click mode button
          - After clicking mode button, wait countdown if present, update stats, repeat until amount satisfied
        """
        if not self.driver:
            self.log(self.app, "Driver not initialized. Please press Setup first.")
            return

        self.running = True
        self.log(self.app, f"Bot started (mode={mode}, amount={amount})")
        sent = 0
        start_time = time.time()

        # mapping mode -> xpath (adjust if site berbeda)
        mode_map = {
            "Views":  "//button[@data-type='views']",
            "Hearts": "//button[@data-type='hearts']",
            "Followers": "//button[@data-type='followers']",
            "Shares": "//button[@data-type='shares']",
            "Favorites": "//button[@data-type='favorites']"
        }
        xpath_btn = mode_map.get(mode, mode_map["Hearts"])

        while self.running and (amount <= 0 or sent < amount):
            try:
                # 1) if countdown present at start, wait
                self.wait_countdown_if_present(max_wait=900)

                # 2) ensure we are at state that allows URL input OR clickable Use button
                input_present = False
                try:
                    input_box = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter URL']"))
                    )
                    input_present = True
                except:
                    input_present = False

                # If input not present, maybe need to click left USE to enter
                if not input_present:
                    clicked = self.safe_find_click("(//button[contains(@class,'btn') and contains(text(),'Use')])[1]", timeout=4)
                    if clicked:
                        # small wait for input to appear
                        try:
                            input_box = WebDriverWait(self.driver, 6).until(
                                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter URL']"))
                            )
                            input_present = True
                        except:
                            input_present = False

                if not input_present:
                    # nothing we can do now, wait a bit and retry
                    self.log(self.app, "Input box not available yet — retrying shortly...")
                    time.sleep(3)
                    continue

                # 3) insert url & search
                try:
                    input_box.clear()
                    input_box.send_keys(vidUrl)
                    self.log(self.app, f"Inserted URL: {vidUrl}")
                except Exception:
                    self.log(self.app, "Failed to write URL into input.")
                    time.sleep(2)
                    continue

                # click Search
                clicked_search = self.safe_find_click("//button[contains(text(),'Search')]", timeout=8)
                if not clicked_search:
                    self.log(self.app, "Search button not found/clickable. Retrying...")
                    time.sleep(3)
                    continue
                self.log(self.app, "Search clicked.")
                time.sleep(1.5 + random.random()*1.0)

                # 4) click mode button (heart/views/..)
                clicked_send = False
                try:
                    # try primary xpath first
                    clicked_send = self.safe_find_click(xpath_btn, timeout=8)
                    if not clicked_send:
                        # fallback try data-type contains mode lowercase
                        fallback = f"//button[contains(translate(@data-type,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{mode.lower()}')]"
                        clicked_send = self.safe_find_click(fallback, timeout=6)
                except Exception:
                    clicked_send = False

                if not clicked_send:
                    # try generic heart-like button as last resort
                    clicked_send = self.safe_find_click("//button[@data-type='hearts' or contains(@title,'heart')]", timeout=6)

                if clicked_send:
                    sent += 1
                    # update app counters based on mode
                    if mode == "Views":
                        self.app.views += 1
                    elif mode == "Hearts":
                        self.app.hearts += 1
                    elif mode == "Followers":
                        self.app.followers += 1
                    elif mode == "Shares":
                        self.app.shares += 1
                    elif mode == "Favorites":
                        self.app.favorites += 1

                    self.log(self.app, f"Action performed: {mode} (total sent: {sent})")
                else:
                    self.log(self.app, f"Failed to click {mode} button. Will retry.")
                    time.sleep(3)
                    continue

                # 5) after action, wait for countdown if site enforces it
                self.wait_countdown_if_present(max_wait=900)

                # small random pause between iterations
                time.sleep(1.0 + random.random()*1.5)

                # === DETECT THEN CLOSE WITH ESC ===
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(@class,'modal') and contains(@class,'show')]")
                        )
                    )
                    time.sleep(0.3)  # tunggu animasi modal
                    self.driver.execute_script(
                        "document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}));"
                    )
                    self.log(self.app, "Modal detected & closed with ESC.")
                except:
                    pass

                # === WAIT COUNTDOWN ===
                self.wait_countdown_if_present(max_wait=900)
                time.sleep(random.uniform(1.0, 2.0))

            except Exception as e:
                self.log(self.app, f"Loop unexpected error: {e}")
                time.sleep(3)
                continue



        elapsed = int(time.time() - start_time)
        self.log(self.app, f"Bot loop ended. Sent {sent} {mode}. Elapsed {elapsed}s")
        self.running = False
