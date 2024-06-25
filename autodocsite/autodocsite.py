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

log = logging.getLogger("red.vrt.autodocs")
_ = Translator("AutoDocs", __file__)


# redgettext -D autodocs.py converters.py formatter.py
@cog_i18n(_)
class AutoDocSite(commands.Cog):
    """
    Automatically generate a documentation site for every cog in the bot.
    """

    __author__ = "[YourName](https://github.com/yourgithub)"
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

    def generate_readme(
        self,
        cog: commands.Cog,
        prefix: str,
        replace_botname: bool,
        extended_info: bool,
        include_hidden: bool,
        include_help: bool,
        max_privilege_level: str,
        min_privilage_level: str = "user",
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
                min_privilage_level,
            )
            doc = c.get_doc()
            if not doc:
                continue
            docs += doc

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
                min_privilage_level,
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

    @commands.command()
    @commands.is_owner()
    async def gendocs(self, ctx: commands.Context):
        """
        Generate a documentation site for every cog in the bot.
        """
        await set_contextual_locales_from_guild(self.bot, ctx.guild)
        async with ctx.typing():
            docs_dir = "docs"
            if os.path.exists(docs_dir):
                shutil.rmtree(docs_dir)
            os.makedirs(docs_dir)

            mkdocs_config = {
                "site_name": "Bot Documentation",
                "theme": {
                    "name": "material"
                },
                "nav": []
            }

            prefix = (await self.bot.get_valid_prefixes(ctx.guild))[0].strip()

            for cog_name, cog in self.bot.cogs.items():
                if cog_name in IGNORE:
                    continue
                docs = self.generate_readme(
                    cog,
                    prefix=prefix,
                    replace_botname=True,
                    extended_info=True,
                    include_hidden=False,
                    include_help=True,
                    max_privilege_level="botowner",
                )
                filename = f"{docs_dir}/{cog_name}.md"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(docs)
                mkdocs_config["nav"].append({cog_name: f"{cog_name}.md"})

            with open("mkdocs.yml", "w", encoding="utf-8") as f:
                f.write(yaml.dump(mkdocs_config, default_flow_style=False))

            os.system("mkdocs build")
            os.system("mkdocs gh-deploy")

            await ctx.send("Documentation site has been generated and deployed to GitHub Pages.")

def setup(bot: Red):
    bot.add_cog(AutoDocSite(bot))
