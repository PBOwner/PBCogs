import discord
from discord.ext import commands
import requests
import uuid
from redbot.core import Config, commands

class DynamicFormCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "api_key": None
        }
        default_guild = {
            "questions": {},
            "form_id": None
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

    @commands.group(name="formconfig")
    async def form_config(self, ctx):
        """Group of commands to configure the form settings."""
        pass

    @form_config.command(name="setapikey")
    async def set_api_key(self, ctx, api_key):
        """Set the Typeform API key globally."""
        await self.config.api_key.set(api_key)
        await ctx.send("API key has been set.")

    @commands.guild_only()
    @commands.command(name="addquestion")
    async def add_question(self, ctx, *, question_text):
        """Add a question to the form."""
        question_id = str(uuid.uuid4())
        async with self.config.guild(ctx.guild).questions() as questions:
            questions[question_id] = {
                "type": "short_text",
                "title": question_text
            }
        await ctx.send(f"Added question with ID: {question_id}")

    @commands.guild_only()
    @commands.command(name="editquestion")
    async def edit_question(self, ctx, question_id: str, *, new_question_text):
        """Edit a question in the form."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if question_id in questions:
                questions[question_id]["title"] = new_question_text
                await ctx.send(f"Edited question {question_id}: {new_question_text}")
            else:
                await ctx.send(f"Invalid question ID: {question_id}")

    @commands.guild_only()
    @commands.command(name="removequestion")
    async def remove_question(self, ctx, question_id: str):
        """Remove a question from the form."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if question_id in questions:
                removed_question = questions.pop(question_id)
                await ctx.send(f"Removed question {question_id}: {removed_question['title']}")
            else:
                await ctx.send(f"Invalid question ID: {question_id}")

    @commands.guild_only()
    @commands.command(name="createform")
    async def create_form(self, ctx, *, form_title):
        """Create the form with the added questions."""
        api_key = await self.config.api_key()
        if not api_key:
            await ctx.send("API key not set. Use `!formconfig setapikey <api_key>` to set it.")
            return

        questions = await self.config.guild(ctx.guild).questions()
        if not questions:
            await ctx.send("No questions added. Use `!addquestion` to add questions.")
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        form_data = {
            "title": form_title,
            "fields": list(questions.values())
        }

        response = requests.post("https://api.typeform.com/forms", headers=headers, json=form_data)
        if response.status_code == 201:
            form_id = response.json()["id"]
            await self.config.guild(ctx.guild).form_id.set(form_id)
            form_link = f"https://form.typeform.com/to/{form_id}"
            await ctx.send(f"Form created: {form_link}")
        else:
            await ctx.send(f"Failed to create form: {response.status_code} {response.text}")

        # Clear questions after form creation
        await self.config.guild(ctx.guild).questions.set({})

    @commands.guild_only()
    @commands.command(name="getresponses")
    async def get_responses(self, ctx):
        """Get responses for the created form."""
        api_key = await self.config.api_key()
        if not api_key:
            await ctx.send("API key not set. Use `!formconfig setapikey <api_key>` to set it.")
            return

        form_id = await self.config.guild(ctx.guild).form_id()
        if not form_id:
            await ctx.send("No form created. Use `!createform <title>` to create a form.")
            return

        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.get(f"https://api.typeform.com/forms/{form_id}/responses", headers=headers)
        if response.status_code == 200:
            data = response.json()
            response_message = "Form Responses:\n"
            for item in data['items']:
                answers = item['answers']
                for answer in answers:
                    response_message += f"{answer['field']['id']}: {answer.get('text', 'N/A')}\n"
            await ctx.send(response_message)
        else:
            await ctx.send(f"Failed to get responses: {response.status_code} {response.text}")

    @commands.guild_only()
    @commands.command(name="getformlink")
    async def get_form_link(self, ctx):
        """Get the link to the created form."""
        form_id = await self.config.guild(ctx.guild).form_id()
        if not form_id:
            await ctx.send("No form created. Use `!createform <title>` to create a form.")
            return

        form_link = f"https://form.typeform.com/to/{form_id}"
        await ctx.send(f"Form link: {form_link}")
