from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

class BrowserSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BROWSER_", env_file=".env", extra="ignore")
    chrome_channel: str = "chrome"
    chrome_profile: Path = PROJECT_ROOT / "automations" / "playwright" / "chrome_profile"
    headless: bool = False


class SalesforceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SF_", env_file=".env", extra="ignore")
    base_salesforce_url: str = "https://fullsail2.lightning.force.com/"
    duo_host_pattern: str = "**://*.duosecurity.com/*"
    sf_host_pattern: str = "**://*.lightning.force.com/*"
    username: str | None = None
    password: str | None = None

class NSLDSSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NSLDS_", env_file=".env", extra="ignore")
    base_url: str = "https://nsldsfap.ed.gov/"
    username: str | None = None
    password: str | None = None

class AppSettings(BaseModel):
    browser: BrowserSettings
    salesforce : SalesforceSettings
    nslds: NSLDSSettings

@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings(
        browser=BrowserSettings(),
        salesforce=SalesforceSettings(),
        nslds=NSLDSSettings(),
    )