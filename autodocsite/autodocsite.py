import os
import shutil
import logging
from io import BytesIO
from typing import List, Literal, Optional, Tuple
import yaml

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n, set_contextual_locales_from_guild

from .formatter import IGNORE, CustomCmdFmt

log = logging.getLogger("fb.fbcogs.autodocsite")
_ = Translator("AutoDocs", __file__)

# redgettext -D autodocs.py converters.py formatter.py
@cog_i18n(_)
class AutoDocSite(commands.Cog):
    """
    Automatically generate a documentation site for every cog in the bot.
    """

    def format_help_for_context(self, ctx):
        helpcmd = super().format_help_for_context(ctx)
        txt = _("{}\nCog Version: {}\nAuthor: {}").format(helpcmd, self.__version__, self.__author__)
        return txt

    async def red_delete_data_for_user(self, *, requester, user_id: int):
        """No data to delete"""

    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    def generate_readme(
        self,
        cog: commands.Cog,
        prefix: str,
        replace_botname: bool,
        extended_info: bool,
        include_hidden: bool,
        include_help: bool,
        max_privilege_level: str,
        min_privilege_level: str = "user",
        embedding_style: bool = False,
    ) -> str:
        docs = ""
        cog_name = cog.qualified_name
        if include_help:
            helptxt = _("Help")
            docs += f"# {cog_name} {helptxt}\n\n"
            cog_help = cog.help if cog.help else None
            if not embedding_style and cog_help:
                cog_help = cog_help.replace("\n", "<br/>")
            if cog_help:
                docs += f"{cog_help}\n\n"

        for cmd in cog.walk_app_commands():
            c = CustomCmdFmt(
                self.bot,
                cmd,
                prefix,
                replace_botname,
                extended_info,
                max_privilege_level,
                embedding_style,
                min_privilege_level,
            )
            doc = c.get_doc()
            if not doc:
                continue
            docs += doc

        ignored = []
        for cmd in cog.walk_commands():
            if cmd.hidden and not include_hidden:
                continue
            if cmd.requires_guild_owner and max_privilege_level not in ["guildowner", "botowner"]:
                continue
            c = CustomCmdFmt(
                self.bot,
                cmd,
                prefix,
                replace_botname,
                extended_info,
                max_privilege_level,
                embedding_style,
                min_privilege_level,
            )
            doc = c.get_doc()
            if doc is None:
                ignored.append(cmd.qualified_name)
            if not doc:
                continue
            skip = False
            for i in ignored:
                if i in cmd.qualified_name:
                    skip = True
            if skip:
                continue
            docs += doc
        return docs

    def categorize_cog(self, cog: commands.Cog) -> str:
        """Categorize the cog based on its commands."""
        fun_keywords = ["joke", "fun", "laugh", "meme"]
        mod_keywords = ["ban", "kick", "mute", "mod"]
        utilities_keywords = ["util", "tool", "info", "help"]
        automod_keywords = ["automod", "auto"]
        economy_keywords = ["econ", "money", "bank", "currency"]
        games_keywords = ["game", "play", "slots", "cah"]

        categories = {
            "Fun": fun_keywords,
            "Mod": mod_keywords,
            "Utilities": utilities_keywords,
            "Automod": automod_keywords,
            "Economy": economy_keywords,
            "Games": games_keywords,
        }

        command_names = [cmd.name.lower() for cmd in cog.walk_commands()]

        for category, keywords in categories.items():
            if any(keyword in cmd for cmd in command_names for keyword in keywords):
                return category

        return "Misc"

    @commands.command()
    @commands.is_owner()
    async def gendocs(
        self,
        ctx: commands.Context,
        repo_dir: str = "/root/PBCogs",
        custom_domain: str = "docs.prismbot.icu",
        site_name: str = "FuturoBot Documentation",
        site_url: str = None,
        theme_name: str = "material",
        use_directory_urls: bool = False,
        include_hidden: bool = False,
        include_help: bool = True,
        max_privilege_level: str = "guildowner",
        min_privilege_level: str = "user",
        replace_botname: bool = True,
        extended_info: bool = True,
        embedding_style: bool = False,
        invite_link: str = "https://discord.com/oauth2/authorize?client_id=1230169850446479370&scope=bot+applications.commands&permissions=8",
        support_server: str = "https://discord.gg/9f7WV6V8ud",
        max_cogs_per_category: int = 5  # New parameter to limit the number of cogs per category
    ):
        """
        Generate a documentation site for every cog in the bot.
        """
        await set_contextual_locales_from_guild(self.bot, ctx.guild)

        if site_url is None:
            site_url = f"https://{custom_domain}/"

        async with ctx.typing():
            docs_dir = os.path.join(repo_dir, "docs")
            mkdocs_config_path = os.path.join(repo_dir, "mkdocs.yml")

            if os.path.exists(docs_dir):
                shutil.rmtree(docs_dir)
            os.makedirs(docs_dir)

            # Create CNAME file for custom domain
            with open(os.path.join(docs_dir, "CNAME"), "w") as f:
                f.write(custom_domain)

            # Get the bot's name and prefix
            bot_name = self.bot.user.name
            prefix = (await self.bot.get_valid_prefixes(ctx.guild))[0].strip()

            # Create index.md file
            index_content = f"""
# Welcome to the Docs

Welcome to the official documentation site for **{site_name}**! This site provides comprehensive information on how to use and configure the various features and commands available in the bot.

## Introduction

**{site_name}** is a powerful and versatile bot designed to enhance your Discord server experience. With a wide range of features, including moderation tools, fun commands, and utility functions, **{bot_name}** is the perfect addition to any server.

## Getting Started

To get started with **{site_name}**, follow these simple steps:

1. **Invite the Bot**: Use the invite link to add the bot to your Discord server.
2. **Set Up Permissions**: Ensure the bot has the necessary permissions to function correctly.
3. **Configure the Bot**: Use the configuration commands to set up the bot according to your preferences.

## Commands

### General Commands

**{site_name}** offers a variety of general commands to enhance your server experience. These commands include:

- `{prefix}help`: Displays a list of available commands.
- `{prefix}info bot`: Provides information about the bot.
- `{prefix}ping`: Checks the bot's response time.

### Moderation Commands

Moderation commands help you manage your server effectively. These commands include:

- `{prefix}ban [user] [reason]`: Bans a user from the server.
- `{prefix}kick [user] [reason]`: Kicks a user from the server.
- `{prefix}mute [user] [duration]`: Mutes a user for a specified duration.
- There's a ton more, just take a look at the different features!

### Fun Commands

Add some fun to your server with these entertaining commands:

- `{prefix}joke`: Tells a random joke.
- `{prefix}slots`: Play some slots, using the bot's currency.
- `{prefix}cah`: Play a game of Cards Against Humanity.
- There's a ton more, just take a look at the different features!

## Configuration

To configure **{site_name}**, use the following commands:

- `{prefix}prefix [prefix]`: Changes the command prefix.

## FAQ

### How do I invite the bot to my server?

Use the invite link provided [here]({invite_link}) to add the bot to your server.

### How do I report a bug or request a feature?

To report a bug, please join the support server and create a ticket. To request a feature, use `{prefix}fr submit <feature>` where `<feature>` is the feature you desire.

## Support

If you need assistance or have any questions, please join our [Support Server]({support_server}).

Thank you for using **{site_name}**! We hope you enjoy all the features and functionality it has to offer.
            """
            with open(os.path.join(docs_dir, "index.md"), "w") as f:
                f.write(index_content)

            # Define categories
            categories = {
                "Fun": [],
                "Mod": [],
                "Utilities": [],
                "Automod": [],
                "Economy": [],
                "Games": [],
                "Misc": []
            }

            prefix = (await self.bot.get_valid_prefixes(ctx.guild))[0].strip()

            for cog_name, cog in self.bot.cogs.items():
                if cog_name in IGNORE:
                    continue
                category = self.categorize_cog(cog)
                docs = self.generate_readme(
                    cog,
                    prefix=prefix,
                    replace_botname=replace_botname,
                    extended_info=extended_info,
                    include_hidden=include_hidden,
                    include_help=include_help,
                    max_privilege_level=max_privilege_level,
                    min_privilege_level=min_privilege_level,
                    embedding_style=embedding_style,
                )
                filename = os.path.join(docs_dir, f"{cog_name}.md")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(docs)
                categories[category].append({cog_name: f"{cog_name}.md"})

            mkdocs_config = {
                "site_name": site_name,
                "site_url": site_url,  # Use your custom domain
                "theme": {
                    "name": theme_name
                },
                "use_directory_urls": use_directory_urls,
                "nav": [{"Home": "index.md"}]
            }

            # Add categorized cogs to the nav with a limit on the number of cogs displayed per category
            for category, cogs in categories.items():
                if cogs:
                    if len(cogs) > max_cogs_per_category:
                        # Create a separate page listing all cogs in the category
                        category_filename = os.path.join(docs_dir, f"{category.lower()}.md")
                        with open(category_filename, "w", encoding="utf-8") as f:
                            f.write(f"# {category} Cogs\n\n")
                            for cog in cogs:
                                for cog_name, cog_file in cog.items():
                                    f.write(f"- [{cog_name}]({cog_file})\n")
                        mkdocs_config["nav"].append({category: cogs[:max_cogs_per_category] + [{f"More {category} Cogs": f"{category.lower()}.md"}]})
                    else:
                        mkdocs_config["nav"].append({category: cogs})

            with open(mkdocs_config_path, "w", encoding="utf-8") as f:
                f.write(yaml.dump(mkdocs_config, default_flow_style=False))

            # Change to the repository directory
            os.chdir(repo_dir)

            mkdocs_path = "/root/fb/bin/mkdocs"  # Replace with the actual path to mkdocs if needed

            # Pull the latest changes before pushing
            os.system("git pull origin gh-pages")

            os.system(f"{mkdocs_path} build")
            os.system(f"{mkdocs_path} gh-deploy")

            await ctx.send(f"Documentation site has been generated and deployed to GitHub Pages.\nYou can view it here: {site_url}")
