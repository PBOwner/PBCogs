    from redbot.core.bot import Red
    from .eventlogger import EventLogger
    from .dashboard_integration import DashboardIntegration

    async def setup(bot: Red):
        cog = EventLogger(bot)
        await bot.add_cog(cog)
        dashboard_integration = DashboardIntegration()
        await bot.add_cog(dashboard_integration)
