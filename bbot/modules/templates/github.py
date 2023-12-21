from bbot.modules.templates.subdomain_enum import subdomain_enum


class github(subdomain_enum):
    """
    A template module for use of the GitHub API
    Inherited by several other github modules.
    """

    _qsize = 1
    base_url = "https://api.github.com"

    async def setup(self):
        await super().setup()
        self.api_key = None
        self.headers = {}
        for module_name in ("github", "github_codesearch", "github_org"):
            module_config = self.scan.config.get("modules", {}).get(module_name, {})
            api_key = module_config.get("api_key", "")
            if api_key:
                self.api_key = api_key
                self.headers = {"Authorization": f"token {self.api_key}"}
                break
        try:
            await self.ping()
            self.hugesuccess(f"API is ready")
            return True
        except Exception as e:
            return None, f"Error with API ({str(e).strip()})"
        if not self.api_key:
            if self.auth_required:
                return None, "No API key set"
        return True

    async def ping(self):
        url = f"{self.base_url}/zen"
        response = await self.helpers.request(url, headers=self.headers)
        assert getattr(response, "status_code", 0) == 200, response.text
