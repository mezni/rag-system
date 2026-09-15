


class PromptManager:
    """Manage and render prompts from YAML configuration."""

    def __init__(self, prompts_path: str = "config/prompts.yaml"):
        self.prompts_path = prompts_path
        import yaml

        with open(prompts_path, "r") as f:
            self.prompts = yaml.safe_load(f)

    def render(self, template_name: str, **kwargs) -> str:
        """Render a prompt template with the given context variables."""
        template = self.prompts.get(template_name, "")
        if template:
            return template.format(**kwargs)
        return template