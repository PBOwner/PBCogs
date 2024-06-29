import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from typing import List, Dict
import uuid
import asyncio

class FormManager(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        self.config.register_guild(forms={})
        self.config.register_member(responses={})

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def form(self, ctx):
        """Form management commands."""
        pass

    @form.command()
    async def create(self, ctx, form_name: str):
        """Create a new form with the given name."""
        forms = await self.config.guild(ctx.guild).forms()
        if form_name in forms:
            await ctx.send(f"Form '{form_name}' already exists.")
            return

        forms[form_name] = []
        await self.config.guild(ctx.guild).forms.set(forms)
        await ctx.send(f"Form '{form_name}' created. Use `[p]form addquestion {form_name} <question>` to add questions.")

    @form.command()
    async def addquestion(self, ctx, form_name: str, *, question: str):
        """Add a question to an existing form."""
        forms = await self.config.guild(ctx.guild).forms()
        if form_name not in forms:
            await ctx.send(f"No form found with the name '{form_name}'.")
            return

        question_id = str(uuid.uuid4())
        forms[form_name].append({"id": question_id, "question": question})
        await self.config.guild(ctx.guild).forms.set(forms)
        await ctx.send(f"Question added to form '{form_name}' with ID {question_id}.")

    @form.command()
    async def list(self, ctx):
        """List all available forms."""
        forms = await self.config.guild(ctx.guild).forms()
        if forms:
            embed = discord.Embed(title="Available Forms", color=discord.Color.blue())
            for form_name, questions in forms.items():
                embed.add_field(name=form_name, value=f"{len(questions)} questions", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No forms available.")

    @form.command()
    async def delete(self, ctx, form_name: str):
        """Delete a form by its name."""
        forms = await self.config.guild(ctx.guild).forms()
        if form_name in forms:
            del forms[form_name]
            await self.config.guild(ctx.guild).forms.set(forms)
            await ctx.send(f"Form '{form_name}' deleted.")
        else:
            await ctx.send(f"No form found with the name '{form_name}'.")

    @form.command()
    async def edit(self, ctx, form_name: str, question_id: str, *, new_question: str):
        """Edit a specific question in an existing form."""
        forms = await self.config.guild(ctx.guild).forms()
        if form_name not in forms:
            await ctx.send(f"No form found with the name '{form_name}'.")
            return

        for question in forms[form_name]:
            if question["id"] == question_id:
                question["question"] = new_question
                await self.config.guild(ctx.guild).forms.set(forms)
                await ctx.send(f"Question with ID {question_id} in form '{form_name}' has been updated.")
                return

        await ctx.send(f"No question found with ID {question_id} in form '{form_name}'.")

    @commands.command()
    async def sendform(self, ctx, user: discord.Member, form_name: str):
        """Send a form to a user via DM."""
        forms = await self.config.guild(ctx.guild).forms()
        if form_name not in forms:
            await ctx.send(f"No form found with the name '{form_name}'.")
            return

        questions = forms[form_name]
        await user.send(f"You have received a form: {form_name}")
        responses = []
        for question in questions:
            await user.send(f"Question ID: {question['id']}\n{question['question']}")
            def check(m):
                return m.author == user and m.channel == user.dm_channel

            try:
                response = await self.bot.wait_for('message', check=check, timeout=300)
                responses.append({"id": question["id"], "response": response.content})
            except asyncio.TimeoutError:
                await user.send("You took too long to respond. Please try again later.")
                return

        user_responses = await self.config.member(user).responses()
        if ctx.guild.id not in user_responses:
            user_responses[ctx.guild.id] = {}
        user_responses[ctx.guild.id][form_name] = responses
        await self.config.member(user).responses.set(user_responses)
        await user.send("Thank you for completing the form!")
        await ctx.send(f"Form '{form_name}' sent to {user.mention}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def viewresponses(self, ctx, user: discord.Member, form_name: str):
        """View a user's responses to a specific form."""
        responses = await self.config.member(user).responses()
        if ctx.guild.id in responses and form_name in responses[ctx.guild.id]:
            embed = discord.Embed(title=f"Responses for '{form_name}'", color=discord.Color.green())
            form_responses = responses[ctx.guild.id][form_name]
            forms = await self.config.guild(ctx.guild).forms()
            questions = {q["id"]: q["question"] for q in forms[form_name]}
            for response in form_responses:
                question_text = questions.get(response["id"], "Unknown Question")
                embed.add_field(name=question_text, value=response["response"], inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No responses found for form '{form_name}' from {user.mention}.")
