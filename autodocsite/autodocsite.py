import os
import shutil
import logging
from io import BytesIO
from typing import List, Literal, Optional, Tuple
from zipfile import ZIP_DEFLATED, ZipFile
import yaml

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

# redgettext -D autodocs.py converters.py formatter.py
@cog_i18n(_)
class AutoDocs(commands.Cog):
    """
    Document your cogs with ease!

    Easily create documentation for any cog in Markdown format.
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
            csv_name = f"{cmd.name} command for {cog_name} cog"
            rows.append([csv_name, f"{csv_name}\n{doc}"])

        ignored = []
        for cmd in cog.walk_commands():
            if cmd.hidden and not include_hidden:
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

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------- ASSISTANT FUNCTION REGISTRATION --------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    async def get_command_info(
        self, guild: discord.Guild, user: discord.Member, command_name: str, *args, **kwargs
    ) -> str:
        command = self.bot.get_command(command_name)
        if not command:
            return "Command not found, check valid commands for this cog first"

        prefixes = await self.bot.get_valid_prefixes(guild)

        if user.id in self.bot.owner_ids:
            level = "botowner"
        elif user.id == guild.owner_id or user.guild_permissions.manage_guild:
            level = "guildowner"
        elif (await is_admin_or_superior(self.bot, user)) or user.guild_permissions.manage_roles:
            level = "admin"
        elif (await is_mod_or_superior(self.bot, user)) or user.guild_permissions.manage_messages:
            level = "mod"
        else:
            level = "user"

        c = CustomCmdFmt(self.bot, command, prefixes[0], True, False, level, True)
        doc = c.get_doc()
        if not doc:
            return "The user you are chatting with does not have the required permissions to use that command"

        return f"Cog name: {command.cog.qualified_name}\nCommand:\n{doc}"

    async def get_command_names(self, cog_name: str, *args, **kwargs):
        cog = self.bot.get_cog(cog_name)
        if not cog:
            return "Could not find that cog, check loaded cogs first"
        names = [i.qualified_name for i in cog.walk_app_commands()] + [i.qualified_name for i in cog.walk_commands()]
        joined = "\n".join(names)
        return f"Available commands for the {cog_name} cog:\n{joined}"

    async def get_cog_info(self, cog_name: str, *args, **kwargs):
        cog = self.bot.get_cog(cog_name)
        if not cog:
            return "Could not find that cog, check loaded cogs first"
        if desc := cog.help:
            return f"Description of the {cog_name} cog: {desc}"
        return "This cog has no description"

    async def get_cog_list(self, *args, **kwargs):
        joined = "\n".join([i for i in self.bot.cogs])
        return f"Currently loaded cogs:\n{joined}"

    @commands.Cog.listener()
    async def on_assistant_cog_add(self, cog: commands.Cog):
        """Registers a command with Assistant enabling it to access to command docs"""
        schemas = []

        schema = {
            "name": "get_command_info",
            "description": "Get info about a specific command",
            "parameters": {
                "type": "object",
                "properties": {
                    "command_name": {
                        "type": "string",
                        "description": "name of the command",
                    },
                },
                "required": ["command_name"],
            },
        }
        schemas.append(schema)

        schema = {
            "name": "get_command_names",
            "description": "Get a list of commands for a cog",
            "parameters": {
                "type": "object",
                "properties": {
                    "cog_name": {
                        "type": "string",
                        "description": "name of the cog, case sensitive",
                    }
                },
                "required": ["cog_name"],
            },
        }
        schemas.append(schema)

        schema = {
            "name": "get_cog_info",
            "description": "Get the description for a cog",
            "parameters": {
                "type": "object",
                "properties": {
                    "cog_name": {
                        "type": "string",
                        "description": "name of the cog, case sensitive",
                    }
                },
                "required": ["cog_name"],
            },
        }
        schemas.append(schema)

        schema = {
            "name": "get_cog_list",
            "description": "Get a list of currently loaded cogs by name",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
        schemas.append(schema)

        await cog.register_functions(self.qualified_name, schemas)


# Now, integrating the documentation generation into the AutoDocSite class

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
        custom_footer: str = "Generated by FuturoBot"
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

            # Create index.md file with static content
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

- `{prefix}ban [user] [reason]`: Bans a user from the server
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

            # Generate Markdown files for all cogs
            for cog_name, cog in sorted(self.bot.cogs.items(), key=lambda item: item[0].lower()):
                if cog_name in IGNORE:
                    continue
                docs, _ = self.generate_readme(
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

            # Create mkdocs.yml configuration
            mkdocs_config = {
                "site_name": site_name,
                "site_url": site_url,  # Use your custom domain
                "theme": {
                    "name": theme_name
                },
                "use_directory_urls": use_directory_urls,
                "nav": [
                    {"Home": "index.md"},
                    {"Cogs": []}
                ],
                "extra": {
                    "footer": custom_footer
                }
            }

            # Add cogs to the Cogs category in the navigation
            for cog_name, cog in sorted(self.bot.cogs.items(), key=lambda item: item[0].lower()):
                if cog_name in IGNORE:
                    continue
                mkdocs_config["nav"][1]["Cogs"].append({cog_name: f"{cog_name}.md"})

            # Write mkdocs.yml configuration
            with open(mkdocs_config_path, "w", encoding="utf-8") as f:
                f.write(yaml.dump(mkdocs_config, default_flow_style=False))

            # Change to the repository directory
            os.chdir(repo_dir)

            mkdocs_path = "/root/fb/bin/mkdocs"  # Replace with the actual path to mkdocs if needed

            # Pull the latest changes before pushing
            os.system("git pull origin gh-pages")

            # Build and deploy the documentation site
            os.system(f"{mkdocs_path} build")
            os.system(f"{mkdocs_path} gh-deploy")

            await ctx.send(f"Documentation site has been generated and deployed to GitHub Pages.\nYou can view it here: {site_url}")

    def generate_command_docs(self, cmd: Command, prefix: str, extended_info: bool) -> str:
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
            csv_name = f"{cmd.name} command for {cog_name} cog"
            rows.append([csv_name, f"{csv_name}\n{doc}"])

        ignored = []
        for cmd in cog.walk_commands():
            if cmd.hidden and not include_hidden:
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
