
import os
import shutil
import logging
from io import BytesIO
from typing import List, Literal, Optional, Tuple
from zipfile import ZIP_DEFLATED, ZipFile
import yaml
import random

import discord
import pandas as pd
from aiocache import cached
from discord import app_commands
from discord.ext.commands import Command, Cog, Group
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n, set_contextual_locales_from_guild
from redbot.core.utils.mod import is_admin_or_superior, is_mod_or_superior

from .formatter import IGNORE, CustomCmdFmt

log = logging.getLogger("red.vrt.autodocs")
_ = Translator("AutoDocs", __file__)

PRIVILEGE_LEVELS = ["user", "mod", "admin", "guildowner", "botowner"]

@cog_i18n(_)
class AutoDocs(commands.Cog):
    """
    Document your cogs with ease!

    Easily create documentation for any cog in Markdown format.

    Credits to Vrt and Vertyco for making this entire code possible.
    """
    __author__ = "[Rosie](https://github.com/PBOwner/PBCogs)"
    __version__ = "1.0.0"

    def format_help_for_context(self, ctx):
        helpcmd = super().format_help_for_context(ctx)
        txt = _("{}\nCog Version: {}\nAuthor: {}").format(helpcmd, self.__version__, self.__author__)
        return txt

    async def red_delete_data_for_user(self, *, requester, user_id: int):
        """No data to delete"""

    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = {
            "repo_dir": "/root/PBCogs",  # Add this line to ensure repo_dir is defined
            "custom_domain": "docs.prismbot.icu"  # Add default value or load from a config file
        }
        self.bot.add_listener(self.on_cog_load, "on_cog_load")
        self.bot.add_listener(self.on_cog_unload, "on_cog_unload")

    async def on_cog_load(self, cog: commands.Cog):
        await self.generate_docs_for_cog(cog)

    async def on_cog_unload(self, cog: commands.Cog):
        await self.generate_docs_for_cog(cog)

    async def generate_docs_for_cog(self, cog: commands.Cog):
        prefix = (await self.bot.get_valid_prefixes())[0].strip()
        docs, _ = self.generate_readme(
            cog,
            prefix,
            replace_botname=True,
            extended_info=True,
            include_hidden=False,
            include_help=True,
            max_privilege_level="botowner",
            min_privilege_level="user",
            embedding_style=False,
        )
        filename = f"{cog.qualified_name}.md"
        with open(os.path.join(self.config["repo_dir"], "docs", filename), "w", encoding="utf-8") as f:
            f.write(docs)

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
    ) -> Tuple[str, pd.DataFrame]:
        columns = [_("name"), _("text")]
        rows = []
        cog_name = cog.qualified_name
        if include_help:
            helptxt = _("Help")
            docs = f"# {cog_name} {helptxt}\n\n"
            cog_help = cog.help if cog.help else None
            if not embedding_style and cog_help:
                cog_help = cog_help.replace("\n", "<br/>")
            if cog_help:
                docs += f"{cog_help}\n\n"
                entry_name = _("{} cog description").format(cog_name)
                rows.append([entry_name, f"{entry_name}\n{cog_help}"])
        else:
            docs = ""

        max_level_index = PRIVILEGE_LEVELS.index(max_privilege_level)
        min_level_index = PRIVILEGE_LEVELS.index(min_privilege_level)

        for cmd in cog.walk_app_commands():
            if PRIVILEGE_LEVELS.index(cmd.extras.get("privilege_level", "user")) > max_level_index:
                continue
            if PRIVILEGE_LEVELS.index(cmd.extras.get("privilege_level", "user")) < min_level_index:
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
            if not doc:
                continue
            docs += doc
            csv_name = f"{cmd.name} command for {cog_name} cog"
            rows.append([csv_name, f"{csv_name}\n{doc}"])

        ignored = []
        for cmd in cog.walk_commands():
            if cmd.hidden and not include_hidden:
                continue
            if PRIVILEGE_LEVELS.index(cmd.extras.get("privilege_level", "user")) > max_level_index:
                continue
            if PRIVILEGE_LEVELS.index(cmd.extras.get("privilege_level", "user")) < min_level_index:
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
            csv_name = f"{cmd.name} command for {cog_name} cog"
            rows.append([csv_name, f"{csv_name}\n{doc}"])
        df = pd.DataFrame(rows, columns=columns)
        return docs, df

    @commands.hybrid_command(name="makedocs", description=_("Create docs for a cog"))
    @app_commands.describe(
        cog_name=_("The name of the cog you want to make docs for (Case Sensitive)"),
        replace_prefix=_("Replace all occurrences of [p] with the bots prefix"),
        replace_botname=_("Replace all occurrences of [botname] with the bots name"),
        extended_info=_("Include extra info like converters and their docstrings"),
        include_hidden=_("Include hidden commands"),
        max_privilege_level=_("Hide commands above specified privilege level (user, mod, admin, guildowner, botowner)"),
        min_privilege_level=_("Hide commands below specified privilege level (user, mod, admin, guildowner, botowner)"),
        csv_export=_("Include a csv with each command isolated per row"),
    )
    @commands.is_owner()
    @commands.bot_has_permissions(attach_files=True)
    async def makedocs(
        self,
        ctx: commands.Context,
        cog_name: str,
        replace_prefix: Optional[bool] = False,
        replace_botname: Optional[bool] = False,
        extended_info: Optional[bool] = False,
        include_hidden: Optional[bool] = False,
        include_help: Optional[bool] = True,
        max_privilege_level: Literal["user", "mod", "admin", "guildowner", "botowner"] = "botowner",
        min_privilege_level: Literal["user", "mod", "admin", "guildowner", "botowner"] = "user",
        csv_export: Optional[bool] = False,
    ):
        """
        Create a Markdown docs page for a cog and send to discord

        **Arguments**
        `cog_name:            `(str) The name of the cog you want to make docs for (Case Sensitive)
        `replace_prefix:      `(bool) If True, replaces the `prefix` placeholder with the bots prefix
        `replace_botname:     `(bool) If True, replaces the `botname` placeholder with the bots name
        `extended_info:       `(bool) If True, include extra info like converters and their docstrings
        `include_hidden:      `(bool) If True, includes hidden commands
        `include_help:        `(bool) If True, includes the cog help text at the top of the docs
        `max_privilege_level: `(str) Hide commands above specified privilege level
        `min_privilege_level: `(str) Hide commands below specified privilege level
        - (user, mod, admin, guildowner, botowner)
        `csv_export:          `(bool) Include a csv with each command isolated per row for use as embeddings

        **Note** If `all` is specified for cog_name, all currently loaded non-core cogs will have docs generated for
        them and sent in a zip file
        """
        await set_contextual_locales_from_guild(self.bot, ctx.guild)
        prefix = (await self.bot.get_valid_prefixes(ctx.guild))[0].strip() if replace_prefix else ""
        async with ctx.typing():
            if cog_name == "all":
                buffer = BytesIO()
                folder_name = _("AllCogDocs")
                with ZipFile(buffer, "w", compression=ZIP_DEFLATED, compresslevel=9) as arc:
                    try:
                        arc.mkdir(folder_name, mode=755)
                    except AttributeError:
                        arc.writestr(f"{folder_name}/", "")
                    for cog in self.bot.cogs:
                        cog = self.bot.get_cog(cog)
                        if cog.qualified_name in IGNORE:
                            continue
                        partial_func = functools.partial(
                            self.generate_readme,
                            cog,
                            prefix,
                            replace_botname,
                            extended_info,
                            include_hidden,
                            include_help,
                            max_privilege_level,
                            min_privilege_level,
                            csv_export,
                        )
                        docs, df = await self.bot.loop.run_in_executor(None, partial_func)
                        filename = f"{folder_name}/{cog.qualified_name}.md"

                        if csv_export:
                            tmp = BytesIO()
                            df.to_csv(tmp, index=False)
                            arc.writestr(
                                filename.replace(".md", ".csv"),
                                tmp.getvalue(),
                                compress_type=ZIP_DEFLATED,
                                compresslevel=9,
                            )
                        else:
                            arc.writestr(
                                filename,
                                docs,
                                compress_type=ZIP_DEFLATED,
                                compresslevel=9,
                            )

                buffer.name = f"{folder_name}.zip"
                buffer.seek(0)
                file = discord.File(buffer)
                txt = _("Here are the docs for all of your currently loaded cogs!")
            else:
                cog = self.bot.get_cog(cog_name)
                if not cog:
                    return await ctx.send(_("I could not find that cog, maybe it is not loaded?"))
                partial_func = functools.partial(
                    self.generate_readme,
                    cog,
                    prefix,
                    replace_botname,
                    extended_info,
                    include_hidden,
                    include_help,
                    max_privilege_level,
                    min_privilege_level,
                    csv_export,
                )
                docs, df = await self.bot.loop.run_in_executor(None, partial_func)
                if csv_export:
                    buffer = BytesIO()
                    df.to_csv(buffer, index=False)
                    buffer.name = f"{cog.qualified_name}.csv"
                    buffer.seek(0)
                else:
                    buffer = BytesIO(docs.encode())
                    buffer.name = f"{cog.qualified_name}.md"
                    buffer.seek(0)
                file = discord.File(buffer)
                txt = _("Here are your docs for {}!").format(cog.qualified_name)
            if ctx.guild and file.__sizeof__() > ctx.guild.filesize_limit:
                await ctx.send("File size too large!")
            else:
                await ctx.send(txt, file=file)

    @cached(ttl=8)
    async def get_coglist(self, string: str) -> List[app_commands.Choice]:
        cogs = set("all")
        for cmd in self.bot.walk_commands():
            cogs.add(str(cmd.cog_name).strip())
        return [app_commands.Choice(name=i, value=i) for i in cogs if string.lower() in i.lower()][:25]

    @makedocs.autocomplete("cog_name")
    async def get_cog_names(self, inter: discord.Interaction, current: str):
        return await self.get_coglist(current)

    # New command to search for a specific command
    @commands.command(name="searchcmd", description="Search for a specific command and get its documentation.")
    async def search_command(self, ctx: commands.Context, *, command_name: str):
        """
        Search for a specific command and get its documentation.

        **Arguments**
        `command_name: `(str) The name of the command you want to search for.
        """
        command = self.bot.get_command(command_name)
        if not command:
            return await ctx.send("Command not found. Please check the command name and try again.")

        prefixes = await self.bot.get_valid_prefixes(ctx.guild)
        prefix = prefixes[0].strip()

        c = CustomCmdFmt(self.bot, command, prefix, True, False, "botowner", True, "user")
        doc = c.get_doc()
        if not doc:
            return await ctx.send("No documentation found for this command.")

        # Create an embed with a randomized color
        embed = discord.Embed(
            title=f"Documentation for `{command_name}`",
            description=doc,
            color=random.randint(0, 0xFFFFFF)
        )

        # Add a link to the relative docs
        cog_name = command.cog.qualified_name
        site_url = self.config.get("site_url", f"https://{self.config['custom_domain']}")
        embed.add_field(name="More Info", value=f"[Documentation]({site_url}/{cog_name}.html#{command_name.replace(' ', '-')})")

        await ctx.send(embed=embed)

