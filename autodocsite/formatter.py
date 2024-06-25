IGNORE = [""]  # Add cogs you want to ignore here

class CustomCmdFmt:
    def __init__(self, bot, cmd, prefix, replace_botname, extended_info, max_privilege_level, embedding_style, min_privilage_level):
        self.bot = bot
        self.cmd = cmd
        self.prefix = prefix
        self.replace_botname = replace_botname
        self.extended_info = extended_info
        self.max_privilege_level = max_privilege_level
        self.embedding_style = embedding_style
        self.min_privilage_level = min_privilage_level

    def get_doc(self):
        # Implement your documentation formatting logic here
        doc = f"### {self.cmd.qualified_name}\n\n"
        doc += f"**Description:** {self.cmd.help}\n\n"
        doc += f"**Usage:** `{self.prefix}{self.cmd.qualified_name}`\n\n"
        return doc
