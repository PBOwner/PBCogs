import discord
from redbot.core import commands
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import tempfile

class Screenshot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="screenshot", with_app_command=True, description="Takes a screenshot of the provided website URL.")
    async def screenshot(self, ctx: commands.Context, url: str):
        await ctx.send("Taking screenshot...")

        # Set up Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=ChromeService(), options=options)

        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            screenshot_path = os.path.join(tempfile.gettempdir(), "screenshot.png")
            driver.save_screenshot(screenshot_path)
            await ctx.send(file=discord.File(screenshot_path))
        except TimeoutException:
            await ctx.send("Failed to load the website within the timeout period.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
        finally:
            driver.quit()