# Now, integrating the documentation generation into the AutoDocSite class

class AutoDocSite(commands.Cog):
    """
    Automatically generate a documentation site for every cog in the bot.
    """
    __version__ = "0.0.2"  # Define the version of the cog
    __author__ = "Rosie Val"  # Define the author of the cog

    def format_help_for_context(self, ctx):
        helpcmd = super().format_help_for_context(ctx)
        txt = _("{}\nCog Version: {}\nAuthor: {}").format(helpcmd, self.__version__, self.__author__)
        return txt

    async def red_delete_data_for_user(self, *, requester, user_id: int):
        """No data to delete"""

    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = {
            "repo_dir": "/root/PBCogs",
            "custom_domain": "docs.prismbot.icu",
            "site_name": "FuturoBot Documentation",
            "site_url": None,
            "theme_name": "dracula",
            "use_directory_urls": False,
            "include_hidden": False,
            "include_help": True,
            "max_privilege_level": "guildowner",
            "min_privilege_level": "user",
            "replace_botname": True,
            "extended_info": True,
            "embedding_style": False,
            "invite_link": "https://discord.com/oauth2/authorize?client_id=1230169850446479370&scope=bot+applications.commands&permissions=8",
            "support_server": "https://discord.gg/9f7WV6V8ud",
            "custom_footer": "Created by [Rosie](https://github.com/PBOwner) with <3"
        }

    @commands.group()
    @commands.is_owner()
    async def setsite(self, ctx: commands.Context):
        """Group command to set site configuration variables."""
        pass

    @setsite.command()
    async def repo_dir(self, ctx: commands.Context, *, value: str):
        """Set the repository directory."""
        self.config["repo_dir"] = value
        await ctx.send(f"Repository directory set to: {value}")

    @setsite.command()
    async def custom_domain(self, ctx: commands.Context, *, value: str):
        """Set the custom domain."""
        self.config["custom_domain"] = value
        await ctx.send(f"Custom domain set to: {value}")

    @setsite.command()
    async def site_name(self, ctx: commands.Context, *, value: str):
        """Set the site name."""
        self.config["site_name"] = value
        await ctx.send(f"Site name set to: {value}")

    @setsite.command()
    async def site_url(self, ctx: commands.Context, *, value: str = None):
        """Set the site URL."""
        self.config["site_url"] = value
        await ctx.send(f"Site URL set to: {value}")

    @setsite.command()
    async def theme_name(self, ctx: commands.Context, *, value: str):
        """Set the theme name."""
        self.config["theme_name"] = value
        await ctx.send(f"Theme name set to: {value}")

    @setsite.command()
    async def use_directory_urls(self, ctx: commands.Context, value: bool):
        """Set the use_directory_urls flag."""
        self.config["use_directory_urls"] = value
        await ctx.send(f"use_directory_urls set to: {value}")

    @setsite.command()
    async def include_hidden(self, ctx: commands.Context, value: bool):
        """Set the include_hidden flag."""
        self.config["include_hidden"] = value
        await ctx.send(f"include_hidden set to: {value}")

    @setsite.command()
    async def include_help(self, ctx: commands.Context, value: bool):
        """Set the include_help flag."""
        self.config["include_help"] = value
        await ctx.send(f"include_help set to: {value}")

    @setsite.command()
    async def max_privilege_level(self, ctx: commands.Context, *, value: str):
        """Set the max_privilege_level."""
        self.config["max_privilege_level"] = value
        await ctx.send(f"max_privilege_level set to: {value}")

    @setsite.command()
    async def min_privilege_level(self, ctx: commands.Context, *, value: str):
        """Set the min_privilege_level."""
        self.config["min_privilege_level"] = value
        await ctx.send(f"min_privilege_level set to: {value}")

    @setsite.command()
    async def replace_botname(self, ctx: commands.Context, value: bool):
        """Set the replace_botname flag."""
        self.config["replace_botname"] = value
        await ctx.send(f"replace_botname set to: {value}")

    @setsite.command()
    async def extended_info(self, ctx: commands.Context, value: bool):
        """Set the extended_info flag."""
        self.config["extended_info"] = value
        await ctx.send(f"extended_info set to: {value}")

    @setsite.command()
    async def embedding_style(self, ctx: commands.Context, value: bool):
        """Set the embedding_style flag."""
        self.config["embedding_style"] = value
        await ctx.send(f"embedding_style set to: {value}")

    @setsite.command()
    async def invite_link(self, ctx: commands.Context, *, value: str):
        """Set the invite link."""
        self.config["invite_link"] = value
        await ctx.send(f"Invite link set to: {value}")

    @setsite.command()
    async def support_server(self, ctx: commands.Context, *, value: str):
        """Set the support server link."""
        self.config["support_server"] = value
        await ctx.send(f"Support server link set to: {value}")

    @setsite.command()
    async def custom_footer(self, ctx: commands.Context, *, value: str):
        """Set the custom footer."""
        self.config["custom_footer"] = value
        await ctx.send(f"Custom footer set to: {value}")

    @commands.hybrid_command(name="gendocs", description=_("Generate documentation site for every cog"))
    @commands.is_owner()
    async def gendocs(self, ctx: commands.Context):
        """
        Generate a documentation site for every cog in the bot.
        """
        await set_contextual_locales_from_guild(self.bot, ctx.guild)

        site_url = self.config["site_url"]
        if site_url is None:
            site_url = f"https://{self.config['custom_domain']}/"

        async with ctx.typing():
            docs_dir = os.path.join(self.config["repo_dir"], "docs")
            mkdocs_config_path = os.path.join(self.config["repo_dir"], "mkdocs.yml")

            if os.path.exists(docs_dir):
                shutil.rmtree(docs_dir)
            os.makedirs(docs_dir)

            # Create CNAME file for custom domain
            with open(os.path.join(docs_dir, "CNAME"), "w") as f:
                f.write(self.config["custom_domain"])

            # Get the bot's name and prefix
            bot_name = self.bot.user.name
            prefix = (await self.bot.get_valid_prefixes(ctx.guild))[0].strip()

            # Create index.md file with static content
            index_content = f"""
# Welcome to the Docs

Welcome to the official documentation site for **{self.config['site_name']}**! This site provides comprehensive information on how to use and configure the various features and commands available in the bot.

## Introduction

**{self.config['site_name']}** is a powerful and versatile bot designed to enhance your Discord server experience. With a wide range of features, including moderation tools, fun commands, and utility functions, **{bot_name}** is the perfect addition to any server.

## Getting Started

To get started with **{self.config['site_name']}**, follow these simple steps:

1. **Invite the Bot**: Use the invite link to add the bot to your Discord server.
2. **Set Up Permissions**: Ensure the bot has the necessary permissions to function correctly.
3. **Configure the Bot**: Use the configuration commands to set up the bot according to your preferences.

## Commands

### General Commands

**{self.config['site_name']}** offers a variety of general commands to enhance your server experience. These commands include:

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

To configure **{self.config['site_name']}**, use the following commands:

- `{prefix}prefix [prefix]`: Changes the command prefix.

## FAQ

### How do I invite the bot to my server?

Use the invite link provided [here]({self.config['invite_link']}) to add the bot to your server.

### How do I report a bug or request a feature?

To report a bug, please join the support server and create a ticket. To request a feature, use `{prefix}fr submit <feature>` where `<feature>` is the feature you desire.

## Support

If you need assistance or have any questions, please join our [Support Server]({self.config['support_server']}).

Thank you for using **{self.config['site_name']}**! We hope you enjoy all the features and functionality it has to offer.
"""
            with open(os.path.join(docs_dir, "index.md"), "w") as f:
                f.write(index_content)

            # Generate Markdown files for all cogs
            for cog_name, cog in sorted(self.bot.cogs.items(), key=lambda item: item[0].lower()):
                if cog_name in IGNORE:
                    continue
                docs, _ = self.generate_readme(
                    cog,
                    prefix=prefix,
                    replace_botname=self.config["replace_botname"],
                    extended_info=self.config["extended_info"],
                    include_hidden=self.config["include_hidden"],
                    include_help=self.config["include_help"],
                    max_privilege_level=self.config["max_privilege_level"],
                    min_privilege_level=self.config["min_privilege_level"],
                    embedding_style=self.config["embedding_style"],
                )
                filename = os.path.join(docs_dir, f"{cog_name}.md")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(docs)

            # Create meta site data for each cog
            meta_config = {
                "site_name": f"{self.bot.user.name}'s Documentation",
                "site_url": site_url,
                "theme": {
                    "name": self.config["theme_name"]
                },
                "use_directory_urls": self.config["use_directory_urls"],
                "nav": [
                    {"Home": "index.md"},
                    {"Cogs": []}
                ],
                "extra": {
                    "footer": self.config["custom_footer"]
                }
            }

            # Add cogs to the Cogs category in the navigation
            for cog_name, cog in sorted(self.bot.cogs.items(), key=lambda item: item[0].lower()):
                if cog_name in IGNORE:
                    continue
                meta_config["nav"][1]["Cogs"].append({cog_name: f"{cog_name}.md"})

                # Create individual mkdocs.yml for each cog
                cog_config = {
                    "site_name": f"{cog_name}'s Documentation",
                    "site_url": f"{site_url}{cog_name}/",
                    "theme": {
                        "name": self.config["theme_name"]
                    },
                    "use_directory_urls": self.config["use_directory_urls"],
                    "nav": [
                        {"Home": "index.md"},
                        {cog_name: f"{cog_name}.md"}
                    ],
                    "extra": {
                        "footer": self.config["custom_footer"]}
                }

                cog_config_path = os.path.join(docs_dir, cog_name, "mkdocs.yml")
                os.makedirs(os.path.dirname(cog_config_path), exist_ok=True)
                with open(cog_config_path, "w", encoding="utf-8") as f:
                    f.write(yaml.dump(cog_config, default_flow_style=False))

            # Write main mkdocs.yml configuration
            with open(mkdocs_config_path, "w", encoding="utf-8") as f:
                f.write(yaml.dump(meta_config, default_flow_style=False))

            # Change to the repository directory
            os.chdir(self.config["repo_dir"])

            mkdocs_path = "/root/fb/bin/mkdocs"  # Replace with the actual path to mkdocs if needed

            # Pull the latest changes before pushing
            os.system("git pull origin gh-pages")

            # Build and deploy the documentation site
            os.system(f"{mkdocs_path} build")
            os.system(f"{mkdocs_path} gh-deploy")

            await ctx.send(f"Documentation site has been generated and deployed to GitHub Pages.\nYou can view it here: {site_url}")

    @commands.command()
    @commands.is_owner()
    async def docs(self, ctx: commands.Context):
        """
        Send the link to the documentation site.
        """
        site_url = self.config["site_url"]
        if site_url is None:
            site_url = f"https://{self.config['custom_domain']}/"
        await ctx.send(f"Here is the link to the documentation site: {site_url}")

    def generate_command_docs(self, cmd: commands.Command, prefix: str, extended_info: bool) -> str:
        """Generate detailed documentation for a command."""
        doc = f"### {prefix}{cmd.qualified_name}\n\n"
        if cmd.help:
            doc += f"**Description:** {cmd.help}\n\n"
        if cmd.aliases:
            doc += f"**Aliases:** {', '.join(cmd.aliases)}\n\n"
        if cmd.usage:
            doc += f"**Usage:** {prefix}{cmd.usage}\n\n"
        if cmd.brief:
            doc += f"**Brief:** {cmd.brief}\n\n"
        if cmd.extras:
            doc += f"**Extras:** {cmd.extras}\n\n"
        if extended_info and cmd.clean_params:
            doc += "**Parameters:**\n"
            for param, info in cmd.clean_params.items():
                doc += f"- **{param}**: {info}\n"
        if hasattr(cmd, 'examples') and cmd.examples:
            doc += "**Examples:**\n"
            for example in cmd.examples:
                doc += f"- `{prefix}{example}`\n"
        doc += f"**Permission Level:** {cmd.checks}\n\n"
        if isinstance(cmd, commands.Group):
            for subcmd in cmd.commands:
                doc += self.generate_command_docs(subcmd, prefix, extended_info)
        return doc

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
    ) -> Tuple[str, pd.DataFrame]:
        columns = [_("name"), _("text")]
        rows = []
        cog_name = cog.qualified_name
        if include_help:
            helptxt = _("Help")
            docs = f"# {cog_name} {helptxt}\n\n"
            cog_help = cog.help if cog.help else None
            if not embedding_style and cog_help:
                cog_help = cog_help.replace("\n", "<br/>")
            if cog_help:
                docs += f"{cog_help}\n\n"
                entry_name = _("{} cog description").format(cog_name)
                rows.append([entry_name, f"{entry_name}\n{cog_help}"])
        else:
            docs = ""

        max_level_index = PRIVILEGE_LEVELS.index(max_privilege_level)
        min_level_index = PRIVILEGE_LEVELS.index(min_privilege_level)

        for cmd in cog.walk_app_commands():
            if PRIVILEGE_LEVELS.index(cmd.extras.get("privilege_level", "user")) > max_level_index:
                continue
            if PRIVILEGE_LEVELS.index(cmd.extras.get("privilege_level", "user")) < min_level_index:
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
            if not doc:
                continue
            docs += doc
            csv_name = f"{cmd.name} command for {cog_name} cog"
            rows.append([csv_name, f"{csv_name}\n{doc}"])

        ignored = []
        for cmd in cog.walk_commands():
            if cmd.hidden and not include_hidden:
                continue
            if PRIVILEGE_LEVELS.index(cmd.extras.get("privilege_level", "user")) > max_level_index:
                continue
            if PRIVILEGE_LEVELS.index(cmd.extras.get("privilege_level", "user")) < min_level_index:
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
            csv_name = f"{cmd.name} command for {cog_name} cog"
            rows.append([csv_name, f"{csv_name}\n{doc}"])
        df = pd.DataFrame(rows, columns=columns)
        return docs, df
